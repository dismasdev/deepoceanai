from __future__ import annotations

import asyncio
import wave
from dataclasses import dataclass
from pathlib import Path

from gtts import gTTS


@dataclass(slots=True)
class TTSResult:
    audio_url: str
    file_path: Path
    provider: str


class TTSService:
    """Text-to-speech service with gTTS and WAV fallback."""

    def __init__(self, output_dir: Path, public_prefix: str = "/static/audio") -> None:
        self.output_dir = output_dir
        self.public_prefix = public_prefix.rstrip("/")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def synthesize(self, text: str, trace_id: str) -> TTSResult:
        normalized_text = " ".join(text.strip().split())
        if not normalized_text:
            normalized_text = "Here is your brainstorm update."

        mp3_filename = f"{trace_id}.mp3"
        mp3_path = self.output_dir / mp3_filename

        try:
            await asyncio.to_thread(self._write_gtts_mp3, normalized_text, mp3_path)
            audio_url = f"{self.public_prefix}/{mp3_filename}"
            return TTSResult(audio_url=audio_url, file_path=mp3_path, provider="gtts")
        except Exception:
            wav_filename = f"{trace_id}.wav"
            wav_path = self.output_dir / wav_filename
            self._write_silent_wav(wav_path)
            audio_url = f"{self.public_prefix}/{wav_filename}"
            return TTSResult(audio_url=audio_url, file_path=wav_path, provider="mock-tts-fallback")

    def _write_gtts_mp3(self, text: str, file_path: Path) -> None:
        tts = gTTS(text=text, lang="en")
        tts.save(str(file_path))

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
