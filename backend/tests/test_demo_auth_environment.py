from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.app.services import demo_auth


def test_demo_auth_allowed_in_development(monkeypatch):
    monkeypatch.setattr(
        demo_auth,
        "get_settings",
        lambda: SimpleNamespace(app_environment="development"),
    )

    demo_auth._ensure_demo_auth_allowed()


def test_demo_auth_allowed_in_test(monkeypatch):
    monkeypatch.setattr(
        demo_auth,
        "get_settings",
        lambda: SimpleNamespace(app_environment="test"),
    )

    demo_auth._ensure_demo_auth_allowed()


@pytest.mark.parametrize("environment", ["production", "staging", "prod", "unknown", ""])
def test_demo_auth_rejected_outside_safe_environments(monkeypatch, environment):
    monkeypatch.setattr(
        demo_auth,
        "get_settings",
        lambda: SimpleNamespace(app_environment=environment),
    )

    with pytest.raises(HTTPException) as exc_info:
        demo_auth._ensure_demo_auth_allowed()

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Demo authentication is unavailable in this environment."
