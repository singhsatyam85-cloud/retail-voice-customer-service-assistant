"""In-memory conversation history manager per voice session."""

from __future__ import annotations

_SESSION_HISTORIES: dict[str, list[dict[str, str]]] = {}


def get_session_history(session_id: str) -> list[dict[str, str]]:
    return _SESSION_HISTORIES.get(session_id, [])


def add_session_turn(session_id: str, role: str, content: str) -> None:
    if session_id not in _SESSION_HISTORIES:
        _SESSION_HISTORIES[session_id] = []
    _SESSION_HISTORIES[session_id].append({"role": role, "content": content})


def clear_session_history(session_id: str) -> None:
    _SESSION_HISTORIES.pop(session_id, None)
