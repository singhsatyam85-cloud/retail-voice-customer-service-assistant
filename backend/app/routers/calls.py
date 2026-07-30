"""HTTP routing for call-related endpoints.

Unmatched/unavailable/invalid verification are expected business
outcomes, not server errors, so this endpoint always returns 200 OK with
the outcome carried in the response body. This keeps the response shape
consistent for a future frontend regardless of verification result.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas import (
    CallStartRequest,
    CallStartResponse,
    CustomerOut,
    OrderItemOut,
    OrderOut,
)
from backend.app.services.caller_verification import start_call

router = APIRouter(prefix="/api/v1/calls", tags=["calls"])


@router.post("/start", response_model=CallStartResponse)
def start_call_endpoint(
    payload: CallStartRequest,
    db: Session = Depends(get_db),
) -> CallStartResponse:
    result = start_call(db, payload.incoming_phone)

    customer_out = None
    if result.customer is not None:
        customer_out = CustomerOut(
            customer_id=result.customer.customer_id,
            full_name=result.customer.full_name,
        )

    orders_out = [
        OrderOut(
            order_id=order.order_id,
            status=order.status,
            total_amount=f"{order.total_amount:.2f}",
            currency_code=order.currency_code,
            placed_at=order.placed_at,
            expected_delivery_at=order.expected_delivery_at,
            delivered_at=order.delivered_at,
            items=[
                OrderItemOut(
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=f"{item.unit_price:.2f}",
                    item_status=item.item_status,
                )
                for item in order.items
            ],
        )
        for order in result.orders
    ]

    return CallStartResponse(
        call_id=result.call_id,
        verification_status=result.verification_status,
        transfer_required=result.transfer_required,
        customer=customer_out,
        orders=orders_out,
    )
