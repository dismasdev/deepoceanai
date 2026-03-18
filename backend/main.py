from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Header,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.orchestrator import BrainstormOrchestrator
from backend.services.stt import STTService
from backend.services.tts import TTSService

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
AUDIO_DIR = STATIC_DIR / "audio"
MAX_AUDIO_BYTES = 8 * 1024 * 1024
ALLOWED_TYPES = {"audio/webm", "audio/wav", "audio/mpeg", "audio/mp4", "application/octet-stream"}

app = FastAPI(title="Brainstorm AI API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

orchestrator = BrainstormOrchestrator()
stt_service = STTService()
tts_service = TTSService(output_dir=AUDIO_DIR)


class ProcessAudioResponse(BaseModel):
    idea: str
    plan: str
    audio_url: str
    transcript: str
    trace_id: str
    latency_ms: int
    streaming_enabled: bool = Field(default=True)


def _entry(entry_type: str, value: Any) -> dict[str, Any]:
    return {"type": entry_type, "value": value}


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "streaming_enabled": True}


@app.get("/app-config")
async def app_config(x_sandbox_id: str | None = Header(default=None, alias="X-Sandbox-ID")) -> dict:
    """Return dynamic app configuration in the format expected by agent-starter-react."""
    sandbox_id = (x_sandbox_id or "local-dev").strip() or "local-dev"
    livekit_agent_name = (os.getenv("AGENT_NAME") or "").strip()

    return {
        "companyName": _entry("string", "Brainstorm AI"),
        "pageTitle": _entry("string", "Brainstorm AI Voice Agent"),
        "pageDescription": _entry("string", f"Voice-only AI brainstorming ({sandbox_id})"),
        "supportsChatInput": _entry("boolean", False),
        "supportsVideoInput": _entry("boolean", True),
        "supportsScreenShare": _entry("boolean", False),
        "isPreConnectBufferEnabled": _entry("boolean", True),
        "startButtonText": _entry("string", "Start Voice Session"),
        "audioVisualizerType": _entry("string", "radial"),
        "audioVisualizerRadialBarCount": _entry("number", 28),
        "audioVisualizerRadialRadius": _entry("number", 92),
        "agentName": _entry("string", livekit_agent_name) if livekit_agent_name else None,
        "sandboxId": _entry("string", sandbox_id),
    }


@app.post("/process-audio", response_model=ProcessAudioResponse)
async def process_audio(
    audio: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
) -> ProcessAudioResponse:
    started = time.perf_counter()
    trace_id = str(uuid.uuid4())

    audio_bytes: bytes | None = None
    if audio is not None:
        if audio.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported audio type: {audio.content_type}")
        audio_bytes = await audio.read()
        if len(audio_bytes) > MAX_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="Audio file too large")

    stt_result = await stt_service.transcribe(audio_bytes=audio_bytes, fallback_text=text)
    if not stt_result.text:
        raise HTTPException(status_code=400, detail="No transcript generated from input")

    orchestration = await orchestrator.run(stt_result.text)
    tts_result = await tts_service.synthesize(f"Idea: {orchestration.idea}\nPlan: {orchestration.plan}", trace_id)

    latency_ms = int((time.perf_counter() - started) * 1000)
    return ProcessAudioResponse(
        idea=orchestration.idea,
        plan=orchestration.plan,
        audio_url=tts_result.audio_url,
        transcript=stt_result.text,
        trace_id=trace_id,
        latency_ms=latency_ms,
        streaming_enabled=True,
    )


@app.websocket("/ws/stream")
async def stream_brainstorm(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            payload = json.loads(message)
            user_text = str(payload.get("text", "")).strip()
            if not user_text:
                await websocket.send_json({"event": "error", "error": "text is required", "done": True})
                continue

            trace_id = str(uuid.uuid4())
            await websocket.send_json({"event": "meta", "trace_id": trace_id, "streaming_enabled": True})

            final_idea = ""
            final_plan = ""
            async for event in orchestrator.stream(user_text):
                await websocket.send_json(event)
                if event.get("event") == "final":
                    final_idea = str(event.get("idea", ""))
                    final_plan = str(event.get("plan", ""))

            tts_result = await tts_service.synthesize(f"Idea: {final_idea}\nPlan: {final_plan}", trace_id)
            await websocket.send_json(
                {
                    "event": "audio_ready",
                    "audio_url": tts_result.audio_url,
                    "done": True,
                    "streaming_enabled": True,
                }
            )
    except WebSocketDisconnect:
        return


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
