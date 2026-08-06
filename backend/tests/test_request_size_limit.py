"""Tests for the ASGI request-size limit middleware.

Two levels are used deliberately, and they prove different things:

  * A low-level ASGI harness drives the middleware (or the whole app)
    with a hand-written `receive` callable. This is the ONLY level that
    can prove transport-level behaviour -- that the middleware stops
    asking for body chunks, and that a missing or dishonest
    Content-Length is still caught.

  * Starlette's TestClient materialises the entire request body and hands
    it to the app as a single http.request message. TestClient tests here
    therefore prove ORDERING INSIDE THE APPLICATION (the middleware runs
    before authentication, before multipart parsing, before the service)
    and integration with CORS. They do not, and are not claimed to,
    prove that bytes stopped crossing a wire -- with TestClient there is
    no wire.
"""

import asyncio
import glob
import os
import tempfile

import starlette.formparsers

from backend.app import main as main_module
from backend.app.main import app
from backend.app.middleware.request_size_limit import (
    AUDIO_MAX_REQUEST_BYTES,
    DEFAULT_MAX_REQUEST_BYTES,
    RequestSizeLimitMiddleware,
    limit_for_path,
)
from backend.app.routers import voice_support as voice_support_router
from backend.app.services.demo_auth import get_authenticated_customer

ONE_MIB = 1024 * 1024
AUDIO_PATH = "/api/v1/voice-support/sessions/VOICE-harness/audio"
SESSIONS_ENDPOINT = "/api/v1/voice-support/sessions"


# --------------------------------------------------------------------------
# Low-level ASGI harness
# --------------------------------------------------------------------------


class _Receiver:
    """Hand-written ASGI receive that records how often it was called.

    The call count is the whole point: it is what proves the middleware
    stopped consuming the body rather than draining it.
    """

    def __init__(self, chunks):
        self._chunks = list(chunks)
        self.calls = 0

    async def __call__(self):
        self.calls += 1
        if self._chunks:
            body = self._chunks.pop(0)
            return {"type": "http.request", "body": body, "more_body": bool(self._chunks)}
        return {"type": "http.request", "body": b"", "more_body": False}


class _Sender:
    """Collects the ASGI response messages the app sent."""

    def __init__(self):
        self.messages = []

    async def __call__(self, message):
        self.messages.append(message)

    @property
    def status(self):
        for message in self.messages:
            if message["type"] == "http.response.start":
                return message["status"]
        return None

    @property
    def body(self):
        return b"".join(
            message.get("body", b"")
            for message in self.messages
            if message["type"] == "http.response.body"
        )

    @property
    def start_count(self):
        return sum(1 for message in self.messages if message["type"] == "http.response.start")

    def header(self, name):
        for message in self.messages:
            if message["type"] == "http.response.start":
                for key, value in message.get("headers", []):
                    if key.lower() == name.lower().encode():
                        return value
        return None


def _scope(path, *, content_length=None, content_type=None, method="POST", extra_headers=()):
    headers = [(b"host", b"testserver")]
    if content_length is not None:
        headers.append((b"content-length", str(content_length).encode()))
    if content_type is not None:
        headers.append((b"content-type", content_type.encode()))
    headers.extend(extra_headers)
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 54321),
        "server": ("testserver", 80),
    }


async def _draining_app(scope, receive, send):
    """Stand-in for a real parser: reads the body until it is exhausted."""
    while True:
        message = await receive()
        if message["type"] != "http.request":
            break
        if not message.get("more_body", False):
            break
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


def _run_middleware(scope, receiver):
    sender = _Sender()
    middleware = RequestSizeLimitMiddleware(_draining_app)
    asyncio.run(middleware(scope, receiver, sender))
    return sender


# --------------------------------------------------------------------------
# limit_for_path
# --------------------------------------------------------------------------


def test_audio_route_gets_the_larger_limit():
    assert limit_for_path(AUDIO_PATH) == AUDIO_MAX_REQUEST_BYTES
    assert AUDIO_MAX_REQUEST_BYTES == 11 * 1024 * 1024


def test_every_other_route_gets_the_default_limit():
    assert DEFAULT_MAX_REQUEST_BYTES == 1024 * 1024
    for path in ("/health", "/api/v1/calls/start", SESSIONS_ENDPOINT, "/api/v1/calls/x/cases"):
        assert limit_for_path(path) == DEFAULT_MAX_REQUEST_BYTES


def test_audio_tier_is_not_widened_by_a_partial_path_match():
    # Prefix without suffix, and suffix without prefix, both stay on the
    # tight default tier.
    assert limit_for_path(SESSIONS_ENDPOINT + "/VOICE-1") == DEFAULT_MAX_REQUEST_BYTES
    assert limit_for_path("/api/v1/calls/audio") == DEFAULT_MAX_REQUEST_BYTES


# --------------------------------------------------------------------------
# A1-A4, A10: transport-level behaviour (ASGI harness)
# --------------------------------------------------------------------------


def test_honest_oversized_content_length_is_rejected_without_reading_a_byte():
    """A1: the Content-Length fast path costs zero body reads."""
    receiver = _Receiver([b"x" * ONE_MIB] * 20)
    sender = _run_middleware(_scope(AUDIO_PATH, content_length=20 * ONE_MIB), receiver)

    assert sender.status == 413
    assert receiver.calls == 0
    assert b"too large" in sender.body


def test_missing_content_length_is_still_limited():
    """A2: absence of a declaration must never be read as permission."""
    receiver = _Receiver([b"x" * ONE_MIB] * 20)
    sender = _run_middleware(_scope(AUDIO_PATH, content_length=None), receiver)

    assert sender.status == 413
    assert sender.start_count == 1
    # The inner app never got to answer.
    assert sender.body != b"ok"


def test_false_smaller_content_length_is_still_limited():
    """A3: a lie that slips past the fast path is caught by the counter."""
    receiver = _Receiver([b"x" * ONE_MIB] * 20)
    sender = _run_middleware(_scope(AUDIO_PATH, content_length=100), receiver)

    assert sender.status == 413
    assert sender.start_count == 1


def test_middleware_stops_requesting_chunks_once_the_limit_is_crossed():
    """A4: the body is abandoned, not drained."""
    receiver = _Receiver([b"x" * ONE_MIB] * 20)
    sender = _run_middleware(_scope(AUDIO_PATH, content_length=None), receiver)

    assert sender.status == 413
    # 11 MiB limit: chunk 12 is the one that crosses it, and nothing is
    # read afterwards. Emphatically not all 20.
    assert receiver.calls == 12


def test_audio_route_accepts_a_body_up_to_its_full_request_limit():
    """Exactly 11 MiB passes the transport cap untouched."""
    receiver = _Receiver([b"x" * ONE_MIB] * 11)
    sender = _run_middleware(
        _scope(AUDIO_PATH, content_length=AUDIO_MAX_REQUEST_BYTES), receiver
    )

    assert sender.status == 200
    assert sender.body == b"ok"
    assert receiver.calls == 11


def test_default_tier_rejects_a_body_the_audio_tier_would_accept():
    """A10: the two tiers really are different."""
    body_chunks = [b"x" * ONE_MIB] * 2

    rejected = _run_middleware(
        _scope("/api/v1/calls/start", content_length=None), _Receiver(body_chunks)
    )
    assert rejected.status == 413

    accepted = _run_middleware(_scope(AUDIO_PATH, content_length=None), _Receiver(body_chunks))
    assert accepted.status == 200


def test_non_http_scopes_pass_straight_through():
    seen = {}

    async def inner(scope, receive, send):
        seen["type"] = scope["type"]

    asyncio.run(RequestSizeLimitMiddleware(inner)({"type": "lifespan"}, _Receiver([]), _Sender()))
    assert seen["type"] == "lifespan"


def test_bodyless_request_is_unaffected():
    receiver = _Receiver([])
    sender = _run_middleware(_scope("/health", method="GET", content_length=0), receiver)

    assert sender.status == 200
    assert sender.body == b"ok"


# --------------------------------------------------------------------------
# Transport-level rejection against the REAL application (no TestClient)
# --------------------------------------------------------------------------


def test_real_app_rejects_undeclared_oversized_body_before_auth_or_service(monkeypatch):
    """The strongest proof available: the real middleware stack, a real
    route, a hand-written receive, and no Content-Length at all.

    Because the harness feeds chunks rather than a materialised body,
    this shows the request is refused while it is still arriving.
    """
    auth_calls = []
    service_calls = []

    def _spy_auth():
        auth_calls.append(True)

    async def _spy_service(*args, **kwargs):
        service_calls.append(True)

    monkeypatch.setattr(voice_support_router, "transcribe_uploaded_audio", _spy_service)
    app.dependency_overrides[get_authenticated_customer] = _spy_auth
    try:
        receiver = _Receiver([b"x" * (12 * ONE_MIB)])
        sender = _Sender()
        asyncio.run(
            app(
                _scope(
                    AUDIO_PATH,
                    content_length=None,
                    content_type="multipart/form-data; boundary=harness",
                ),
                receiver,
                sender,
            )
        )
    finally:
        app.dependency_overrides.pop(get_authenticated_customer, None)

    assert sender.status == 413
    assert sender.start_count == 1
    # Must be the middleware's own 413, not FastAPI's 400 body-parsing
    # error: FastAPI wraps parsing in `except Exception`, which is why the
    # internal signal derives from BaseException.
    assert b"Request body is too large." in sender.body
    assert receiver.calls == 1, "the body must be abandoned after the first oversized chunk"
    assert auth_calls == [], "authentication must never run for a rejected request"
    assert service_calls == [], "the voice-support service must never run"


def test_real_app_rejects_false_content_length_before_auth_or_service(monkeypatch):
    auth_calls = []
    service_calls = []

    def _spy_auth():
        auth_calls.append(True)

    async def _spy_service(*args, **kwargs):
        service_calls.append(True)

    monkeypatch.setattr(voice_support_router, "transcribe_uploaded_audio", _spy_service)
    app.dependency_overrides[get_authenticated_customer] = _spy_auth
    try:
        receiver = _Receiver([b"x" * (12 * ONE_MIB)])
        sender = _Sender()
        asyncio.run(
            app(
                _scope(
                    AUDIO_PATH,
                    content_length=100,
                    content_type="multipart/form-data; boundary=harness",
                ),
                receiver,
                sender,
            )
        )
    finally:
        app.dependency_overrides.pop(get_authenticated_customer, None)

    assert sender.status == 413
    assert b"Request body is too large." in sender.body
    assert receiver.calls == 1
    assert auth_calls == []
    assert service_calls == []


# --------------------------------------------------------------------------
# A5-A9: in-application ordering and integration (TestClient)
# --------------------------------------------------------------------------


def _temp_voice_support_file_count():
    return len(glob.glob(os.path.join(tempfile.gettempdir(), "voice-support-*")))


def test_oversized_request_is_rejected_before_auth_parsing_and_service(client, monkeypatch):
    """A5: three independent spies, none of which may fire.

    TestClient materialises the body, so this proves ordering within the
    application -- not that transmission was cut short. The harness tests
    above cover that.
    """
    auth_calls = []
    parse_calls = []
    service_calls = []

    def _spy_auth():
        auth_calls.append(True)

    async def _spy_parse(self, *args, **kwargs):
        parse_calls.append(True)

    async def _spy_service(*args, **kwargs):
        service_calls.append(True)

    monkeypatch.setattr(starlette.formparsers.MultiPartParser, "parse", _spy_parse)
    monkeypatch.setattr(voice_support_router, "transcribe_uploaded_audio", _spy_service)
    app.dependency_overrides[get_authenticated_customer] = _spy_auth
    try:
        response = client.post(
            AUDIO_PATH,
            files={"audio": ("voice-support.webm", b"0" * (12 * ONE_MIB), "audio/webm")},
        )
    finally:
        app.dependency_overrides.pop(get_authenticated_customer, None)

    assert response.status_code == 413
    assert response.json() == {"detail": "Request body is too large."}
    assert auth_calls == []
    assert parse_calls == []
    assert service_calls == []


def test_no_authorization_header_still_yields_413_not_401(client):
    """Rejection precedes authentication, so the size error wins."""
    response = client.post(
        AUDIO_PATH,
        files={"audio": ("voice-support.webm", b"0" * (12 * ONE_MIB), "audio/webm")},
    )

    assert response.status_code == 413


def test_no_temporary_audio_file_remains_after_rejection(client):
    """A6: the service never ran, so it created no temp file."""
    before = _temp_voice_support_file_count()

    response = client.post(
        AUDIO_PATH,
        headers={"Authorization": "Bearer demo-cust-101"},
        files={"audio": ("voice-support.webm", b"0" * (12 * ONE_MIB), "audio/webm")},
    )

    assert response.status_code == 413
    assert _temp_voice_support_file_count() == before


def test_oversized_json_request_on_a_normal_route_is_rejected(client):
    """The 1 MiB default tier applies to the telephony APIs."""
    response = client.post(
        "/api/v1/calls/start",
        json={"incoming_phone": "07700 900101", "padding": "x" * (2 * ONE_MIB)},
    )

    assert response.status_code == 413


def test_existing_valid_audio_upload_still_passes(client):
    """A7: nothing about the happy path changed."""
    start = client.post(SESSIONS_ENDPOINT, headers={"Authorization": "Bearer demo-cust-101"})
    assert start.status_code == 201
    session_id = start.json()["session_id"]

    response = client.post(
        f"{SESSIONS_ENDPOINT}/{session_id}/audio",
        headers={"Authorization": "Bearer demo-cust-101"},
        files={"audio": ("voice-support.webm", b"fake-audio-bytes-for-test", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "transcribed"


def test_audio_between_the_two_limits_is_rejected_by_the_endpoint_not_the_middleware(client):
    """The layers are genuinely separate.

    10.5 MiB clears the 11 MiB transport cap and is then refused by the
    unchanged 10 MB audio-content rule -- identifiable by its message.
    """
    start = client.post(SESSIONS_ENDPOINT, headers={"Authorization": "Bearer demo-cust-101"})
    session_id = start.json()["session_id"]

    response = client.post(
        f"{SESSIONS_ENDPOINT}/{session_id}/audio",
        headers={"Authorization": "Bearer demo-cust-101"},
        files={
            "audio": (
                "voice-support.webm",
                b"0" * (10 * ONE_MIB + ONE_MIB // 2),
                "audio/webm",
            )
        },
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Audio exceeds the 10 MB limit."


def test_existing_json_and_telephone_apis_still_pass(client, make_call_record):
    """A8: regression guard over every other route."""
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "healthy"}

    call = client.post("/api/v1/calls/start", json={"incoming_phone": "07700 900101"})
    assert call.status_code == 200
    assert call.json()["verification_status"] == "verified"

    call_id = make_call_record(
        verification_status="verified", customer_id="CUST-101", transfer_required=False
    )
    case = client.post(
        f"/api/v1/calls/{call_id}/cases",
        json={
            "category": "delayed_delivery",
            "order_id": "ORD-5001",
            "summary": "My order was due yesterday and has not arrived.",
        },
    )
    assert case.status_code == 201


def test_413_response_carries_cors_headers(client):
    """A9: proves the size middleware sits INSIDE CORSMiddleware.

    If the ordering in main.py were reversed, this header would be
    missing and a browser would surface an opaque network error instead
    of the real 413.
    """
    origin = "http://localhost:5173"

    response = client.post(
        AUDIO_PATH,
        headers={"Origin": origin},
        files={"audio": ("voice-support.webm", b"0" * (12 * ONE_MIB), "audio/webm")},
    )

    assert response.status_code == 413
    assert response.headers.get("access-control-allow-origin") == origin


def test_cors_middleware_is_registered_outside_the_size_limit():
    """Guards the ordering directly, independently of any request."""
    classes = [middleware.cls for middleware in main_module.app.user_middleware]
    from fastapi.middleware.cors import CORSMiddleware

    assert classes.index(CORSMiddleware) < classes.index(RequestSizeLimitMiddleware), (
        "CORSMiddleware must be the outermost layer: user_middleware is ordered "
        "outermost-first, so it must appear before RequestSizeLimitMiddleware."
    )
