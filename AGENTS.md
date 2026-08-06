# Development Agent Rules

## Purpose

Use this file to control AI-assisted development of the existing
`retail-voice-customer-service-assistant` repository.

Do not restate product requirements here. Use the existing approved documents.

## Source-of-truth order

When information conflicts, use this order:

1. Running code and observed test results
2. `docs/04-in-app-voice-support-foundation.md`
3. `docs/03-support-case-api.md`
4. `docs/02-caller-verification-api.md`
5. `docs/01-business-requirements.md`
6. `PROJECT_STATE.md`
7. `TASK_QUEUE.md`
8. README and chat history

Important:

- The authenticated in-app voice-support journey is now the primary journey.
- The telephone caller-verification journey remains implemented but is secondary.
- The current voice foundation stops after transcription.
- Support-case creation exists as a separate verified-call workflow.
- Do not assume the transcript-to-case connection already exists.
- Retry idempotency and duplicate-case handling are not approved requirements yet.

## Start-of-session reading

Read only:

1. `AGENTS.md`
2. `PROJECT_STATE.md`
3. `TASK_QUEUE.md`
4. `DECISIONS.md` when the current task refers to a decision
5. Code files required for the current task

Do not reassess the whole repository unless the state files conflict with the code.

## Development rules

- Continue from existing code.
- Preserve the current architecture and technology stack.
- Do not rebuild a working feature.
- Do not rewrite code only for style.
- Do not add cloud deployment, production authentication, telephony integration or paid APIs.
- Keep authority-changing decisions with a human.
- Never automatically approve refunds, returns or cancellations.
- Do not invent customer, order, transcript or case data.
- Do not delete or overwrite the local database.
- Use isolated temporary databases for automated tests.
- Do not implement retry idempotency or duplicate-case semantics without an approved decision in `DECISIONS.md`.
- Ask before changing architecture, replacing providers or adding a large dependency.
- Do not commit or push unless the user explicitly asks.

## Token rules

- Work on one task at a time.
- Read only relevant files.
- Do not repeat project history.
- Do not print complete files in chat.
- Run focused tests before the full suite.
- Update project files immediately after a tested checkpoint.
- Stop after one completed task.

## Required task cycle

1. Read the current task and acceptance criteria.
2. Inspect the relevant implementation.
3. Check whether the task was already partially completed.
4. Make the smallest necessary change.
5. Run focused tests.
6. Review the diff.
7. Update `PROJECT_STATE.md`.
8. Update `TASK_QUEUE.md`.
9. Append the test result to `TEST_LOG.md`.
10. Stop at a tested checkpoint.

## Interrupted-session recovery

When a session stops during a task:

1. Run `git status --short`.
2. Read the current task in `PROJECT_STATE.md`.
3. Inspect the changed files.
4. Check relevant database state before retrying a write.
5. Run the smallest relevant test.
6. Continue from the first safe incomplete action.
7. Update the state files immediately.

Never restart the full task blindly.

## Required response format

```text
Current task:
Work completed:
Files changed:
Test result:
Blocker:
Next task:
```

Use `None` when no blocker exists.
