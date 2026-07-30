from backend.app.models import CallRecord

ENDPOINT = "/api/v1/calls/start"


def _get_call_record(test_session_factory, call_id):
    session = test_session_factory()
    try:
        return session.get(CallRecord, call_id)
    finally:
        session.close()


def test_scenario_1_uk_local_number_one_order(client, test_session_factory):
    response = client.post(ENDPOINT, json={"incoming_phone": "07700 900101"})
    assert response.status_code == 200

    body = response.json()
    assert body["verification_status"] == "verified"
    assert body["transfer_required"] is False
    assert body["customer"]["customer_id"] == "CUST-101"
    assert len(body["orders"]) == 1
    assert body["orders"][0]["order_id"] == "ORD-5001"
    assert body["orders"][0]["status"] == "delayed"

    record = _get_call_record(test_session_factory, body["call_id"])
    assert record is not None
    assert record.customer_id == "CUST-101"
    assert record.verification_status == "verified"


def test_scenario_2_international_uk_format_multiple_orders(client):
    response = client.post(ENDPOINT, json={"incoming_phone": "+44 7700 900102"})
    assert response.status_code == 200

    body = response.json()
    assert body["verification_status"] == "verified"
    assert body["transfer_required"] is False
    assert body["customer"]["customer_id"] == "CUST-102"

    order_ids = {order["order_id"] for order in body["orders"]}
    assert order_ids == {"ORD-5002", "ORD-5003"}


def test_scenario_3_international_0044_no_orders(client):
    response = client.post(ENDPOINT, json={"incoming_phone": "00447700900103"})
    assert response.status_code == 200

    body = response.json()
    assert body["verification_status"] == "verified"
    assert body["transfer_required"] is False
    assert body["customer"]["customer_id"] == "CUST-103"
    assert body["orders"] == []


def test_scenario_4_unmatched_valid_looking_number(client, test_session_factory):
    response = client.post(ENDPOINT, json={"incoming_phone": "+447700900199"})
    assert response.status_code == 200

    body = response.json()
    assert body["verification_status"] == "unmatched"
    assert body["transfer_required"] is True
    assert body["customer"] is None
    assert body["orders"] == []

    record = _get_call_record(test_session_factory, body["call_id"])
    assert record is not None
    assert record.customer_id is None


def test_scenario_5_hidden_number(client):
    for value in ("withheld", "private", "unknown"):
        response = client.post(ENDPOINT, json={"incoming_phone": value})
        assert response.status_code == 200

        body = response.json()
        assert body["verification_status"] == "unavailable"
        assert body["transfer_required"] is True
        assert body["customer"] is None
        assert body["orders"] == []


def test_scenario_6_blank_value(client):
    for value in ("", "   "):
        response = client.post(ENDPOINT, json={"incoming_phone": value})
        assert response.status_code == 200

        body = response.json()
        assert body["verification_status"] == "unavailable"
        assert body["transfer_required"] is True
        assert body["customer"] is None
        assert body["orders"] == []


def test_scenario_7_invalid_value(client):
    response = client.post(ENDPOINT, json={"incoming_phone": "abc123"})
    assert response.status_code == 200

    body = response.json()
    assert body["verification_status"] == "invalid"
    assert body["transfer_required"] is True
    assert body["customer"] is None
    assert body["orders"] == []


def test_scenario_8_formatting_variations_resolve_to_same_customer(client):
    variations = [
        "07700900101",
        "07700 900101",
        "07700-900101",
        "(07700) 900101",
        "+447700900101",
        "+44 7700 900101",
        "00447700900101",
    ]

    for value in variations:
        response = client.post(ENDPOINT, json={"incoming_phone": value})
        assert response.status_code == 200

        body = response.json()
        assert body["verification_status"] == "verified"
        assert body["customer"]["customer_id"] == "CUST-101"


def test_scenario_9_cross_customer_protection(client):
    response = client.post(ENDPOINT, json={"incoming_phone": "+447700900101"})
    assert response.status_code == 200

    body = response.json()
    order_ids = {order["order_id"] for order in body["orders"]}
    assert "ORD-5002" not in order_ids
    assert "ORD-5003" not in order_ids


def test_scenario_10_health_endpoint_still_works(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
