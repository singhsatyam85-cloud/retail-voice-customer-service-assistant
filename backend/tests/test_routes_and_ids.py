"""Confirms the agreed route paths and backend-generated identifier format.

These checks exist so a future accidental route rename (e.g. dropping the
/api/v1 prefix) or a truncated UUID would fail a test immediately, rather
than only surfacing in a live smoke test.
"""

from __future__ import annotations

VALID_SUMMARY = "My order was due yesterday and has not arrived."


def test_verification_route_is_api_v1_calls_start(client):
    response = client.post("/api/v1/calls/start", json={"incoming_phone": "07700 900101"})
    assert response.status_code == 200

    body = response.json()
    assert body["call_id"].startswith("CALL-")
    assert len(body["call_id"]) <= 50


def test_unversioned_calls_start_path_does_not_exist(client):
    response = client.post("/calls/start", json={"incoming_phone": "07700 900101"})
    assert response.status_code == 404


def test_case_creation_route_is_api_v1_calls_call_id_cases(client, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )

    response = client.post(
        f"/api/v1/calls/{call_id}/cases",
        json={"category": "delayed_delivery", "order_id": "ORD-5001", "summary": VALID_SUMMARY},
    )
    assert response.status_code == 201

    body = response.json()
    assert body["case_id"].startswith("CASE-")
    assert len(body["case_id"]) <= 50


def test_unversioned_case_creation_path_does_not_exist(client, make_call_record):
    call_id = make_call_record(
        verification_status="verified",
        customer_id="CUST-101",
        transfer_required=False,
    )

    response = client.post(
        f"/calls/{call_id}/cases",
        json={"category": "delayed_delivery", "order_id": "ORD-5001", "summary": VALID_SUMMARY},
    )
    assert response.status_code == 404


def test_openapi_paths_match_agreed_contract(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200

    paths = response.json()["paths"]
    assert "/api/v1/calls/start" in paths
    assert "/api/v1/calls/{call_id}/cases" in paths
    assert "/calls/start" not in paths
    assert "/calls/{call_id}/cases" not in paths
