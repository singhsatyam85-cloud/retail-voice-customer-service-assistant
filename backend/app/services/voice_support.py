"""In-app voice-support session business logic.

Covers only the foundation: starting a session, validating an uploaded
recording, writing it to a self-cleaning temporary file, and handing it
to a SpeechToTextProvider. No intent classification, complaint capture,
or SupportCase creation happens here -- see
docs/04-in-app-voice-support-foundation.md for what is deliberately out
of scope.
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models import Customer, Order, VoiceSupportSession
from backend.app.services.speech_to_text.base import SpeechToTextProvider, SpeechToTextUnavailableError

RECENT_ORDERS_LIMIT = 5
MAX_AUDIO_BYTES = 10 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024

# Only what the browser MediaRecorder / common audio containers actually
# send. Content-type is client-supplied, so this is a filter, not proof
# the bytes are valid audio.
ALLOWED_AUDIO_CONTENT_TYPES = {
    "audio/webm": ".webm",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp4": ".mp4",
    "audio/ogg": ".ogg",
}


class VoiceSessionNotFoundError(Exception):
    """Session does not exist, or does not belong to the caller."""


class EmptyAudioError(Exception):
    pass


class AudioTooLargeError(Exception):
    pass


class UnsupportedAudioTypeError(Exception):
    pass


def start_voice_session(db: Session, customer: Customer) -> tuple[VoiceSupportSession, list[Order]]:
    session = VoiceSupportSession(
        session_id=f"VOICE-{uuid4()}",
        customer_id=customer.customer_id,
        status="started",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    recent_orders = list(
        db.scalars(
            select(Order)
            .where(Order.customer_id == customer.customer_id)
            .options(selectinload(Order.items))
            .order_by(Order.placed_at.desc())
            .limit(RECENT_ORDERS_LIMIT)
        ).all()
    )

    return session, recent_orders


def get_owned_session(db: Session, session_id: str, customer: Customer) -> VoiceSupportSession:
    session = db.get(VoiceSupportSession, session_id)
    if session is None or session.customer_id != customer.customer_id:
        # Identical error either way -- never reveal that a session
        # exists for a different customer.
        raise VoiceSessionNotFoundError()
    return session


def _safe_delete(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


async def _write_temp_audio_file(upload: UploadFile, suffix: str) -> tuple[str, int]:
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="voice-support-")
    total_bytes = 0
    try:
        with os.fdopen(fd, "wb") as temp_file:
            while True:
                chunk = await upload.read(UPLOAD_CHUNK_BYTES)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_AUDIO_BYTES:
                    raise AudioTooLargeError()
                temp_file.write(chunk)
    except Exception:
        _safe_delete(path)
        raise
    return path, total_bytes


async def transcribe_uploaded_audio(
    db: Session,
    session: VoiceSupportSession,
    upload: UploadFile,
    provider: SpeechToTextProvider,
) -> VoiceSupportSession:
    content_type = (upload.content_type or "").lower()
    suffix = ALLOWED_AUDIO_CONTENT_TYPES.get(content_type)
    if suffix is None:
        raise UnsupportedAudioTypeError()

    temp_path, total_bytes = await _write_temp_audio_file(upload, suffix)
    try:
        if total_bytes == 0:
            raise EmptyAudioError()

        session.status = "processing"
        # Metadata only, never used as a filesystem path.
        session.original_filename = upload.filename
        session.audio_content_type = content_type
        db.commit()

        try:
            result = provider.transcribe(temp_path)
        except SpeechToTextUnavailableError:
            session.status = "failed"
            session.completed_at = datetime.now(timezone.utc)
            db.commit()
            raise

        session.status = "transcribed"
        session.transcript = result.transcript
        session.detected_language = result.detected_language
        session.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(session)
        return session
    finally:
        _safe_delete(temp_path)
