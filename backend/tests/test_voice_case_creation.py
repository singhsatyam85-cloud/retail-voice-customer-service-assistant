import pytest
from sqlalchemy import func, select
from backend.app.models import SupportCase

VALID_SUMMARY = "My order was due yesterday and has not arrived."


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _voice_cases_endpoint(session_id: str) -> str:
    return f"/api/v1/voice-support/sessions/{session_id}/cases"


def _calls_cases_endpoint(call_id: str) -> str:
    return f"/api/v1/calls/{call_id}/cases"


def _count_support_cases(test_session_factory) -> int:
    session = test_session_factory()
    try:
        return session.scalar(select(func.count()).select_from(SupportCase))
    finally:
        session.close()


def _start_voice_session(client, token: str) -> str:
    response = client.post("/api/v1/voice-support/sessions", headers=_auth(token))
    assert response.status_code == 201
    return response.json()["session_id"]


def test_scenario_1_valid_voice_session_case_creation(client, test_session_factory):
    session_id = _start_voice_session(client, "demo-cust-101")
    before = _count_support_cases(test_session_factory)

    response = client.post(
        _voice_cases_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": VALID_SUMMARY,
            "idempotency_key": "idemp-key-101"
        }
    )
    assert response.status_code == 201
    body = response.json()
    assert body["case_id"].startswith("CASE-")
    assert body["voice_session_id"] == session_id
    assert body["customer_id"] == "CUST-101"
    assert body["order_id"] == "ORD-5001"
    assert body["category"] == "delayed_delivery"
    assert body["status"] == "pending"
    assert body["requires_human_review"] is True
    assert _count_support_cases(test_session_factory) == before + 1


def test_scenario_2_wrong_customer_session_access(client, test_session_factory):
    session_id = _start_voice_session(client, "demo-cust-101")
    before = _count_support_cases(test_session_factory)

    response = client.post(
        _voice_cases_endpoint(session_id),
        headers=_auth("demo-cust-102"),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": VALID_SUMMARY,
            "idempotency_key": "idemp-key-102"
        }
    )
    assert response.status_code == 404
    assert _count_support_cases(test_session_factory) == before


def test_scenario_3_order_ownership(client, test_session_factory):
    session_id = _start_voice_session(client, "demo-cust-101")
    before = _count_support_cases(test_session_factory)

    # ORD-5002 belongs to CUST-102, CUST-101 cannot access it
    response = client.post(
        _voice_cases_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5002",
            "summary": VALID_SUMMARY,
            "idempotency_key": "idemp-key-103"
        }
    )
    assert response.status_code == 404
    assert _count_support_cases(test_session_factory) == before


def test_scenario_4_human_agent_request_without_order(client, test_session_factory):
    session_id = _start_voice_session(client, "demo-cust-103")
    before = _count_support_cases(test_session_factory)

    response = client.post(
        _voice_cases_endpoint(session_id),
        headers=_auth("demo-cust-103"),
        json={
            "category": "human_agent_request",
            "summary": "I need to talk to a person.",
            "idempotency_key": "idemp-key-104"
        }
    )
    assert response.status_code == 201
    body = response.json()
    assert body["order_id"] is None
    assert body["status"] == "pending"
    assert body["requires_human_review"] is True
    assert _count_support_cases(test_session_factory) == before + 1


def test_scenario_5_pending_status_and_human_review_enforcement(client, test_session_factory):
    session_id = _start_voice_session(client, "demo-cust-101")

    # Try to override status and requires_human_review (CreateVoiceCaseRequest inherits CreateCaseRequest which forbids extra fields)
    response = client.post(
        _voice_cases_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": VALID_SUMMARY,
            "idempotency_key": "idemp-key-105",
            "status": "approved",
            "requires_human_review": False
        }
    )
    assert response.status_code == 422


def test_scenario_6_repeated_idempotency_key(client, test_session_factory):
    session_id = _start_voice_session(client, "demo-cust-101")
    before = _count_support_cases(test_session_factory)

    response1 = client.post(
        _voice_cases_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": VALID_SUMMARY,
            "idempotency_key": "idemp-key-uniq"
        }
    )
    assert response1.status_code == 201
    body1 = response1.json()

    # Repeat request with same idempotency key
    response2 = client.post(
        _voice_cases_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": VALID_SUMMARY,
            "idempotency_key": "idemp-key-uniq"
        }
    )
    assert response2.status_code == 201
    body2 = response2.json()
    
    assert body1["case_id"] == body2["case_id"]
    assert _count_support_cases(test_session_factory) == before + 1


def test_scenario_7_new_idempotency_key(client, test_session_factory):
    session_id = _start_voice_session(client, "demo-cust-101")
    before = _count_support_cases(test_session_factory)

    response1 = client.post(
        _voice_cases_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": VALID_SUMMARY,
            "idempotency_key": "idemp-key-a"
        }
    )
    assert response1.status_code == 201

    response2 = client.post(
        _voice_cases_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": VALID_SUMMARY,
            "idempotency_key": "idemp-key-b"
        }
    )
    assert response2.status_code == 201

    assert _count_support_cases(test_session_factory) == before + 2


def test_scenario_8_existing_call_based_route_remains_working(client, test_session_factory, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )
    before = _count_support_cases(test_session_factory)

    response = client.post(
        _calls_cases_endpoint(call_id),
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": VALID_SUMMARY,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["call_id"] == call_id
    assert body["voice_session_id"] is None
    assert _count_support_cases(test_session_factory) == before + 1
