"""Tests for Ollama conversation service."""

from unittest.mock import MagicMock, patch
import json
import pytest

from backend.app.config import Settings
from backend.app.models import Customer, Order, OrderItem
from backend.app.services.ollama_service import (
    OllamaInvalidResponseError,
    OllamaModelMissingError,
    OllamaUnavailableError,
    build_system_prompt,
    check_ollama_status,
    generate_fallback_response,
    generate_ollama_response,
)


def _make_resp(status_code: int, data: dict):
    resp = MagicMock()
    resp.status = status_code
    resp.read.return_value = json.dumps(data).encode("utf-8")
    resp.__enter__.return_value = resp
    return resp


@pytest.fixture
def mock_customer():
    cust = MagicMock(spec=Customer)
    cust.customer_id = "CUST-101"
    cust.full_name = "Test Customer"
    return cust


@pytest.fixture
def mock_orders():
    order = MagicMock(spec=Order)
    order.order_id = "ORD-5001"
    order.status = "delayed"
    order.total_amount = 129.99
    order.currency_code = "GBP"
    order.delivered_at = None
    order.expected_delivery_at = None

    item = MagicMock(spec=OrderItem)
    item.quantity = 1
    item.product_name = "Wireless Headphones"
    order.items = [item]

    return [order]


def test_build_system_prompt(mock_customer, mock_orders):
    prompt = build_system_prompt(mock_customer, mock_orders)
    assert "Test Customer" in prompt
    assert "CUST-101" in prompt
    assert "ORD-5001" in prompt
    assert "1x Wireless Headphones" in prompt
    assert "Never invent or hallucinate order IDs" in prompt


def test_check_ollama_status_success():
    resp = _make_resp(200, {"models": [{"name": "llama3.2:3b"}]})
    with patch("urllib.request.urlopen", return_value=resp):
        models = check_ollama_status("http://localhost:11434", "llama3.2:3b")
        assert "llama3.2:3b" in models


def test_check_ollama_status_unavailable():
    with patch("urllib.request.urlopen", side_effect=OSError("Connection refused")):
        with pytest.raises(OllamaUnavailableError):
            check_ollama_status("http://localhost:11434", "llama3.2:3b")


def test_check_ollama_status_model_missing():
    resp = _make_resp(200, {"models": [{"name": "mistral:latest"}]})
    with patch("urllib.request.urlopen", return_value=resp):
        with pytest.raises(OllamaModelMissingError):
            check_ollama_status("http://localhost:11434", "nonexistent-model")


def test_generate_ollama_response_success(mock_customer, mock_orders):
    tags_resp = _make_resp(200, {"models": [{"name": "llama3.2:3b"}]})
    chat_payload = {
        "message": {
            "content": json.dumps({
                "intent": "delayed_delivery",
                "reply": "I see your order ORD-5001 is delayed. Would you like me to open a support case?",
                "requires_order": True,
                "needs_clarification": False,
                "create_case": False,
            })
        }
    }
    chat_resp = _make_resp(200, chat_payload)

    def side_effect(req, timeout=None):
        if "tags" in req.full_url:
            return tags_resp
        return chat_resp

    settings = Settings(ollama_base_url="http://localhost:11434", ollama_model="llama3.2:3b")

    with patch("urllib.request.urlopen", side_effect=side_effect):
        res = generate_ollama_response(
            customer=mock_customer,
            recent_orders=mock_orders,
            user_transcript="Where is my order?",
            conversation_history=[],
            settings=settings,
        )
        assert res.intent == "delayed_delivery"
        assert "ORD-5001" in res.reply
        assert res.requires_order is True


def test_generate_ollama_response_invalid_json(mock_customer, mock_orders):
    tags_resp = _make_resp(200, {"models": [{"name": "llama3.2:3b"}]})
    chat_resp = _make_resp(200, {"message": {"content": "Not a JSON object"}})

    def side_effect(req, timeout=None):
        if "tags" in req.full_url:
            return tags_resp
        return chat_resp

    settings = Settings(ollama_base_url="http://localhost:11434", ollama_model="llama3.2:3b")

    with patch("urllib.request.urlopen", side_effect=side_effect):
        with pytest.raises(OllamaInvalidResponseError):
            generate_ollama_response(
                customer=mock_customer,
                recent_orders=mock_orders,
                user_transcript="Where is my order?",
                conversation_history=[],
                settings=settings,
            )


def test_generate_fallback_response_human_agent(mock_customer, mock_orders):
    res = generate_fallback_response(
        customer=mock_customer,
        recent_orders=mock_orders,
        user_transcript="I want to speak with a human agent",
        conversation_history=[],
    )
    assert res.intent == "human_agent_request"
    assert res.requires_order is False
    assert res.create_case is True


def test_generate_fallback_response_single_order(mock_customer, mock_orders):
    res = generate_fallback_response(
        customer=mock_customer,
        recent_orders=mock_orders,
        user_transcript="My order is delayed",
        conversation_history=[],
    )
    assert res.intent == "delayed_delivery"
    assert "ORD-5001" in res.reply
    assert res.requires_order is True
