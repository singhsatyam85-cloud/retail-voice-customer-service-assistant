"""Caller-verification business logic for the Phase 1 MVP.

Implements the agreed rule: exactly one active customer record may match
the normalised incoming phone number. A CallRecord is created for every
verification attempt, including failed ones, and orders are only ever
retrieved through the matched customer's own relationship — never by a
frontend-supplied customer_id or order_id.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.models import CallRecord, Customer, Order
from backend.app.services.phone_normalisation import normalise_uk_phone


@dataclass
class CallStartResult:
    call_id: str
    verification_status: str
    transfer_required: bool
    customer: Optional[Customer]
    orders: list[Order] = field(default_factory=list)


def start_call(db: Session, incoming_phone_raw: Optional[str]) -> CallStartResult:
    normalisation = normalise_uk_phone(incoming_phone_raw)

    customer: Optional[Customer] = None
    if normalisation.status == "valid":
        customer = db.scalar(
            select(Customer).where(
                Customer.registered_phone == normalisation.normalised_number,
                Customer.is_active.is_(True),
            )
        )

    if normalisation.status == "unavailable":
        verification_status = "unavailable"
    elif normalisation.status == "invalid":
        verification_status = "invalid"
    elif customer is not None:
        verification_status = "verified"
    else:
        verification_status = "unmatched"

    transfer_required = verification_status != "verified"

    call_record = CallRecord(
        call_id=f"CALL-{uuid4()}",
        customer_id=customer.customer_id if customer is not None else None,
        incoming_phone=incoming_phone_raw,
        verification_status=verification_status,
        transfer_required=transfer_required,
    )
    db.add(call_record)
    db.commit()

    orders: list[Order] = []
    if customer is not None:
        orders = list(
            db.scalars(
                select(Order)
                .where(Order.customer_id == customer.customer_id)
                .options(selectinload(Order.items))
                .order_by(Order.placed_at)
            ).all()
        )

    return CallStartResult(
        call_id=call_record.call_id,
        verification_status=verification_status,
        transfer_required=transfer_required,
        customer=customer,
        orders=orders,
    )
