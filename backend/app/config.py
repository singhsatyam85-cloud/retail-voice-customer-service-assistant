"""Application configuration, sourced from environment variables.

Keeps speech-provider and CORS choices out of route/service logic so they
can be changed per environment without editing code.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False)

    # "mock" (default, used by automated tests) or "faster_whisper"
    # (local CPU transcription -- see docs/04-in-app-voice-support-foundation.md).
    stt_provider: str = "mock"
    stt_model_size: str = "tiny.en"
    stt_device: str = "cpu"
    stt_compute_type: str = "int8"

    # Comma-separated list of origins allowed to call the API with
    # credentials. Must be explicit origins, never "*", because the
    # voice-support endpoints read an Authorization header.
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
