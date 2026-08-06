from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    registered_phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    orders: Mapped[list[Order]] = relationship(
        back_populates="customer",
    )

    calls: Mapped[list[CallRecord]] = relationship(
        back_populates="customer",
    )

    support_cases: Mapped[list[SupportCase]] = relationship(
        back_populates="customer",
    )

    voice_support_sessions: Mapped[list[VoiceSupportSession]] = relationship(
        back_populates="customer",
    )


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )

    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"),
        index=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
    )

    placed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    expected_delivery_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer: Mapped[Customer] = relationship(
        back_populates="orders",
    )

    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order",
    )

    support_cases: Mapped[list[SupportCase]] = relationship(
        back_populates="order",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    order_item_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    order_id: Mapped[str] = mapped_column(
        ForeignKey("orders.order_id"),
        index=True,
        nullable=False,
    )

    product_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    item_status: Mapped[str] = mapped_column(
        String(30),
        default="ordered",
        nullable=False,
    )

    order: Mapped[Order] = relationship(
        back_populates="items",
    )


class CallRecord(Base):
    __tablename__ = "call_records"

    call_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    customer_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("customers.customer_id"),
        index=True,
        nullable=True,
    )

    incoming_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    verification_status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    complaint_category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    transcript: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    transfer_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer: Mapped[Optional[Customer]] = relationship(
        back_populates="calls",
    )

    support_cases: Mapped[list[SupportCase]] = relationship(
        back_populates="call",
    )


class SupportCase(Base):
    __tablename__ = "support_cases"

    case_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"),
        index=True,
        nullable=False,
    )

    order_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("orders.order_id"),
        index=True,
        nullable=True,
    )

    call_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("call_records.call_id"),
        index=True,
        nullable=True,
    )

    voice_session_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("voice_support_sessions.session_id"),
        index=True,
        nullable=True,
    )

    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    requires_human_review: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    customer: Mapped[Customer] = relationship(
        back_populates="support_cases",
    )

    order: Mapped[Optional[Order]] = relationship(
        back_populates="support_cases",
    )

    call: Mapped[Optional[CallRecord]] = relationship(
        back_populates="support_cases",
    )

    voice_session: Mapped[Optional[VoiceSupportSession]] = relationship(
        back_populates="support_cases",
    )


class VoiceSupportSession(Base):
    """One in-app voice-support session for an authenticated customer.

    Deliberately separate from CallRecord: a CallRecord represents a
    telephone verification attempt (may have no customer at all), while a
    voice-support session only ever exists for an already-authenticated
    customer and never stores raw audio.
    """

    __tablename__ = "voice_support_sessions"

    session_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"),
        index=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="started",
        nullable=False,
    )

    transcript: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    detected_language: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )

    # Audit metadata only -- never used to build a filesystem path.
    original_filename: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    audio_content_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer: Mapped[Customer] = relationship(
        back_populates="voice_support_sessions",
    )

    support_cases: Mapped[list[SupportCase]] = relationship(
        back_populates="voice_session",
    )