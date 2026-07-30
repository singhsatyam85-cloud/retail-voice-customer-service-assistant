from sqlalchemy import func, select

from backend.app.models import Order, SupportCase

VALID_SUMMARY = "My order was due yesterday and has not arrived."


def _cases_endpoint(call_id: str) -> str:
    return f"/api/v1/calls/{call_id}/cases"


def _count_support_cases(test_session_factory) -> int:
    session = test_session_factory()
    try:
        return session.scalar(select(func.count()).select_from(SupportCase))
    finally:
        session.close()


def _get_order_status(test_session_factory, order_id: str) -> str:
    session = test_session_factory()
    try:
        return session.scalar(select(Order.status).where(Order.order_id == order_id))
    finally:
        session.close()


def test_scenario_1_verified_delayed_delivery_case(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )

    response = client.post(
        _cases_endpoint(call_id),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": VALID_SUMMARY,
        },
    )
    assert response.status_code == 201

    body = response.json()
    assert body["case_id"].startswith("CASE-")
    assert body["call_id"] == call_id
    assert body["customer_id"] == "CUST-101"
    assert body["order_id"] == "ORD-5001"
    assert body["category"] == "delayed_delivery"
    assert body["status"] == "pending"
    assert body["requires_human_review"] is True

    session = test_session_factory()
    try:
        persisted = session.get(SupportCase, body["case_id"])
        assert persisted is not None
        assert persisted.customer_id == "CUST-101"
        assert persisted.order_id == "ORD-5001"
        assert persisted.status == "pending"
        assert persisted.requires_human_review is True
    finally:
        session.close()


def test_scenario_2_cross_customer_order_protection(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )

    before = _count_support_cases(test_session_factory)
    response = client.post(
        _cases_endpoint(call_id),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5002",
            "summary": VALID_SUMMARY,
        },
    )

    assert response.status_code == 404
    assert "CUST-102" not in response.text
    assert _count_support_cases(test_session_factory) == before


def test_scenario_3_unknown_call_id(client, test_session_factory):
    before = _count_support_cases(test_session_factory)
    response = client.post(
        _cases_endpoint("CALL-does-not-exist"),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": VALID_SUMMARY,
        },
    )

    assert response.status_code == 404
    assert _count_support_cases(test_session_factory) == before


def test_scenario_4_unmatched_caller_cannot_create_case(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="unmatched",
        customer_id=None,
        transfer_required=True,
    )

    before = _count_support_cases(test_session_factory)
    response = client.post(
        _cases_endpoint(call_id),
        json={"category": "human_agent_request", "summary": VALID_SUMMARY},
    )

    assert response.status_code == 409
    assert _count_support_cases(test_session_factory) == before


def test_scenario_5_unavailable_caller_cannot_create_case(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="unavailable",
        customer_id=None,
        transfer_required=True,
    )

    before = _count_support_cases(test_session_factory)
    response = client.post(
        _cases_endpoint(call_id),
        json={"category": "human_agent_request", "summary": VALID_SUMMARY},
    )

    assert response.status_code == 409
    assert _count_support_cases(test_session_factory) == before


def test_scenario_6_invalid_caller_cannot_create_case(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="invalid",
        customer_id=None,
        transfer_required=True,
    )

    before = _count_support_cases(test_session_factory)
    response = client.post(
        _cases_endpoint(call_id),
        json={"category": "human_agent_request", "summary": VALID_SUMMARY},
    )

    assert response.status_code == 409
    assert _count_support_cases(test_session_factory) == before


def test_scenario_7_missing_order_for_order_specific_category(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )

    before = _count_support_cases(test_session_factory)
    response = client.post(
        _cases_endpoint(call_id),
        json={
            "category": "damaged_product",
            "summary": "The product arrived damaged and cannot be used.",
        },
    )

    assert response.status_code == 422
    assert _count_support_cases(test_session_factory) == before


def test_scenario_8_human_agent_request_without_order(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-103",
        transfer_required=False,
    )

    response = client.post(
        _cases_endpoint(call_id),
        json={
            "category": "human_agent_request",
            "summary": "I need to speak with a customer service adviser.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["order_id"] is None
    assert body["status"] == "pending"
    assert body["requires_human_review"] is True
    assert body["customer_id"] == "CUST-103"


def test_scenario_9_invalid_category(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )

    before = _count_support_cases(test_session_factory)
    response = client.post(
        _cases_endpoint(call_id),
        json={
            "category": "refund_approved",
            "order_id": "ORD-5001",
            "summary": VALID_SUMMARY,
        },
    )

    assert response.status_code == 422
    assert _count_support_cases(test_session_factory) == before


def test_scenario_10_blank_summary(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )

    before = _count_support_cases(test_session_factory)
    response = client.post(
        _cases_endpoint(call_id),
        json={"category": "delayed_delivery", "order_id": "ORD-5001", "summary": "   "},
    )

    assert response.status_code == 422
    assert _count_support_cases(test_session_factory) == before


def test_scenario_11_summary_too_short(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )

    before = _count_support_cases(test_session_factory)
    response = client.post(
        _cases_endpoint(call_id),
        json={"category": "delayed_delivery", "order_id": "ORD-5001", "summary": "Delayed"},
    )

    assert response.status_code == 422
    assert _count_support_cases(test_session_factory) == before


def test_scenario_12_malicious_authority_fields_rejected(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )

    before = _count_support_cases(test_session_factory)
    original_status = _get_order_status(test_session_factory, "ORD-5001")

    response = client.post(
        _cases_endpoint(call_id),
        json={
            "category": "cancellation_request",
            "order_id": "ORD-5001",
            "summary": "Please cancel this order because I no longer need it.",
            "status": "approved",
            "requires_human_review": False,
            "customer_id": "CUST-102",
        },
    )

    assert response.status_code == 422
    assert _count_support_cases(test_session_factory) == before
    assert _get_order_status(test_session_factory, "ORD-5001") == original_status


def test_scenario_13_cancellation_request_does_not_cancel_order(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )
    original_status = _get_order_status(test_session_factory, "ORD-5001")

    response = client.post(
        _cases_endpoint(call_id),
        json={
            "category": "cancellation_request",
            "order_id": "ORD-5001",
            "summary": "Please cancel this order because I no longer need it.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["requires_human_review"] is True
    assert _get_order_status(test_session_factory, "ORD-5001") == original_status


def test_scenario_14_return_request_does_not_approve_return(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )
    original_status = _get_order_status(test_session_factory, "ORD-5001")

    response = client.post(
        _cases_endpoint(call_id),
        json={
            "category": "return_request",
            "order_id": "ORD-5001",
            "summary": "I would like to return this item, it does not fit.",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["requires_human_review"] is True
    assert _get_order_status(test_session_factory, "ORD-5001") == original_status
