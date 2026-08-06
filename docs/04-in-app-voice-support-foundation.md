In-App Voice Support Foundation - Technical Note

Document status: Draft, Phase 1 MVP implementation note (not a business-requirements document).

1. Updated Product Direction

The product is no longer framed primarily as a telephone queue assistant. The main product is an AI Voice Support button embedded inside an existing, already-authenticated e-commerce application. The customer never dials a number -- they tap a button inside an app they are already logged into.

The telephone caller-verification journey (docs/02) and the pending support-case journey (docs/03) remain implemented and tested, but they are no longer the primary customer journey this product is being built around.

2. One-Click Voice Journey (this task's scope)

  Customer taps "AI Voice Support"
  -> frontend starts a voice-support session for the authenticated customer
  -> panel shows the customer's first name and recent orders
  -> customer taps "Start speaking"
  -> browser requests microphone permission
  -> recording begins, with a visible indicator and timer
  -> customer taps "Stop"
  -> the recording is uploaded
  -> the backend transcribes it
  -> the transcript is shown in the panel

Nothing past the transcript is implemented yet -- see section 12 for what deliberately stops here.

3. Authentication Assumption and Local Demo-Auth Limitation

A real retailer application already has its own authentication and session handling. This repository does not, so a development-only adapter simulates it:

  backend/app/services/demo_auth.py

  Authorization: Bearer demo-cust-101   -> CUST-101
  Authorization: Bearer demo-cust-102   -> CUST-102
  Authorization: Bearer demo-cust-103   -> CUST-103

THIS IS NOT PRODUCTION AUTHENTICATION. It is a fixed, fictional, local-only token map. A future retailer integration replaces this entire module with the retailer's real authentication/session provider -- nothing else in the codebase needs to know how demo tokens are structured, because customer identity is only ever obtained through this one dependency (Depends(get_authenticated_customer)), never from a request body.

Behaviour:

  Missing Authorization header      -> 401
  Invalid/unrecognised demo token   -> 401
  Token maps to an inactive customer -> 403 (same generic message as "not found", to avoid revealing account state)

4. Voice-Session Endpoints

POST /api/v1/voice-support/sessions
  Requires: Authorization: Bearer <demo-token>
  Body: none (no customer_id is ever accepted)
  201 response:
    {
      "session_id": "VOICE-...",
      "status": "started",
      "customer": { "customer_id": "CUST-101", "full_name": "Test Customer One" },
      "recent_orders": [ { "order_id": "ORD-5001", "status": "delayed", "total_amount": "24.99",
                            "currency_code": "GBP", "items": [ { "product_name": "Wireless Headphones", "quantity": 1 } ] } ],
      "created_at": "..."
    }
  recent_orders only ever contains the authenticated customer's own orders, newest first, capped at 5.

POST /api/v1/voice-support/sessions/{session_id}/audio
  Requires: Authorization header, multipart/form-data with an "audio" field.
  A session may only be used by the customer who created it -- an unknown session_id and a
  session belonging to a different customer both return the same generic 404, so a caller can
  never distinguish "doesn't exist" from "isn't yours".
  200 response:
    {
      "session_id": "VOICE-...",
      "status": "transcribed",
      "transcript": "My wireless headphones have not arrived and the order shows delayed.",
      "detected_language": "en",
      "customer": { "customer_id": "CUST-102", "full_name": "Test Customer Two" }
    }

Neither endpoint creates a SupportCase, modifies an Order, or creates a CallRecord. See section 12.

5. Supported Audio Types and Maximum File Size

  audio/webm, audio/wav, audio/x-wav, audio/mpeg, audio/mp4, audio/ogg
  Maximum: 10 MB

  400  Empty audio
  404  Unknown or non-owned session
  413  Audio exceeds the 10 MB limit
  415  Unsupported audio type
  422  Malformed request (e.g. the "audio" field is missing entirely -- FastAPI's own validation)
  503  Speech-to-text service unavailable (never a raw traceback)

Content-Type is client-supplied, so this is a filter, not proof the bytes are valid audio -- true content sniffing is out of scope for this foundation (see Known Limitations).

6. Temporary-File Handling

Uploaded audio is streamed to a system-temp file in bounded 1 MB chunks (so a 10 MB+ upload is rejected mid-stream rather than fully buffered in memory first). The filename is always backend-generated (tempfile.mkstemp with a fixed prefix); the browser-supplied filename is stored only as audit metadata on VoiceSupportSession.original_filename and is never used to build a path. The temp file is deleted in a finally block after every attempt, success or failure. No raw audio is ever written to the database or committed to Git.

7. Speech-Provider Architecture

  backend/app/services/speech_to_text/base.py                 SpeechToTextProvider interface, TranscriptionResult
  backend/app/services/speech_to_text/mock_provider.py         canned transcript, used by all automated tests
  backend/app/services/speech_to_text/faster_whisper_provider.py  local CPU provider (see below)
  backend/app/services/speech_to_text/factory.py               reads Settings.stt_provider, used as a FastAPI dependency

Configuration (backend/app/config.py, environment-driven):

  STT_PROVIDER=mock              (default; what automated tests use)
  STT_MODEL_SIZE=tiny.en
  STT_DEVICE=cpu
  STT_COMPUTE_TYPE=int8

To use real local transcription, set STT_PROVIDER=faster_whisper.

8. faster-whisper: Status in This Task

faster-whisper was NOT installed or pip-added in this task. The provider file was written against its expected API (lazy-imported so importing the module never requires the package), but the package itself was deliberately not added to requirements.txt yet. Reasoning:

  - It was not already installed (checked via `pip list` before starting).
  - It pulls in ctranslate2 (native binary wheels) plus tokenizers and related dependencies --
    a meaningfully larger deployment footprint than anything else in this repository, which this
    task's rules require explaining before adding.
  - The tiny.en model itself downloads on first real use (roughly tens of MB), which is a network
    dependency this task's rules also require flagging before it happens silently.
  - The task's own acceptance criteria explicitly allow demonstrating the complete flow with the
    mock provider when faster-whisper cannot be verified live, rather than installing a large
    dependency speculatively.

To enable it yourself: `pip install faster-whisper`, then set `STT_PROVIDER=faster_whisper` (tiny.en/cpu/int8 are reasonable first defaults). The first transcription call will download the tiny.en model automatically. This has not been tested in this environment -- do not assume it works until it has actually been run once.

9. Frontend Environment Variables

  frontend/.env.example:
    VITE_API_BASE_URL=http://127.0.0.1:8000
    VITE_DEMO_AUTH_TOKEN=demo-cust-101

  Copy to frontend/.env (git-ignored) and edit locally. Switch customer accounts by changing
  VITE_DEMO_AUTH_TOKEN to demo-cust-101 / demo-cust-102 / demo-cust-103 and restarting the dev
  server -- this lets you exercise a one-order customer, a multi-order customer, and a
  no-orders customer without touching code.

10. Microphone Permission Behaviour

The VoiceSupportButton / VoiceSupportPanel / useVoiceRecorder implementation:
  - Detects MediaRecorder + getUserMedia support before attempting to record; shows a controlled
    "this browser does not support in-browser audio recording" message otherwise.
  - Requests audio-only access (no video).
  - Stops every MediaStreamTrack when recording ends, when the panel unmounts, and on any
    recorder error -- the microphone indicator in the browser chrome should never stay lit after
    the panel closes.
  - Shows a controlled "Microphone permission was denied" message if the browser permission
    prompt is rejected, with a Try again action.

11. Privacy Rules Followed

  - No raw audio is ever persisted to the database or the repository.
  - Only fictional UK seed customers/orders are used anywhere in code, tests, or this document.
  - The request body for both voice-support endpoints can never carry a customer_id -- identity
    only ever comes from the Authorization header via get_authenticated_customer.
  - A session lookup failure (unknown or wrong-owner) returns an identical generic 404 either way.
  - CORS is a narrow, explicit allowlist (see below), not "*", because these endpoints read an
    Authorization header.

12. CORS Configuration

  backend/app/config.py: CORS_ALLOWED_ORIGINS (comma-separated), default:
    http://localhost:5173,http://127.0.0.1:5173

  Wired in backend/app/main.py via CORSMiddleware with allow_credentials=True. Production
  origins are NOT configured here and must be set explicitly via the CORS_ALLOWED_ORIGINS
  environment variable before any non-local deployment -- the default only covers the local
  Vite dev server.

13. Test Evidence

Backend: `.venv\Scripts\python.exe -m pytest backend/tests -v`
  62 collected, 62 passed, 0 failed, 1 warning, 804.71s
  (1 warning is the pre-existing httpx/starlette.testclient deprecation notice, unrelated to
  this task.) This includes all 46 previously-existing caller-verification/support-case tests
  plus 16 new voice-support tests in backend/tests/test_voice_support.py.

Frontend: `npm test` (vitest run)
  3 test files, 13 tests, 13 passed, 0 failed.

Frontend build: `npm run build` (tsc -b && vite build)
  Succeeded: dist/index.html, dist/assets/index-*.css (5.13 kB), dist/assets/index-*.js (198.40 kB, 62.47 kB gzipped).

Live smoke test (see final report for full detail): backend endpoints exercised directly over
HTTP for demo-cust-101/102/103 (session start + audio upload), plus a real CORS preflight
request from the http://localhost:5173 origin, plus the Vite dev server confirmed serving the
built app. Clicking the button and granting microphone permission in an actual browser was NOT
performed -- this environment has no browser or microphone available to drive one. The
automated frontend tests substitute for that by exercising the same code paths against mocked
MediaRecorder/getUserMedia implementations.

14. Known Limitations

  - Demo authentication is not production authentication (see section 3).
  - Intent understanding is not implemented -- the transcript is just displayed, not interpreted.
  - Complaint submission from the transcript is not implemented.
  - Return submission from the transcript is not implemented.
  - No conversational AI model is connected yet.
  - No text-to-speech response yet -- the assistant does not speak back.
  - No streaming transcription yet -- audio is uploaded only after the customer taps Stop.
  - No production monitoring or rate limiting on either voice-support endpoint.
  - Audio Content-Type is trusted from the client, not sniffed from the actual bytes.
  - faster-whisper is not installed/verified in this environment (see section 8).
  - The panel is not a fully focus-trapped modal; keyboard users can still reach page content
    behind it while it is open.

15. Next Development Stage

  - Feed the transcript into intent classification (still bound by the Phase 1 authority limits
    already documented in docs/03).
  - Let a classified intent pre-fill a SupportCase creation request for human confirmation.
  - Investigate streaming transcription for lower perceived latency.
  - Decide, with Business Analyst input, whether/how to add retry idempotency across the voice
    and support-case endpoints together.
