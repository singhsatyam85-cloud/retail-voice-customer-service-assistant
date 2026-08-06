"""Selects a speech-to-text provider based on Settings.stt_provider.

Used as a FastAPI dependency (Depends(get_speech_to_text_provider)) so
tests can override it the same way get_db is overridden, without needing
to change environment variables.
"""

from __future__ import annotations

from backend.app.config import get_settings
from backend.app.services.speech_to_text.base import SpeechToTextProvider
from backend.app.services.speech_to_text.mock_provider import MockSpeechToTextProvider


def get_speech_to_text_provider() -> SpeechToTextProvider:
    settings = get_settings()

    if settings.stt_provider == "mock":
        return MockSpeechToTextProvider()

    if settings.stt_provider == "faster_whisper":
        # Imported lazily so a mock-only environment never needs the
        # faster-whisper package installed.
        from backend.app.services.speech_to_text.faster_whisper_provider import (
            FasterWhisperProvider,
        )

        return FasterWhisperProvider(
            model_size=settings.stt_model_size,
            device=settings.stt_device,
            compute_type=settings.stt_compute_type,
        )

    raise ValueError(f"Unsupported STT_PROVIDER: {settings.stt_provider!r}")
