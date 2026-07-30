Support Case API - Technical Note

Document status: Draft, Phase 1 MVP implementation note (not a business-requirements document).

1. Endpoint

POST /api/v1/calls/{call_id}/cases

call_id is the trusted identifier returned by a prior POST /api/v1/calls/start call. See docs/02-caller-verification-api.md for that endpoint.

2. Request Schema

  {
    "category": "delayed_delivery",
    "order_id": "ORD-5001",
    "summary": "My order was due yesterday and has not arrived."
  }

- category: required, one of the allowed values below.
- order_id: required for order-specific categories, optional for human_agent_request.
- summary: required text, trimmed, 10-1000 meaningful characters.

Unexpected fields (for example status, requires_human_review, customer_id, case_id, created_at, approved, refund_amount, cancellation_status) are rejected outright with HTTP 422 rather than silently ignored. This stops a caller from smuggling authority-changing values into the request.

3. Allowed Categories

  order_status
  delayed_delivery
  missing_delivery
  damaged_product
  return_request
  cancellation_request
  wrong_item
  human_agent_request

An unrecognised category value is rejected with HTTP 422. No other category values may be created without an approved requirement change.

4. Order Requirement by Category

These categories require order_id:

  order_status, delayed_delivery, missing_delivery, damaged_product,
  return_request, cancellation_request, wrong_item

human_agent_request may be created without an order_id, or with one when the request concerns a specific order. Submitting an order-specific category without order_id returns HTTP 422 and no SupportCase is created.

5. Verified-Call Rule

A support case may only be created when the referenced CallRecord has:

  verification_status = "verified"
  customer_id is not null
  transfer_required = false

The customer identity always comes from the persisted CallRecord.customer_id, never from the request body. Unknown call_id returns HTTP 404. An existing call with verification_status of unmatched, unavailable or invalid returns HTTP 409 and no case is created; no customer information is exposed in that response.

6. Order-Ownership Rule

When order_id is supplied, the backend confirms ownership in a single query condition:

  order.order_id = requested order_id
  AND order.customer_id = verified_call.customer_id

An order_id is never looked up on its own, and a frontend-supplied customer_id is never trusted. When the order does not belong to the verified caller, the API returns a generic HTTP 404 with the message "Order not found for this verified call." — it does not reveal whether the order exists for a different customer, and no SupportCase is created.

7. Response Schema

HTTP 201 Created:

  {
    "case_id": "CASE-...",
    "call_id": "CALL-...",
    "customer_id": "CUST-101",
    "order_id": "ORD-5001",
    "category": "delayed_delivery",
    "status": "pending",
    "summary": "My order was due yesterday and has not arrived.",
    "requires_human_review": true,
    "created_at": "..."
  }

case_id is generated server-side as CASE-<UUID>; it cannot be supplied by the client.

8. HTTP Status Behaviour

  201  Support case created.
  404  Unknown call_id, or order_id does not belong to the verified caller.
  409  Call exists but was not a successful verification (unmatched, unavailable or invalid).
  422  Request validation failure: unknown category, missing order_id for an order-specific category, blank/too-short/too-long summary, or an unexpected field in the request body.

9. Phase 1 Authority Limitation

Every case is created with status = "pending" and requires_human_review = true, and the client cannot override either value. Creating a case is only ever a record of what the customer asked for. It never approves a return, rejects a return, approves a cancellation, cancels an order, issues a refund, or updates finance or inventory records — cancellation_request and return_request cases leave the underlying order unchanged. All such decisions remain with an authorised human agent.

10. Examples

Verified delayed-delivery case (matches section 2).

Human-agent request without an order:

  { "category": "human_agent_request", "summary": "I need to speak with a customer service adviser." }

11. Evidence Required Before This Feature Can Be Marked Complete

- All automated tests in backend/tests/test_case_creation.py passing via `.venv\Scripts\python.exe -m pytest`, alongside the existing caller-verification suite.
- Live smoke test through the running server: a verified call followed by a successful case creation, and a rejected cross-customer order attempt.
- Confirmation that backend/retail_voice.db remains untracked/excluded from Git.
- Business Analyst review of the category list, the order-requirement split, and the HTTP status choices against docs/01-business-requirements.md (BR-014, BR-017, BR-018, RULE-009 to RULE-013).

12. Known Limitations

- API retry idempotency has not been implemented. If a client resubmits the same successful request (for example after a network timeout), a separate SupportCase is created for each attempt. No idempotency key or deduplication design has been added, and none should be implemented without Business Analyst approval, since it affects how duplicate customer contacts are represented to human reviewers.
- Ownership checks assume a single customer per order (matching the existing data model); no support for shared or business accounts exists in Phase 1.
- No rate limiting or throttling is applied to repeated case-creation attempts.
