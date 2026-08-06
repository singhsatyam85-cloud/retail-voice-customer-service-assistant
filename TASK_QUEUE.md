# Task Queue

Work on one task at a time.

Status values:

- `NOT STARTED`
- `IN PROGRESS`
- `BLOCKED`
- `PASS`
- `DEFERRED`

## P0.1 Verify the current baseline

Status: `PASS`

Acceptance criteria:

- Confirm Git state and commit `ecde417`.
- Start the backend.
- Start the frontend.
- Confirm frontend-to-backend communication.
- Run current frontend tests.
- Run the current frontend production build.
- Do not repeat the backend suite unless code changes or the existing result is doubtful.
- Record exact commands and results.

---

## P0.2 Map the current voice-to-case gap

Status: `PASS`

Acceptance criteria:

- Identify the exact frontend and backend files involved after transcript creation.
- Identify the existing support-case service or endpoint that can be reused.
- Confirm whether any classifier or case-draft code already exists.
- Produce a file-level implementation plan of no more than ten lines.
- Do not implement a new classification approach until D005 is approved.

---

## P0.3 Implement transcript classification

Status: `PASS`

Acceptance criteria after approval:

- Convert a transcript into one supported case category.
- Extract or request the relevant order when required.
- Do not fabricate an order selection.
- Return an explicit unknown/needs-clarification result when confidence is insufficient.
- Keep the implementation local and testable.
- Add focused tests for every supported category used in the demo.

---

## P0.4 Create and display a case draft

Status: `PASS`

Acceptance criteria:

- Present category, order and summary before case creation.
- Let the customer correct or cancel the draft.
- Do not create a case merely because transcription completed.
- Keep return, refund and cancellation decisions pending human review.
- Reuse the existing case authority rules.

---

## P0.5 Connect the confirmed voice request to pending-case creation

Status: `PASS`

Acceptance criteria:

- Create a pending case only after customer confirmation.
- Link it to the authenticated customer.
- Link the correct order for order-specific categories.
- Display case ID, pending status and summary.
- Do not allow the client to set status or authority fields.
- Decide retry behaviour according to D006 before adding deduplication.

---

## P0.6 Verify failure and human-support paths

Status: `PASS`

Acceptance criteria:

- Missing or invalid authentication produces a controlled result.
- Microphone denial produces a clear retry or alternative path.
- Unsupported or oversized audio produces a controlled result.
- Speech-provider failure does not expose a traceback.
- Unknown intent asks for clarification or offers human support.
- A direct human-agent request follows the documented authority rules.

---

## P0.7 Run the full local MVP journey

Status: `PASS`

Journey:

1. Open the local application.
2. Use a valid demo-authenticated customer.
3. Open AI Voice Support.
4. Record or upload a supported request.
5. View the transcript.
6. Review the category, order and summary.
7. Confirm the request.
8. Create the pending case.
9. View the case ID and status.
10. Verify persisted records.

Acceptance criteria:

- One complete supported complaint journey passes.
- One direct human-agent request passes.
- No unauthorised business decision is made.
- No critical browser-console or backend error remains.

---

## P0.7.5 WebGL circular DNA voice animation

Status: `PASS`

Acceptance criteria:
- Circular DNA helix structure using `@react-three/fiber` and `three`.
- Distinct motion/color profiles for idle, listening, speaking, processing.
- Centered, lightweight, transparent canvas in the panel body.
- No HTML/SVG type collision in TS compiler.

---

## P0.8 Final regression and documentation check

Status: `PASS`

Acceptance criteria:

- Focused tests pass.
- Full backend suite passes.
- Frontend tests pass.
- Frontend build passes.
- Git diff contains only intended changes.
- No `.env`, database, audio, model, build, cache or dependency files are staged.
- README accurately explains local setup and the verified demo journey.
- Known limitations remain honest and current.
