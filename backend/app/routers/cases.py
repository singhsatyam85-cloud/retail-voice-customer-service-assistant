"""HTTP routing for support-case creation.

Unlike call verification, the outcomes here are true request failures
(unknown call, unverified caller, order not owned by the caller), so they
are represented with real HTTP error status codes rather than 200 OK.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import CreateCaseRequest, SupportCaseOut
from backend.app.services.case_creation import (
    CallNotFoundError,
    CallNotVerifiedError,
    OrderNotAvailableError,
    create_support_case,
)

router = APIRouter(prefix="/api/v1/calls", tags=["cases"])


@router.post(
    "/{call_id}/cases",
    response_model=SupportCaseOut,
    status_code=status.HTTP_201_CREATED,
)
def create_case_endpoint(
    call_id: str,
    payload: CreateCaseRequest,
    db: Session = Depends(get_db),
) -> SupportCaseOut:
    try:
        support_case = create_support_case(db, call_id, payload)
    except CallNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Call not found.") from exc
    except CallNotVerifiedError as exc:
        raise HTTPException(
            status_code=409,
            detail="Support case cannot be created because the caller was not verified.",
        ) from exc
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
    )
