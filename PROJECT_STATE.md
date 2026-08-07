# Project State

Last updated: 6 August 2026

## Repository baseline

- Repository: `singhsatyam85-cloud/retail-voice-customer-service-assistant`
- Branch: `main`
- Latest verified commit: `ecde417`
- Commit: `feat(voice-support): add voice support and request size limits`
- Local branch and `origin/main` were synchronized after the push.
- Working tree was clean after the push.

## Latest verified test result

- Backend: `135 passed, 1 warning` (`.venv\Scripts\python -m pytest backend\tests\`)
- Frontend: `30 passed` (`npm test -- --run`)
- Frontend Build: `passed` (`npm run build`)
- Local Ollama: Verified with installed `llama3.2:3b` model (intent classification and prompt optimization confirmed).

## Existing product direction

The primary journey is the authenticated in-app **AI Voice Support** button.

The older simulated telephone caller-verification flow remains implemented and tested, but it is not the main journey for the next development stage.

## Verified implemented foundation

Based on the current repository documents and commit history:

- FastAPI backend and database foundation
- Caller verification and linked-order retrieval
- Pending support-case API for verified calls
- Demo authentication for the local in-app journey
- Voice-support session creation
- Recent-order display for the authenticated customer
- Browser recording controls
- Audio upload with a 10 MB limit
- Mock speech-to-text provider
- Local faster-whisper provider adapter
- Transcript returned and displayed
- Request-size middleware
- React WebGL circular DNA voice animation (VoiceOrbDNA)
- Backend automated tests

## Confirmed current gaps

The in-app voice journey now supports a premium React WebGL voice animation, deterministic classification, and case submission with idempotency key.

Not yet confirmed as implemented:

- Spoken assistant response
- Manual browser microphone verification on this machine

**Voice-to-case integration gap findings:**
- Frontend transcript is received in `VoiceSupportPanel.tsx`.
- Backend session audio endpoint is `POST /api/v1/voice-support/sessions/{session_id}/audio`.
- Existing case endpoint `POST /api/v1/calls/{call_id}/cases` uses `CreateCaseRequest` but strictly requires a `call_id`.
- The smallest connection path requires updating `SupportCase` to accept an optional `session_id` alongside `call_id`, adding a `create_voice_support_case` service function, and a new `POST /sessions/{session_id}/cases` route.

## Current phase

Phase 0 MVP Completed Successfully.

## Current task

None.

## Current blocker

None. D005 and D006 have been approved, recorded, and verified.

## Completion standard

The two-day MVP is complete when:

1. The local backend and frontend start.
2. An authenticated demo customer opens voice support.
3. The customer records or submits a supported audio request.
4. The system produces a transcript.
5. The customer can confirm the complaint/request details.
6. The system creates one valid pending case using the existing authority rules.
7. The case reference, pending status and summary are displayed.
8. Error and human-transfer paths are clear.
9. Relevant tests and the final regression suite pass.
10. Setup instructions match the observed commands.
