from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class STTResult:
    text: str
    provider: str


class STTService:
    """Speech-to-text service with mock fallback for local development."""

    async def transcribe(self, audio_bytes: bytes | None, fallback_text: str | None = None) -> STTResult:
        if fallback_text and fallback_text.strip():
            return STTResult(text=fallback_text.strip(), provider="text-fallback")

        if not audio_bytes:
            return STTResult(text="", provider="mock-stt")

        # Placeholder transcription logic. Integrate DeepOcean SDK STT call here.
        # Example target behavior: call provider API with audio_bytes and return transcript.
        return STTResult(
            text="I want to build a voice assistant that helps me brainstorm startup ideas.",
            provider="mock-stt",
        )
