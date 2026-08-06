"""Speech-to-text provider interface.

Any provider (mock, faster-whisper, or a future one) implements this so
the voice-support service never depends on a specific speech engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class TranscriptionResult:
    transcript: str
    detected_language: str


class SpeechToTextProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_file_path: str) -> TranscriptionResult:
        """Transcribe the audio file at audio_file_path.

        Raises SpeechToTextUnavailableError on any failure -- callers
        must never see a raw provider exception or traceback.
        """


class SpeechToTextUnavailableError(Exception):
    """Raised when the configured speech-to-text provider cannot process audio."""
