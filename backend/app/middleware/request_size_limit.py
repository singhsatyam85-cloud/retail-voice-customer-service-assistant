"""Reject oversized request bodies before FastAPI parses them.

The endpoint-level 10 MB audio check in
backend/app/services/voice_support.py runs far too late to be a defence:
by the time it executes, Starlette's MultiPartParser has already received
the whole request body and spooled anything over 1 MB to disk. Worse,
FastAPI resolves the request body *before* it solves dependencies, so
Depends(get_authenticated_customer) runs after the upload has been
parsed -- an unauthenticated caller can make the server receive and spool
an arbitrarily large body and only then be told 401.

This middleware closes that gap at the ASGI layer, before any of the
above happens. It is a cap on the raw request, not a replacement for the
10 MB audio-content rule, which stays exactly where it is as defence in
depth. See docs/04-in-app-voice-support-foundation.md.
"""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Iterable, MutableMapping, Optional

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

# Every other route in this application takes a small JSON body, so the
# default cap is deliberately tight.
DEFAULT_MAX_REQUEST_BYTES = 1 * 1024 * 1024  # 1 MiB

# The audio route carries a 10 MiB file plus multipart framing. Real
# framing for the request the frontend sends is ~196 bytes (~450 bytes
# worst case with a 255-character filename), and the HTTP request line
# and headers are not counted at all because only ASGI http.request body
# bytes are measured. 11 MiB therefore leaves over a megabyte of
# headroom, so multipart overhead can never reject a legitimate 10 MiB
# recording.
AUDIO_MAX_REQUEST_BYTES = 11 * 1024 * 1024  # 11 MiB

AUDIO_PATH_PREFIX = "/api/v1/voice-support/sessions/"
AUDIO_PATH_SUFFIX = "/audio"

_TOO_LARGE_BODY = json.dumps({"detail": "Request body is too large."}).encode("utf-8")


class _RequestBodyTooLarge(BaseException):
    """Internal signal raised out of the wrapped receive callable.

    Deliberately derived from BaseException, NOT Exception. FastAPI wraps
    request-body parsing in `except Exception` and re-raises it as
    HTTPException(400, "There was an error parsing the body"), and
    Starlette's ServerErrorMiddleware likewise catches Exception. A
    normal exception is therefore swallowed and the caller sees 400
    instead of 413. Deriving from BaseException lets the signal travel
    untouched to __call__ below, which is the only place that handles it.

    Never escapes this module: __call__ catches it and turns it into the
    413 response.
    """


def limit_for_path(path: str) -> int:
    """Return the request-body cap that applies to path.

    The permissive tier is scoped as narrowly as the route itself. A
    crafted path satisfying both the prefix and the suffix can only reach
    the audio endpoint or a 404, so it cannot widen the cap for any other
    handler.
    """
    if path.startswith(AUDIO_PATH_PREFIX) and path.endswith(AUDIO_PATH_SUFFIX):
        return AUDIO_MAX_REQUEST_BYTES
    return DEFAULT_MAX_REQUEST_BYTES


def _declared_content_length(headers: Iterable[tuple[bytes, bytes]]) -> Optional[int]:
    """Parse Content-Length, or None if absent/unparseable/negative.

    None means "no usable declaration", which must never be read as
    permission -- see __call__.
    """
    for name, value in headers:
        if name.lower() == b"content-length":
            try:
                declared = int(value)
            except (TypeError, ValueError):
                return None
            return declared if declared >= 0 else None
    return None


def _signals_body_too_large(exc: BaseException) -> bool:
    """True if exc is, or wraps, the internal too-large signal."""
    if isinstance(exc, _RequestBodyTooLarge):
        return True
    if isinstance(exc, BaseExceptionGroup):
        return any(_signals_body_too_large(inner) for inner in exc.exceptions)
    return False


async def _send_too_large(send: Send) -> None:
    """Emit the 413 in the same {"detail": ...} shape as every other error.

    Connection: close because the remaining body was deliberately not
    drained, so the connection is not safely reusable.
    """
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(_TOO_LARGE_BODY)).encode("ascii")),
                (b"connection", b"close"),
            ],
        }
    )
    await send({"type": "http.response.body", "body": _TOO_LARGE_BODY, "more_body": False})


class RequestSizeLimitMiddleware:
    """Cap request bodies by counting actual ASGI body bytes.

    Must be registered *inside* CORSMiddleware (i.e. added to the app
    before it), so that a 413 still carries Access-Control-Allow-Origin
    and the browser reports the real status instead of an opaque network
    error.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        limit_for_path: Callable[[str], int] = limit_for_path,
    ) -> None:
        self.app = app
        self._limit_for_path = limit_for_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            # lifespan and websocket scopes carry no http.request body.
            await self.app(scope, receive, send)
            return

        limit = self._limit_for_path(scope.get("path", ""))

        # Fast path only. A caller that honestly declares an oversized
        # body is rejected without a single body byte being read.
        declared = _declared_content_length(scope.get("headers") or ())
        if declared is not None and declared > limit:
            await _send_too_large(send)
            return

        # There is deliberately no "else: allow" branch. A missing,
        # unparseable or dishonestly small Content-Length falls straight
        # through to the counter below, which enforces the same limit
        # against the bytes that actually arrive -- so Content-Length is
        # never the permitting decision.
        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    # Raising rather than returning unwinds the whole
                    # downstream stack, so this callable is never invoked
                    # again and the rest of the body is never read.
                    raise _RequestBodyTooLarge()
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, guarded_send)
        except BaseException as exc:
            if not _signals_body_too_large(exc):
                raise
            # User middleware sits inside Starlette's ServerErrorMiddleware
            # and outside its ExceptionMiddleware, so this runs before
            # anything can turn the signal into a 500.
            if not response_started:
                await _send_too_large(send)
