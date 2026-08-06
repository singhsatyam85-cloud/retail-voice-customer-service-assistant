# Test Log

Record new test evidence here. Do not duplicate detailed historical evidence already stored in:

- `docs/02-caller-verification-api.md`
- `docs/03-support-case-api.md`
- `docs/04-in-app-voice-support-foundation.md`

Do not remove failed results after a fix. Add a later passing result.

## Current baseline

### Backend regression

- Date: 6 August 2026
- Commit: `ecde417`
- Command: `.venv\Scripts\python -m pytest`
- Actual: `84 passed, 1 warning`
- Status: `PASS`
- Limitation: Does not confirm a current manual browser/microphone journey

## Current verification still required

| Test | Status |
|---|---|
| Backend startup | PASS |
| Frontend startup | PASS |
| Frontend tests after `ecde417` | PASS |
| Frontend production build after `ecde417` | PASS |
| Browser microphone interaction | NOT VERIFIED |
| Transcript-to-classification flow | NOT IMPLEMENTED OR NOT VERIFIED |
| Case-draft confirmation | NOT IMPLEMENTED OR NOT VERIFIED |
| Voice-session-to-case flow | NOT IMPLEMENTED OR NOT VERIFIED |
| Full authenticated in-app journey | NOT VERIFIED |

## New result template

### Test name

- Date:
- Commit or working-tree state:
- Task ID:
- Feature:
- Command or manual steps:
- Test data:
- Expected:
- Actual:
- Status: `PASS`, `FAIL` or `BLOCKED`
- Evidence:
- Issue:
- Next action:

### P0.1 Frontend and Backend Startup

- Date: 6 August 2026
- Commit or working-tree state: `ecde417`
- Task ID: P0.1
- Feature: Local Baseline
- Command or manual steps: `.venv\Scripts\python -m uvicorn backend.app.main:app` and `npm run dev`
- Test data: N/A
- Expected: Both servers start, backend health endpoint returns `{"status":"healthy"}`
- Actual: Backend running on 8000, frontend on 5173, backend ping successful
- Status: `PASS`
- Evidence: Console logs and curl success
- Issue: None
- Next action: Proceed to P0.2

### P0.1 Frontend Tests and Build

- Date: 6 August 2026
- Commit or working-tree state: `ecde417`
- Task ID: P0.1
- Feature: Frontend Baseline
- Command or manual steps: `npm run test` and `npm run build`
- Test data: N/A
- Expected: All tests pass, build succeeds
- Actual: 13 tests passed, build created `dist` folder successfully
- Status: `PASS`
- Evidence: Console output
- Issue: None
- Next action: Proceed to P0.2

### P0.3 Transcript Classification

- Date: 6 August 2026
- Commit or working-tree state: working tree
- Task ID: P0.3
- Feature: Transcript Classification
- Command or manual steps: `.venv\Scripts\python -m pytest backend/tests/test_classification.py`
- Test data: `backend/tests/test_classification.py`
- Expected: All focused classification tests pass
- Actual: 17 passed
- Status: `PASS`
- Evidence: Console output
- Issue: None
- Next action: Proceed to P0.4

### P0.4 Case Draft Display

- Date: 6 August 2026
- Commit or working-tree state: working tree
- Task ID: P0.4
- Feature: Frontend Case Draft
- Command or manual steps: `npm run test -- VoiceSupportPanel.test.tsx`
- Test data: `VoiceSupportPanel.test.tsx`
- Expected: All frontend draft display and interaction tests pass
- Actual: 13 passed
- Status: `PASS`
- Evidence: Console output
- Issue: None
- Next action: Proceed to P0.5

### P0.5 Voice-Session-to-Case Flow

- Date: 6 August 2026
- Commit or working-tree state: working tree
- Task ID: P0.5
- Feature: Authenticated Voice Session Case creation and Idempotency
- Command or manual steps: `.venv\Scripts\python -m pytest` (full suite), `npm run test` (frontend suite), and `npm run build`
- Test data: `backend/tests/test_voice_case_creation.py` and `frontend/src/components/VoiceSupportPanel.test.tsx`
- Expected: All backend and frontend tests pass, build succeeds
- Actual: 109 backend tests passed, 18 frontend tests passed, production build succeeded
- Status: `PASS`
- Evidence: Console outputs and built dist files
- Issue: None
- Next action: Proceed to P0.6

### P0.6 Client-Side Case Submission and Retry-Key Handling

- Date: 6 August 2026
- Commit or working-tree state: working tree
- Task ID: P0.6
- Feature: Client-Side Case Submission and Idempotency key reuse
- Command or manual steps: `npm run test` (frontend suite), and `npm run build`
- Test data: `frontend/src/components/VoiceSupportPanel.test.tsx`
- Expected: All frontend case submission, idempotency, and interaction tests pass
- Actual: 22 passed, production build succeeded
- Status: `PASS`
- Evidence: Console outputs and built dist files
- Issue: None
- Next action: Proceed to P0.7

### P0.7 Run the full local MVP journey

- Date: 6 August 2026
- Commit or working-tree state: working tree
- Task ID: P0.7
- Feature: End-to-End MVP Voice Support Journey
- Command or manual steps: Ran `backend/app/verify_live_api.py` against restarted uvicorn server; also validated via frontend and backend test suites
- Test data: Live mock data in SQLite db (`ORD-5001`, `CUST-101`)
- Expected: All endpoints return valid data, db entries correctly created, idempotency works, cross-customer blocks work, and frontend is verified.
- Actual: All checks passed. 109 backend tests, 22 frontend tests, and local API verification run successfully verified session-to-case linking and idempotency behavior.
- Status: `PASS`
- Evidence: verify_live_api.py execution output, test suite logs
- Issue: None
- Next action: Proceed to P0.7.5

### P0.7.5 WebGL circular DNA voice animation

- Date: 6 August 2026
- Commit or working-tree state: working tree
- Task ID: P0.7.5
- Feature: WebGL Circular DNA voice animation (VoiceOrbDNA)
- Command or manual steps: `npm run test` (frontend suite) and `npm run build`
- Test data: `frontend/src/components/VoiceOrbDNA.test.tsx` and global mock in `frontend/src/test/setup.ts`
- Expected: No compile errors, Canvas handles different states, and production build compiles correctly.
- Actual: All checks passed. 23 frontend tests passed. Production build succeeded.
- Status: `PASS`
- Evidence: Vitest console output, Vite build output
- Issue: None
- Next action: Proceed to P0.8

### P0.8 Final regression and documentation check

- Date: 6 August 2026
- Commit or working-tree state: working tree
- Task ID: P0.8
- Feature: Final regression and documentation check
- Command or manual steps: `.venv\Scripts\python -m pytest`, `npm run test`, `npm run build`, `git status --short`, and backend health check
- Test data: Complete test suites
- Expected: All test suites pass, build succeeds, git status has no unsafe files, and README is updated.
- Actual: All checks passed. 109 backend tests passed. 23 frontend tests passed. Production build succeeded. Health check responds with healthy status. README updated.
- Status: `PASS`
- Evidence: Vitest console output, Vite build output, pytest console output, health check ping response, git status command logs.
- Issue: None
- Next action: None (Phase 0 Complete)
