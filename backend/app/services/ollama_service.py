"""Local Ollama LLM conversation service.

Provides local AI understanding and structured JSON response generation using
an Ollama model running locally (defaulting to http://localhost:11434).

No OpenAI, Gemini, Claude, or external paid APIs are used.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Optional

from backend.app.config import Settings
from backend.app.models import Customer, Order
from backend.app.schemas import CaseCategory, OllamaStructuredResponse
from backend.app.services.classification import classify_transcript, IntentCategory


class OllamaServiceError(Exception):
    """Base exception for Ollama conversation service errors."""


class OllamaUnavailableError(OllamaServiceError):
    """Ollama endpoint is not reachable or service is down."""


class OllamaModelMissingError(OllamaServiceError):
    """Configured model is not installed in the local Ollama instance."""


class OllamaInvalidResponseError(OllamaServiceError):
    """Ollama returned an unparseable or invalid JSON schema."""


SUPPORTED_INTENT_NAMES = [category.value for category in CaseCategory] + ["needs_clarification"]


def check_ollama_status(base_url: str, model_name: str, timeout: float = 5.0) -> list[str]:
    """Check if Ollama server is reachable and verify if model_name is installed.
    
    Raises OllamaUnavailableError if server is unreachable.
    Raises OllamaModelMissingError if no models or requested model is missing.
    Returns list of available model names.
    """
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise OllamaUnavailableError(f"Ollama tags endpoint returned status {resp.status}.")
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
            raw_names = [m.get("name", "") for m in data.get("models", [])]
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OllamaUnavailableError(f"Ollama server is unavailable at {base_url}.") from exc
    except Exception as exc:
        raise OllamaUnavailableError(f"Failed to parse Ollama status response: {exc}") from exc

    if not raw_names:
        raise OllamaModelMissingError("No models are currently installed in Ollama.")

    # Check if model_name (or model_name:tag) is available
    model_base = model_name.split(":")[0]
    if model_name not in raw_names and model_base not in models:
        raise OllamaModelMissingError(
            f"Configured Ollama model '{model_name}' is not installed in Ollama. "
            f"Available models: {', '.join(raw_names)}"
        )

    return raw_names


def build_system_prompt(customer: Customer, recent_orders: list[Order]) -> str:
    """Build a grounded system prompt containing verified customer and order facts."""
    order_lines = []
    for order in recent_orders:
        items_str = ", ".join(f"{it.quantity}x {it.product_name}" for it in order.items)
        extras = ""
        if order.delivered_at:
            extras += f", delivered={order.delivered_at}"
        if order.expected_delivery_at:
            extras += f", expected={order.expected_delivery_at}"
        order_lines.append(
            f"- Order ID: {order.order_id}, Status: {order.status}, Total: {order.currency_code} {order.total_amount:.2f}, Items: [{items_str}]{extras}"
        )

    orders_block = "\n".join(order_lines) if order_lines else "No active orders found."

    return (
        "You are an AI retail customer service assistant. You must assist the customer below.\n\n"
        "STRICT FACT GROUNDING RULES:\n"
        "1. Never invent or hallucinate order IDs, delivery dates, refund amounts, or customer info.\n"
        "2. All order facts must come ONLY from the Ground Truth Facts list below.\n"
        "3. You cannot execute returns, refunds, or cancellations directly. You can only create pending cases for human review.\n"
        "4. Classify intent strictly: use 'order_status' when customer asks where an order/parcel/package is or tracks status. Use 'human_agent_request' ONLY when customer asks for a human person or representative.\n\n"
        f"Verified Customer: {customer.full_name} (ID: {customer.customer_id})\n"
        f"Ground Truth Facts (Recent Orders):\n{orders_block}\n\n"
        "REQUIRED OUTPUT FORMAT:\n"
        "Respond ONLY with a single JSON object matching this schema:\n"
        "{\n"
        '  "intent": "<order_status|delayed_delivery|missing_delivery|damaged_product|return_request|cancellation_request|wrong_item|human_agent_request|needs_clarification>",\n'
        '  "reply": "<helpful assistant response to customer>",\n'
        '  "requires_order": <true|false>,\n'
        '  "needs_clarification": <true|false>,\n'
        '  "create_case": <true|false>\n'
        "}\n"
    )


def generate_ollama_response(
    customer: Customer,
    recent_orders: list[Order],
    user_transcript: str,
    conversation_history: list[dict[str, str]],
    settings: Settings,
) -> OllamaStructuredResponse:
    """Generate a structured JSON response from Ollama.
    
    Raises OllamaServiceError subclasses if Ollama is down, model missing, or JSON invalid.
    """
    # Skip separate check_ollama_status() -- let the chat request itself
    # reveal connection or model errors, saving one network round-trip.

    system_prompt = build_system_prompt(customer, recent_orders)
    
    messages = [{"role": "system", "content": system_prompt}]
    for turn in conversation_history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_transcript})

    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "format": "json",
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0,
            "num_ctx": 2048,
            "num_predict": 256,
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=settings.ollama_timeout) as resp:
            if resp.status != 200:
                raise OllamaUnavailableError(f"Ollama chat endpoint returned HTTP status {resp.status}.")
            res_body = json.loads(resp.read().decode("utf-8"))
            content = res_body.get("message", {}).get("content", "")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OllamaUnavailableError(f"Failed to communicate with Ollama at {url}.") from exc

    try:
        parsed = json.loads(content)
        intent = parsed.get("intent", "needs_clarification")
        if intent not in SUPPORTED_INTENT_NAMES:
            intent = "needs_clarification"

        return OllamaStructuredResponse(
            intent=intent,
            reply=str(parsed.get("reply", "I can help you with your request.")),
            requires_order=bool(parsed.get("requires_order", False)),
            needs_clarification=bool(parsed.get("needs_clarification", False)),
            create_case=bool(parsed.get("create_case", False)),
        )
    except Exception as exc:
        raise OllamaInvalidResponseError(f"Ollama returned invalid JSON schema: {content!r}") from exc


def generate_fallback_response(
    customer: Customer,
    recent_orders: list[Order],
    user_transcript: str,
    conversation_history: list[dict[str, str]],
) -> OllamaStructuredResponse:
    """Deterministic fallback response generator when Ollama is offline or unavailable.
    
    Uses deterministic keyword classification and factual order information.
    """
    category = classify_transcript(user_transcript)

    if category == IntentCategory.HUMAN_AGENT_REQUEST:
        return OllamaStructuredResponse(
            intent="human_agent_request",
            reply="I understand you want to speak with a human agent. I can submit a support request for a representative to contact you.",
            requires_order=False,
            needs_clarification=False,
            create_case=True,
        )

    if category == IntentCategory.NEEDS_CLARIFICATION or not category:
        return OllamaStructuredResponse(
            intent="needs_clarification",
            reply="I'm not sure I understood your request. Could you please provide more details or let me know if you want to speak with an agent?",
            requires_order=False,
            needs_clarification=True,
            create_case=False,
        )

    # Order-specific category
    if not recent_orders:
        return OllamaStructuredResponse(
            intent=category.value,
            reply=f"I understand your request regarding {category.value.replace('_', ' ')}, but I couldn't find any recent orders linked to your account.",
            requires_order=True,
            needs_clarification=True,
            create_case=False,
        )

    if len(recent_orders) == 1:
        ord_obj = recent_orders[0]
        return OllamaStructuredResponse(
            intent=category.value,
            reply=f"I found your order {ord_obj.order_id} (Status: {ord_obj.status}). Would you like me to prepare a support case for this request?",
            requires_order=True,
            needs_clarification=False,
            create_case=False,
        )

    # Multiple orders
    order_ids = ", ".join(o.order_id for o in recent_orders)
    return OllamaStructuredResponse(
        intent=category.value,
        reply=f"I found multiple orders ({order_ids}). Please select which order your request regarding {category.value.replace('_', ' ')} is about.",
        requires_order=True,
        needs_clarification=False,
        create_case=False,
    )
