"""Pydantic request/response schemas for the public API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

VerificationStatus = Literal["verified", "unmatched", "unavailable", "invalid"]


class CallStartRequest(BaseModel):
    incoming_phone: Optional[str] = None


class CustomerOut(BaseModel):
    customer_id: str
    full_name: str


class OrderItemOut(BaseModel):
    product_name: str
    quantity: int
    unit_price: str
    item_status: str


class OrderOut(BaseModel):
    order_id: str
    status: str
    total_amount: str
    currency_code: str
    placed_at: datetime
    expected_delivery_at: Optional[datetime]
    delivered_at: Optional[datetime]
    items: list[OrderItemOut]


class CallStartResponse(BaseModel):
    call_id: str
    verification_status: VerificationStatus
    transfer_required: bool
    customer: Optional[CustomerOut]
    orders: list[OrderOut]


class CaseCategory(str, Enum):
    ORDER_STATUS = "order_status"
    DELAYED_DELIVERY = "delayed_delivery"
    MISSING_DELIVERY = "missing_delivery"
    DAMAGED_PRODUCT = "damaged_product"
    RETURN_REQUEST = "return_request"
    CANCELLATION_REQUEST = "cancellation_request"
    WRONG_ITEM = "wrong_item"
    HUMAN_AGENT_REQUEST = "human_agent_request"


# Categories that describe a specific order and therefore cannot be
# recorded without one. human_agent_request is the only category that
# may stand alone (it may still carry an order_id when relevant).
ORDER_REQUIRED_CATEGORIES = frozenset(
    category for category in CaseCategory if category is not CaseCategory.HUMAN_AGENT_REQUEST
)


class CreateCaseRequest(BaseModel):
    # extra="forbid" is the control that stops a caller from smuggling
    # authority fields (status, requires_human_review, customer_id, ...)
    # into the request instead of silently ignoring them.
    model_config = ConfigDict(extra="forbid")

    category: CaseCategory
    order_id: Optional[str] = None
    summary: str

    @field_validator("summary")
    @classmethod
    def _validate_summary(cls, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 10:
            raise ValueError("summary must contain at least 10 meaningful characters")
        if len(trimmed) > 1000:
            raise ValueError("summary must not exceed 1000 characters")
        return trimmed

    @model_validator(mode="after")
    def _validate_order_requirement(self) -> "CreateCaseRequest":
        if self.category in ORDER_REQUIRED_CATEGORIES and not self.order_id:
            raise ValueError(f"order_id is required for category '{self.category.value}'")
        return self


class SupportCaseOut(BaseModel):
    case_id: str
    call_id: Optional[str] = None
    customer_id: str
    order_id: Optional[str]
    category: CaseCategory
    status: str
    summary: str
    requires_human_review: bool
    created_at: datetime
    voice_session_id: Optional[str] = None


class RecentOrderItemOut(BaseModel):
    product_name: str
    quantity: int


class RecentOrderOut(BaseModel):
    order_id: str
    status: str
    total_amount: str
    currency_code: str
    items: list[RecentOrderItemOut]


class VoiceSessionStartResponse(BaseModel):
    session_id: str
    status: str
    customer: CustomerOut
    recent_orders: list[RecentOrderOut]
    created_at: datetime


class VoiceSessionAudioResponse(BaseModel):
    session_id: str
    status: str
    transcript: Optional[str]
    detected_language: Optional[str]
    customer: CustomerOut
    intent_category: Optional[str] = None


class CreateVoiceCaseRequest(CreateCaseRequest):
    idempotency_key: str
