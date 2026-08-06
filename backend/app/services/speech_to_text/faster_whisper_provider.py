"""Local CPU speech-to-text using the faster-whisper package.

Not installed by default -- see docs/04-in-app-voice-support-foundation.md
for why, and for the exact steps to enable it. The faster-whisper package
and its model weights are only imported/downloaded the first time this
provider is actually instantiated, so selecting STT_PROVIDER=mock never
touches either.
"""

from __future__ import annotations

from backend.app.services.speech_to_text.base import (
    SpeechToTextProvider,
    SpeechToTextUnavailableError,
    TranscriptionResult,
)


class FasterWhisperProvider(SpeechToTextProvider):
    def __init__(self, model_size: str, device: str, compute_type: str) -> None:
        try:
            from faster_whisper import WhisperModel  # type: ignore[import-not-found]
        except ImportError as exc:
            raise SpeechToTextUnavailableError(
                "faster-whisper is not installed. Install it and its model "
                "before setting STT_PROVIDER=faster_whisper."
            ) from exc

        try:
            self._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as exc:
            # Broad on purpose: model download/load can fail in many ways
            # (missing model files, no network, unsupported device). Every
            # path becomes the same controlled, traceback-free error.
            raise SpeechToTextUnavailableError("faster-whisper model could not be loaded.") from exc

    def transcribe(self, audio_file_path: str) -> TranscriptionResult:
        try:
            segments, info = self._model.transcribe(audio_file_path)
            transcript = " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as exc:
            # Broad on purpose: decoding/inference failures must never
            # reach the client as a raw traceback.
            raise SpeechToTextUnavailableError("Speech-to-text processing failed.") from exc

        return TranscriptionResult(
            transcript=transcript,
            detected_language=getattr(info, "language", None) or "en",
        )
