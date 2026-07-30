Caller Verification API - Technical Note

Document status: Draft, Phase 1 MVP implementation note (not a business-requirements document).

1. Endpoint

POST /api/v1/calls/start

Always returns HTTP 200. Unmatched, unavailable and invalid verification outcomes are expected business results, not server errors, so they are carried in the response body rather than as HTTP error codes. This keeps the response shape identical across every outcome for a future frontend.

2. Accepted Input

Request body:

  { "incoming_phone": "07700 900101" }

incoming_phone is optional and may be missing, null, blank, a hidden-caller value ("withheld", "private", "unknown"), or any string.

3. Normalisation Rule (UK MVP only)

Supported representations of the same UK number:

  +447700900101
  +44 7700 900101
  0044 7700 900101
  07700 900101
  07700-900101
  (07700) 900101

Rule: spaces, hyphens and parentheses are removed, then the prefix (+44, 0044, or a single leading 0) is replaced with +44. The remaining digits must be exactly 10 digits and must not start with 0. Anything else is rejected as invalid. This is deliberately limited to the agreed UK MVP rule, not a general phone-number library.

4. Verification Statuses

- verified: exactly one active customer matches the normalised number.
- unmatched: the number normalises correctly but no active customer matches it.
- unavailable: the number is missing, blank, or a recognised hidden-caller value.
- invalid: the value cannot be interpreted as a supported UK number.

5. Transfer Behaviour

transfer_required is false only when verification_status is "verified". It is true for unmatched, unavailable and invalid outcomes.

6. Response Structure

Verified:

  {
    "call_id": "CALL-...",
    "verification_status": "verified",
    "transfer_required": false,
    "customer": { "customer_id": "CUST-101", "full_name": "Test Customer One" },
    "orders": [ ... orders belonging only to that customer ... ]
  }

Unmatched / unavailable / invalid:

  {
    "call_id": "CALL-...",
    "verification_status": "unmatched",
    "transfer_required": true,
    "customer": null,
    "orders": []
  }

A CallRecord is created for every attempt, including failed ones. customer_id on the CallRecord is only set when verification_status is "verified".

7. Known MVP Limitations

- One registered phone number maps to exactly one active customer. This is a Phase 1 simplification, not a real identity-verification mechanism.
- There is no OTP, PIN or other second-factor verification. A matching phone number alone is treated as sufficient for Phase 1, per business rule RULE-002 in docs/01-business-requirements.md.
- Only the UK number formats listed above are supported; no other country codes are handled.

8. Evidence Required Before This Feature Can Be Marked Complete

- All automated tests in backend/tests/test_phone_normalisation.py and backend/tests/test_call_start.py passing via `.venv\Scripts\python.exe -m pytest`.
- Manual confirmation that GET /health still returns {"status": "healthy"}.
- Confirmation that backend/retail_voice.db remains untracked/excluded from Git.
- Business Analyst review of the four verification statuses and transfer behaviour against docs/01-business-requirements.md (BR-002, BR-003, RULE-001 to RULE-003).
