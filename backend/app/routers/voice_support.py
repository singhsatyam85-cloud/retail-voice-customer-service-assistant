"""HTTP routing for in-app voice-support sessions.

Every route here requires an authenticated customer (see
backend/app/services/demo_auth.py) -- there is no customer_id in any
request body.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Customer
from backend.app.schemas import (
    CustomerOut,
    RecentOrderItemOut,
    RecentOrderOut,
    VoiceSessionAudioResponse,
    VoiceSessionStartResponse,
)
from backend.app.services.demo_auth import get_authenticated_customer
from backend.app.services.speech_to_text.base import SpeechToTextProvider, SpeechToTextUnavailableError
from backend.app.services.speech_to_text.factory import get_speech_to_text_provider
from backend.app.services.voice_support import (
    AudioTooLargeError,
    EmptyAudioError,
    UnsupportedAudioTypeError,
    VoiceSessionNotFoundError,
    get_owned_session,
    start_voice_session,
    transcribe_uploaded_audio,
)

router = APIRouter(prefix="/api/v1/voice-support", tags=["voice-support"])


@router.post(
    "/sessions",
    response_model=VoiceSessionStartResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_session_endpoint(
    customer: Customer = Depends(get_authenticated_customer),
    db: Session = Depends(get_db),
) -> VoiceSessionStartResponse:
    session, recent_orders = start_voice_session(db, customer)

    return VoiceSessionStartResponse(
        session_id=session.session_id,
        status=session.status,
        customer=CustomerOut(customer_id=customer.customer_id, full_name=customer.full_name),
        recent_orders=[
            RecentOrderOut(
                order_id=order.order_id,
                status=order.status,
                total_amount=f"{order.total_amount:.2f}",
                currency_code=order.currency_code,
                items=[
                    RecentOrderItemOut(product_name=item.product_name, quantity=item.quantity)
                    for item in order.items
                ],
            )
            for order in recent_orders
        ],
        created_at=session.created_at,
    )


@router.post(
    "/sessions/{session_id}/audio",
    response_model=VoiceSessionAudioResponse,
)
async def upload_audio_endpoint(
    session_id: str,
    audio: UploadFile = File(...),
    customer: Customer = Depends(get_authenticated_customer),
    db: Session = Depends(get_db),
    provider: SpeechToTextProvider = Depends(get_speech_to_text_provider),
) -> VoiceSessionAudioResponse:
    try:
        session = get_owned_session(db, session_id, customer)
    except VoiceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Voice support session not found.") from exc

    try:
        session = await transcribe_uploaded_audio(db, session, audio, provider)
    except EmptyAudioError as exc:
        raise HTTPException(status_code=400, detail="Uploaded audio is empty.") from exc
    except UnsupportedAudioTypeError as exc:
        raise HTTPException(status_code=415, detail="Unsupported audio type.") from exc
    except AudioTooLargeError as exc:
        raise HTTPException(status_code=413, detail="Audio exceeds the 10 MB limit.") from exc
    except SpeechToTextUnavailableError as exc:
        raise HTTPException(status_code=503, detail="Speech-to-text service is unavailable.") from exc

    return VoiceSessionAudioResponse(
        session_id=session.session_id,
        status=session.status,
        transcript=session.transcript,
        detected_language=session.detected_language,
        customer=CustomerOut(customer_id=customer.customer_id, full_name=customer.full_name),
    )
