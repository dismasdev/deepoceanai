# Brainstorm AI (MVP)

Real-time voice-based AI brainstorming assistant built with FastAPI + browser frontend.

Pipeline:
Audio -> STT -> Idea Agent -> Planner Agent -> TTS -> Audio response

This repository is configured for a uv-only workflow and includes a full ADK entrypoint.

## Features

- POST /process-audio endpoint for audio upload and structured response.
- WebSocket real-time endpoint for streaming idea/plan chunks.
- Multi-agent orchestration:
	- Idea Agent: expands concept.
	- Planner Agent: creates step-by-step plan.
- Mock STT/TTS with clear integration points for DeepOcean/Gradient SDK.
- ADK entrypoint for gradient agent run/deploy flows.

## Project Structure

```text
brainstorm-ai/
├── backend/
│   ├── main.py
│   ├── adk_entrypoint.py
│   ├── orchestrator.py
│   ├── agents/
│   │   ├── idea_agent.py
│   │   └── planner_agent.py
│   ├── services/
│   │   ├── stt.py
│   │   └── tts.py
│   └── static/audio/
├── frontend/
│   ├── index.html
│   └── app.js
├── main.py
└── pyproject.toml
```

## Prerequisites

- Python 3.12+
- uv installed

Install uv (if needed):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup (uv)

```bash
uv sync
```

## Run Backend

```bash
uv run python main.py
```

Backend will run on http://localhost:8000

## Run Frontend

Open frontend/index.html in your browser.

For local CORS-safe serving, use a static server:

```bash
uv run python -m http.server 5500
```

Then open http://localhost:5500/frontend/

## API Endpoints

### Health

```bash
curl http://localhost:8000/health
```

### Process Audio

```bash
curl -X POST http://localhost:8000/process-audio \
	-F "audio=@sample.wav"
```

Or text fallback:

```bash
curl -X POST http://localhost:8000/process-audio \
	-F "text=I want an app that helps students brainstorm science fair ideas"
```

Response format:

```json
{
	"idea": "...",
	"plan": "...",
	"audio_url": "/static/audio/<trace_id>.wav",
	"transcript": "...",
	"trace_id": "...",
	"latency_ms": 123,
	"streaming_enabled": true
}
```

### Real-time Streaming (WebSocket)

WebSocket URL:

```text
ws://localhost:8000/ws/stream
```

Send:

```json
{"text":"Build a voice-first startup brainstorming app","stream":true}
```

Stream events include:

- meta
- status
- idea_chunk
- plan_chunk
- final
- audio_ready

Streaming is enabled by default (true).

## ADK Setup

The project includes backend/adk_entrypoint.py with @entrypoint.

1. Verify CLI install:

```bash
uv run gradient --version
```

2. Initialize/configure agent workspace (choose names when prompted):

```bash
uv run gradient agent configure
```

If you prefer a brand-new ADK scaffold elsewhere:

```bash
uv run gradient agent init
```

3. Run locally:

```bash
uv run gradient agent run --verbose
```

4. Deploy:

```bash
export DIGITALOCEAN_API_TOKEN="<your-token>"
uv run gradient agent deploy
```

## Environment Variables

Optional variables for real model calls:

- ENABLE_GRADIENT_AGENT=true
- GRADIENT_MODEL_ACCESS_KEY=<key>
- GRADIENT_MODEL_ID=openai-gpt-oss-120b
- GRADIENT_INFERENCE_ENDPOINT=https://inference.do-ai.run

Without these values, the app runs with low-latency mock STT/TTS and deterministic agents.

## LiveKit Notes

Frontend includes placeholders for LiveKit room/token integration in frontend/app.js.

Recommended next step:

- add backend /livekit-token endpoint
- connect livekit-client in frontend
- publish mic and subscribe to AI voice track

## Production Readiness Notes

- CORS is currently open for MVP convenience.
- Replace mock STT/TTS with provider SDKs.
- Add auth + rate limits before internet exposure.
- Add persistent object storage for generated audio.

## Deployment

DigitalOcean + Gradient deployment artifacts are included in:

- `deploy/DEPLOYMENT.md`
- `deploy/do-backend-app.yaml`
- `deploy/do-frontend-app.yaml`

