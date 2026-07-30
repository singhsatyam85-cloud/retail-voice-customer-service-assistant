"""Support-case creation business logic for the Phase 1 MVP.

A SupportCase records what a verified caller is asking for. It never
carries an approval, refund, or cancellation decision — Phase 1 may only
capture the request for human review (see docs/03-support-case-api.md).
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import CallRecord, Order, SupportCase
from backend.app.schemas import CreateCaseRequest


class CallNotFoundError(Exception):
    """Raised when the call_id in the URL does not match any CallRecord."""


class CallNotVerifiedError(Exception):
    """Raised when the call exists but was not a successful verification."""


class OrderNotAvailableError(Exception):
    """Raised when order_id does not belong to the verified call's customer."""


def create_support_case(db: Session, call_id: str, payload: CreateCaseRequest) -> SupportCase:
    call_record = db.get(CallRecord, call_id)
    if call_record is None:
        raise CallNotFoundError()

    # Trust only the persisted verification outcome, never the request body.
    if (
        call_record.verification_status != "verified"
        or call_record.customer_id is None
        or call_record.transfer_required
    ):
        raise CallNotVerifiedError()

    order: Order | None = None
    if payload.order_id is not None:
        # Ownership must be checked in the same query — an order_id match
        # alone is not proof the order belongs to this caller.
        order = db.scalar(
            select(Order).where(
                Order.order_id == payload.order_id,
                Order.customer_id == call_record.customer_id,
            )
        )
        if order is None:
            raise OrderNotAvailableError()

    support_case = SupportCase(
        case_id=f"CASE-{uuid4()}",
        customer_id=call_record.customer_id,
        order_id=order.order_id if order is not None else None,
        call_id=call_record.call_id,
        category=payload.category.value,
        status="pending",
        summary=payload.summary,
        requires_human_review=True,
    )
    db.add(support_case)
    db.commit()
    db.refresh(support_case)
    return support_case
