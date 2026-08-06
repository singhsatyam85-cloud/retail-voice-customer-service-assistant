# Decisions

Only record decisions that affect implementation, scope or test expectations.

## D001: Primary product journey

Status: `APPROVED`

Decision:

The authenticated in-app AI Voice Support button is the primary product journey.

The simulated telephone caller-verification journey remains implemented but is secondary.

Source:

`docs/04-in-app-voice-support-foundation.md`

---

## D002: Sensitive decisions

Status: `APPROVED`

Decision:

The system may capture requests and create pending cases. It must not approve refunds, returns or cancellations. Those decisions remain with an authorised human.

Sources:

- `docs/01-business-requirements.md`
- `docs/03-support-case-api.md`

---

## D003: Voice foundation boundary

Status: `APPROVED`

Decision:

The existing voice foundation ends after transcription. Intent understanding and complaint submission from the transcript were not included in that completed stage.

Source:

`docs/04-in-app-voice-support-foundation.md`

---

## D004: Paid speech services

Status: `APPROVED`

Decision:

Do not require a paid speech service for the local MVP. The mock provider may support automated tests. A local provider may be used only when its dependency and model download are understood and approved.

Source:

`docs/04-in-app-voice-support-foundation.md`

---

## D005: Transcript classification method

Status: `APPROVED`

Decision:

Use a deterministic local transcript classifier for the two-day MVP.

Supported categories:
- order_status
- delayed_delivery
- missing_delivery
- damaged_product
- return_request
- cancellation_request
- wrong_item
- human_agent_request

Rules:
- Do not use a paid or external AI service.
- A direct human-agent request takes priority.
- Unknown input returns needs_clarification.
- Conflicting categories return needs_clarification.
- Do not infer or invent an order from transcript text.
- Order selection remains a separate customer-confirmed step.
- Keep the classifier as a small pure service with focused unit tests.

---

## D006: Retry and duplicate-case behaviour

Status: `APPROVED`

Decision:

Prevent accidental repeat case submission using an idempotency key.

- Generate one UUID when the frontend creates a confirmed case draft.
- Reuse the same key when retrying that submission.
- Store it as a unique backend value.
- Return the existing case when the same key is submitted again.
- Generate a new key for a genuinely new customer contact.
- Do not detect duplicates by comparing transcript text, category, order or time.

Architecture decision:

Do not create a fake CallRecord for the in-app voice journey. Keep the existing call-based case endpoint unchanged. Later, create a separate authenticated voice-session case route. A SupportCase may reference either call_id or voice_session_id, but not both. Customer identity must come from the authenticated VoiceSupportSession. Any database change must use a safe migration.
