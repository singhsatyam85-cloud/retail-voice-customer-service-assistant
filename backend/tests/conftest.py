"""Shared pytest fixtures.

Every test runs against an isolated, temporary SQLite database file so
tests never depend on (or modify) the developer's local
backend/retail_voice.db.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, enable_sqlite_foreign_keys, get_db
from backend.app.main import app
from backend.app.models import CallRecord, Customer, Order, OrderItem
from backend.app.services.speech_to_text.factory import get_speech_to_text_provider
from backend.app.services.speech_to_text.mock_provider import MockSpeechToTextProvider


@pytest.fixture()
def test_engine(tmp_path):
    db_path = tmp_path / "test_retail_voice.db"
    engine = create_engine(f"sqlite:///{db_path}")
    enable_sqlite_foreign_keys(engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def test_session_factory(test_engine):
    return sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def seeded_data(test_session_factory):
    current_time = datetime.now(timezone.utc)

    customers = [
        Customer(
            customer_id="CUST-101",
            full_name="Test Customer One",
            registered_phone="+447700900101",
            is_active=True,
        ),
        Customer(
            customer_id="CUST-102",
            full_name="Test Customer Two",
            registered_phone="+447700900102",
            is_active=True,
        ),
        Customer(
            customer_id="CUST-103",
            full_name="Test Customer Three",
            registered_phone="+447700900103",
            is_active=True,
        ),
    ]

    orders = [
        Order(
            order_id="ORD-5001",
            customer_id="CUST-101",
            status="delayed",
            total_amount=Decimal("24.99"),
            currency_code="GBP",
            placed_at=current_time - timedelta(days=7),
            expected_delivery_at=current_time - timedelta(days=1),
            delivered_at=None,
        ),
        Order(
            order_id="ORD-5002",
            customer_id="CUST-102",
            status="delivered",
            total_amount=Decimal("14.99"),
            currency_code="GBP",
            placed_at=current_time - timedelta(days=12),
            expected_delivery_at=current_time - timedelta(days=7),
            delivered_at=current_time - timedelta(days=7),
        ),
        Order(
            order_id="ORD-5003",
            customer_id="CUST-102",
            status="processing",
            total_amount=Decimal("7.99"),
            currency_code="GBP",
            placed_at=current_time - timedelta(days=1),
            expected_delivery_at=current_time + timedelta(days=4),
            delivered_at=None,
        ),
    ]

    order_items = [
        OrderItem(
            order_id="ORD-5001",
            product_name="Wireless Headphones",
            quantity=1,
            unit_price=Decimal("19.99"),
            item_status="ordered",
        ),
        OrderItem(
            order_id="ORD-5001",
            product_name="USB Charging Cable",
            quantity=1,
            unit_price=Decimal("5.00"),
            item_status="ordered",
        ),
        OrderItem(
            order_id="ORD-5002",
            product_name="Electric Kettle",
            quantity=1,
            unit_price=Decimal("14.99"),
            item_status="delivered",
        ),
        OrderItem(
            order_id="ORD-5003",
            product_name="Mobile Phone Case",
            quantity=1,
            unit_price=Decimal("7.99"),
            item_status="ordered",
        ),
    ]

    session = test_session_factory()
    try:
        session.add_all(customers)
        session.add_all(orders)
        session.add_all(order_items)
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def make_call_record(test_session_factory, seeded_data):
    """Insert a CallRecord directly with a chosen verification outcome.

    Lets support-case tests set up unmatched/unavailable/invalid calls
    deterministically without going through phone normalisation.
    """

    def _make(
        *,
        verification_status: str,
        customer_id: Optional[str],
        transfer_required: bool,
        incoming_phone: Optional[str] = "+447700900101",
    ) -> str:
        call_id = f"CALL-{uuid4()}"
        session = test_session_factory()
        try:
            session.add(
                CallRecord(
                    call_id=call_id,
                    customer_id=customer_id,
                    incoming_phone=incoming_phone,
                    verification_status=verification_status,
                    transfer_required=transfer_required,
                )
            )
            session.commit()
        finally:
            session.close()
        return call_id

    return _make


@pytest.fixture()
def client(test_session_factory, seeded_data):
    def _get_test_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    # Tests must never depend on a real speech model being installed.
    app.dependency_overrides[get_speech_to_text_provider] = lambda: MockSpeechToTextProvider()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
