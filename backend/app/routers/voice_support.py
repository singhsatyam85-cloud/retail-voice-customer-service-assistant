"""HTTP routing for in-app voice-support sessions.

Every route here requires an authenticated customer (see
backend/app/services/demo_auth.py) -- there is no customer_id in any
request body.
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.database import get_db
from backend.app.models import Customer, Order
from backend.app.schemas import (
    CustomerOut,
    RecentOrderItemOut,
    RecentOrderOut,
    VoiceSessionAudioResponse,
    VoiceSessionStartResponse,
    CreateVoiceCaseRequest,
    SupportCaseOut,
    ConversationTurnOut,
)
from backend.app.services.demo_auth import get_authenticated_customer
from backend.app.services.classification import classify_transcript
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
from backend.app.services.case_creation import (
    create_voice_support_case,
    OrderNotAvailableError,
    VoiceSessionNotFoundError as CaseVoiceSessionNotFoundError,
)
from backend.app.services.ollama_service import (
    generate_ollama_response,
    generate_fallback_response,
    OllamaServiceError,
)
from backend.app.services.session_history import get_session_history, add_session_turn
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/api/v1/voice-support", tags=["voice-support"])
logger = logging.getLogger("voice_support")


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

    _t0_stt = time.perf_counter()
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
    stt_elapsed = time.perf_counter() - _t0_stt

    transcript_text = session.transcript or ""
    logger.info("STT transcript: %r (lang=%s)", transcript_text, session.detected_language)
    history = get_session_history(session.session_id)
    if transcript_text:
        add_session_turn(session.session_id, "user", transcript_text)

    recent_orders = list(
        db.scalars(
            select(Order)
            .where(Order.customer_id == customer.customer_id)
            .options(selectinload(Order.items))
            .order_by(Order.placed_at.desc())
            .limit(5)
        ).all()
    )

    settings = get_settings()
    ollama_source = "ollama"

    _t0_ollama = time.perf_counter()
    try:
        ollama_res = generate_ollama_response(
            customer=customer,
            recent_orders=recent_orders,
            user_transcript=transcript_text,
            conversation_history=history,
            settings=settings,
        )
    except OllamaServiceError as exc:
        logger.warning("Ollama failed (%s), using deterministic fallback.", exc)
        ollama_source = "fallback"
        ollama_res = generate_fallback_response(
            customer=customer,
            recent_orders=recent_orders,
            user_transcript=transcript_text,
            conversation_history=history,
        )
    ollama_elapsed = time.perf_counter() - _t0_ollama
    logger.info(
        "Classification [%s]: intent=%s, reply=%r (%.2fs)",
        ollama_source, ollama_res.intent, ollama_res.reply[:80], ollama_elapsed,
    )

    if ollama_res.reply:
        add_session_turn(session.session_id, "assistant", ollama_res.reply)

    history_out = [
        ConversationTurnOut(role=t["role"], content=t["content"])
        for t in get_session_history(session.session_id)
    ]

    suggested_order_id = recent_orders[0].order_id if len(recent_orders) == 1 else None

    total_elapsed = stt_elapsed + ollama_elapsed
    logger.info(
        "Request timing: stt=%.2fs, ollama=%.2fs, total=%.2fs",
        stt_elapsed, ollama_elapsed, total_elapsed,
    )

    return VoiceSessionAudioResponse(
        session_id=session.session_id,
        status=session.status,
        transcript=session.transcript,
        detected_language=session.detected_language,
        customer=CustomerOut(customer_id=customer.customer_id, full_name=customer.full_name),
        intent_category=ollama_res.intent,
        assistant_reply=ollama_res.reply,
        conversation_history=history_out,
        requires_order=ollama_res.requires_order,
        needs_clarification=ollama_res.needs_clarification,
        suggested_order_id=suggested_order_id,
    )


@router.post(
    "/sessions/{session_id}/cases",
    response_model=SupportCaseOut,
    status_code=status.HTTP_201_CREATED,
)
def create_voice_case_endpoint(
    session_id: str,
    payload: CreateVoiceCaseRequest,
    customer: Customer = Depends(get_authenticated_customer),
    db: Session = Depends(get_db),
) -> SupportCaseOut:
    try:
        support_case = create_voice_support_case(db, session_id, customer, payload)
    except CaseVoiceSessionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Voice support session not found.") from exc
    except OrderNotAvailableError as exc:
        raise HTTPException(
            status_code=404,
            detail="Order not found for this verified call.",
        ) from exc

    return SupportCaseOut(
        case_id=support_case.case_id,
        call_id=support_case.call_id,
        customer_id=support_case.customer_id,
        order_id=support_case.order_id,
        category=support_case.category,
        status=support_case.status,
        summary=support_case.summary,
        requires_human_review=support_case.requires_human_review,
        created_at=support_case.created_at,
        voice_session_id=support_case.voice_session_id,
    )
