"""Deterministic speech-to-text stand-in for tests and offline development.

Never inspects the uploaded audio bytes. Exists so the full
session -> upload -> transcript flow can be exercised end-to-end without
a real speech model installed.
"""

from __future__ import annotations

from backend.app.services.speech_to_text.base import SpeechToTextProvider, TranscriptionResult

_CANNED_TRANSCRIPT = "My wireless headphones have not arrived and the order shows delayed."


class MockSpeechToTextProvider(SpeechToTextProvider):
    def transcribe(self, audio_file_path: str) -> TranscriptionResult:
        return TranscriptionResult(transcript=_CANNED_TRANSCRIPT, detected_language="en")
