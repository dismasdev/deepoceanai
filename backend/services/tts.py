from __future__ import annotations

import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TTSResult:
    audio_url: str
    file_path: Path
    provider: str


class TTSService:
    """Text-to-speech service with a lightweight WAV placeholder output."""

    def __init__(self, output_dir: Path, public_prefix: str = "/static/audio") -> None:
        self.output_dir = output_dir
        self.public_prefix = public_prefix.rstrip("/")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize(self, text: str, trace_id: str) -> TTSResult:
        filename = f"{trace_id}.wav"
        file_path = self.output_dir / filename

        # Placeholder TTS: generate 1 second of silence for local playback contract.
        # Integrate DeepOcean SDK TTS here and write returned audio bytes to file_path.
        self._write_silent_wav(file_path)

        audio_url = f"{self.public_prefix}/{filename}"
        return TTSResult(audio_url=audio_url, file_path=file_path, provider="mock-tts")

    def _write_silent_wav(self, file_path: Path) -> None:
        sample_rate = 16000
        duration_seconds = 1
        n_frames = sample_rate * duration_seconds
        silence_frame = (0).to_bytes(2, byteorder="little", signed=True)

        with wave.open(str(file_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(silence_frame * n_frames)
