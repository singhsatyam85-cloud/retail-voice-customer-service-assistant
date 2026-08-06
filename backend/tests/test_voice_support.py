import glob
import os
import tempfile

from sqlalchemy import func, select

from backend.app.main import app
from backend.app.models import CallRecord, Customer, Order, SupportCase, VoiceSupportSession
from backend.app.services.speech_to_text.base import (
    SpeechToTextProvider,
    SpeechToTextUnavailableError,
    TranscriptionResult,
)
from backend.app.services.speech_to_text.factory import get_speech_to_text_provider

SESSIONS_ENDPOINT = "/api/v1/voice-support/sessions"


def _audio_endpoint(session_id: str) -> str:
    return f"{SESSIONS_ENDPOINT}/{session_id}/audio"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _count(test_session_factory, model) -> int:
    session = test_session_factory()
    try:
        return session.scalar(select(func.count()).select_from(model))
    finally:
        session.close()


def _get_voice_session(test_session_factory, session_id: str):
    session = test_session_factory()
    try:
        return session.get(VoiceSupportSession, session_id)
    finally:
        session.close()


def _get_order_status(test_session_factory, order_id: str) -> str:
    session = test_session_factory()
    try:
        return session.scalar(select(Order.status).where(Order.order_id == order_id))
    finally:
        session.close()


def _audio_file(content_type: str = "audio/webm", content: bytes = b"fake-audio-bytes-for-test"):
    return {"audio": ("voice-support.webm", content, content_type)}


def _temp_voice_support_file_count() -> int:
    pattern = os.path.join(tempfile.gettempdir(), "voice-support-*")
    return len(glob.glob(pattern))


class _FailingProvider(SpeechToTextProvider):
    def transcribe(self, audio_file_path: str) -> TranscriptionResult:
        raise SpeechToTextUnavailableError("simulated provider failure")


def _start_session(client, token: str) -> str:
    response = client.post(SESSIONS_ENDPOINT, headers=_auth(token))
    assert response.status_code == 201
    return response.json()["session_id"]


def test_scenario_1_valid_token_starts_session_for_cust_101(client):
    response = client.post(SESSIONS_ENDPOINT, headers=_auth("demo-cust-101"))
    assert response.status_code == 201

    body = response.json()
    assert body["session_id"].startswith("VOICE-")
    assert body["customer"]["customer_id"] == "CUST-101"

    order_ids = {order["order_id"] for order in body["recent_orders"]}
    assert order_ids == {"ORD-5001"}


def test_scenario_2_cust_102_sees_only_own_orders(client):
    response = client.post(SESSIONS_ENDPOINT, headers=_auth("demo-cust-102"))
    assert response.status_code == 201

    body = response.json()
    assert body["customer"]["customer_id"] == "CUST-102"
    order_ids = {order["order_id"] for order in body["recent_orders"]}
    assert order_ids == {"ORD-5002", "ORD-5003"}
    assert "ORD-5001" not in order_ids


def test_scenario_3_cust_103_has_no_orders(client):
    response = client.post(SESSIONS_ENDPOINT, headers=_auth("demo-cust-103"))
    assert response.status_code == 201

    body = response.json()
    assert body["customer"]["customer_id"] == "CUST-103"
    assert body["recent_orders"] == []


def test_scenario_4_missing_authorization_header(client, test_session_factory):
    before = _count(test_session_factory, VoiceSupportSession)
    response = client.post(SESSIONS_ENDPOINT)
    assert response.status_code == 401
    assert _count(test_session_factory, VoiceSupportSession) == before


def test_scenario_5_invalid_demo_token(client, test_session_factory):
    before = _count(test_session_factory, VoiceSupportSession)
    response = client.post(SESSIONS_ENDPOINT, headers=_auth("demo-cust-999"))
    assert response.status_code == 401
    assert "CUST-" not in response.text
    assert _count(test_session_factory, VoiceSupportSession) == before


def test_scenario_6_inactive_customer_rejected(client, test_session_factory):
    session = test_session_factory()
    try:
        customer = session.get(Customer, "CUST-103")
        customer.is_active = False
        session.commit()
    finally:
        session.close()

    before = _count(test_session_factory, VoiceSupportSession)
    response = client.post(SESSIONS_ENDPOINT, headers=_auth("demo-cust-103"))
    assert response.status_code == 403
    assert _count(test_session_factory, VoiceSupportSession) == before


def test_scenario_7_valid_audio_upload_with_mock_provider(client, test_session_factory):
    session_id = _start_session(client, "demo-cust-101")

    response = client.post(
        _audio_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        files=_audio_file(),
    )
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "transcribed"
    assert body["transcript"]
    assert body["detected_language"] == "en"

    persisted = _get_voice_session(test_session_factory, session_id)
    assert persisted.status == "transcribed"
    assert persisted.transcript == body["transcript"]


def test_scenario_8_cross_customer_audio_upload_blocked(client, test_session_factory):
    session_id = _start_session(client, "demo-cust-101")

    response = client.post(
        _audio_endpoint(session_id),
        headers=_auth("demo-cust-102"),
        files=_audio_file(),
    )
    assert response.status_code == 404
    assert "transcript" not in response.text.lower()

    persisted = _get_voice_session(test_session_factory, session_id)
    assert persisted.status == "started"
    assert persisted.transcript is None


def test_scenario_9_unknown_session_id(client):
    response = client.post(
        _audio_endpoint("VOICE-does-not-exist"),
        headers=_auth("demo-cust-101"),
        files=_audio_file(),
    )
    assert response.status_code == 404


def test_scenario_10_unsupported_mime_type(client, test_session_factory):
    session_id = _start_session(client, "demo-cust-101")

    response = client.post(
        _audio_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        files=_audio_file(content_type="text/plain"),
    )
    assert response.status_code == 415

    persisted = _get_voice_session(test_session_factory, session_id)
    assert persisted.status == "started"
    assert persisted.transcript is None


def test_scenario_11_empty_audio(client, test_session_factory):
    session_id = _start_session(client, "demo-cust-101")

    response = client.post(
        _audio_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        files=_audio_file(content=b""),
    )
    assert response.status_code == 400

    persisted = _get_voice_session(test_session_factory, session_id)
    assert persisted.transcript is None


def test_scenario_12_audio_larger_than_10mb(client, test_session_factory):
    session_id = _start_session(client, "demo-cust-101")
    oversized = b"0" * (10 * 1024 * 1024 + 1)

    response = client.post(
        _audio_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        files=_audio_file(content=oversized),
    )
    assert response.status_code == 413

    persisted = _get_voice_session(test_session_factory, session_id)
    assert persisted.transcript is None


def test_scenario_13_temp_file_cleanup_after_success(client):
    session_id = _start_session(client, "demo-cust-101")

    before = _temp_voice_support_file_count()
    response = client.post(
        _audio_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        files=_audio_file(),
    )
    assert response.status_code == 200
    assert _temp_voice_support_file_count() == before


def test_scenario_14_temp_file_cleanup_after_provider_failure(client, test_session_factory):
    session_id = _start_session(client, "demo-cust-101")

    app.dependency_overrides[get_speech_to_text_provider] = lambda: _FailingProvider()
    try:
        before = _temp_voice_support_file_count()
        response = client.post(
            _audio_endpoint(session_id),
            headers=_auth("demo-cust-101"),
            files=_audio_file(),
        )
    finally:
        app.dependency_overrides.pop(get_speech_to_text_provider, None)

    assert response.status_code == 503
    assert _temp_voice_support_file_count() == before

    persisted = _get_voice_session(test_session_factory, session_id)
    assert persisted.status == "failed"
    assert persisted.transcript is None


def test_scenario_15_no_business_action_taken(client, test_session_factory):
    support_cases_before = _count(test_session_factory, SupportCase)
    call_records_before = _count(test_session_factory, CallRecord)
    order_status_before = _get_order_status(test_session_factory, "ORD-5001")

    session_id = _start_session(client, "demo-cust-101")
    response = client.post(
        _audio_endpoint(session_id),
        headers=_auth("demo-cust-101"),
        files=_audio_file(),
    )
    assert response.status_code == 200

    assert _count(test_session_factory, SupportCase) == support_cases_before
    assert _count(test_session_factory, CallRecord) == call_records_before
    assert _get_order_status(test_session_factory, "ORD-5001") == order_status_before


def test_scenario_16_existing_apis_still_work(client, make_call_record):
    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "healthy"}

    call_response = client.post("/api/v1/calls/start", json={"incoming_phone": "07700 900101"})
    assert call_response.status_code == 200
    assert call_response.json()["verification_status"] == "verified"

    verified_call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )
    case_response = client.post(
        f"/api/v1/calls/{verified_call_id}/cases",
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": "My order was due yesterday and has not arrived.",
        },
    )
    assert case_response.status_code == 201
