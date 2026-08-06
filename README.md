# Retail AI Voice Customer Service Assistant

## Product Purpose

The Retail AI Voice Customer Service Assistant is designed to handle customer-service calls for retail businesses.

The assistant verifies the caller using the registered phone number, retrieves linked order information, understands the customerâ€™s complaint or request, provides permitted information and creates a pending customer-service case for human review.

The target product is intended for integration with a retail telephone or contact-centre system.

During the MVP stage, a browser microphone and a simulated incoming phone number will be used only to test the voice conversation and customer-service process locally.

The purpose of this MVP is to demonstrate how an AI voice assistant can reduce repetitive call-handling work while keeping refunds, returns, cancellations and other sensitive decisions under human control.

## Business Problem

Retail customer-service teams receive repeated calls about order status, delivery delays, damaged products, returns, cancellations and missing items.

Agents often spend time verifying customers, searching for orders, recording complaints and creating cases.

This product aims to automate the early stages of the call while transferring complex or sensitive decisions to a human agent.

## Target Users

- Retail customers contacting customer service
- Customer-service agents
- Customer-service team leaders
- Complaint-handling teams
- Retail operations teams

## MVP Scope

The MVP will support:

- simulated incoming customer calls
- voice interaction through a microphone
- simulated incoming phone-number identification
- customer verification using the registered phone number
- order retrieval using the verified customer record
- clarification when multiple orders are found
- speech-to-text conversion
- AI-generated customer-service responses
- text-to-speech voice responses
- call recording
- conversation transcript creation
- complaint and request classification
- pending case creation
- transfer to a human agent when required
- customer, order and case information display

## Supported Customer Requests

The assistant will support:

- order status enquiries
- delayed delivery complaints
- missing delivery complaints
- damaged product complaints
- return requests
- cancellation requests
- wrong item received complaints
- requests to speak with a human agent

## Customer Verification Rules

1. The assistant must first check the incoming phone number.

2. When the incoming phone number matches a registered customer, the customer can proceed to the next stage.

3. When the phone number is hidden, unavailable or unmatched, the interaction must be transferred to a human agent.

4. The assistant must not request the order number first when the customer has already been verified.

5. When multiple orders are linked to the same customer, the assistant must ask which order the customer is calling about.

## Business Rules

1. The assistant may provide order and delivery information available in the system.

2. The assistant may capture complaints and customer requests.

3. The assistant may create a pending customer-service case.

4. The assistant must record the call and create a transcript.

5. The assistant must link the interaction to the verified customer and relevant order.

6. The assistant must transfer the interaction to a human when verification fails.

7. The assistant must transfer the interaction when the customer directly requests a human agent.

8. The assistant must not approve or reject returns during Phase 1.

9. The assistant must not issue refunds during Phase 1.

10. The assistant must not approve cancellations during Phase 1.

11. The assistant must not update finance or inventory systems during Phase 1.

12. Final decisions must remain with an authorised human agent.

## High-Level Customer Journey

```text
Customer calls retail customer service
                â†“
Incoming phone number is identified
                â†“
Phone number matches a registered customer?
          Yes                    No
           â†“                      â†“
Retrieve customer record     Transfer to human
           â†“
Retrieve linked orders
           â†“
One order or multiple orders?
           â†“
Identify the relevant order
           â†“
Understand complaint or request
           â†“
Provide permitted information
           â†“
Create recording and transcript
           â†“
Create pending customer-service case
           â†“
Human agent reviews the case when required
```

---

## Technical Setup & Developer Guide

### Startup Commands

To run the application locally:

#### Backend
Start the FastAPI server from the repository root:
```bash
.venv\Scripts\python -m uvicorn backend.app.main:app
```
Health check endpoint: `http://127.0.0.1:8000/health`

#### Frontend
Start the Vite development server from the `frontend/` directory:
```bash
npm run dev
```
Development page: `http://localhost:5173/`

### Demo Authentication Setup
The application simulates an already-authenticated session. The bearer token can be configured in `frontend/.env` via the `VITE_DEMO_AUTH_TOKEN` key.
Available demo credentials:
- `demo-cust-101`: Test Customer One (linked to one order `ORD-5001`).
- `demo-cust-102`: Test Customer Two (linked to multiple orders `ORD-5002` and `ORD-5003`).
- `demo-cust-103`: Test Customer Three (no orders).

---

### MVP In-App Voice Support Journey

1. **Start Session**: Click the floating **AI Voice Support** widget at the bottom corner of the web page. The panel retrieves verified customer and order information.
2. **WebGL circular DNA Orb Animation**: Renders a premium, smooth circular DNA-like double-helix structure inside the panel.
   - **idle**: Slow rotation, soft pulsing (before recording).
   - **listening**: Active outward and inward wave breathing (while recording).
   - **processing**: Medium-speed rotation, tighter ring movement (during audio uploading and case processing).
   - **speaking**: Energy-rich oscillation (occurs once assistant transcript results are displayed on screen).
3. **Record Request**: Click **Start speaking**, record your complaint, and click **Stop**.
4. **Deterministic Classification**: The mock provider transcribes the audio, and the backend deterministically maps keywords to support categories.
5. **Review Case Draft**: The UI displays:
   - Request Category (e.g. `delayed_delivery`, `human_agent_request`).
   - Transcript Summary (captured directly from the user speech).
   - Preselected Order (suggested when exactly one order exists) or require explicit manual selection (when multiple orders exist).
   - Human-review notice.
6. **Submit Case**: Click **Confirm and Create Case**. A `SupportCase` database record is generated, and its ID, status, and summary are presented.

---

### Verification and Testing

#### Backend Suite
Run the full backend test suite:
```bash
.venv\Scripts\python -m pytest
```
*Result*: 109 tests passed.

#### Frontend Suite
Run the Vitest test runner:
```bash
npm run test
```
*Result*: 23 tests passed.

#### Production Build
Compile production assets:
```bash
npm run build
```
*Result*: Compiles successfully.
Final bundle sizes:
- JS: `1086.42 kB` (uncompressed), `298.42 kB` (gzip)
- CSS: `5.58 kB` (uncompressed), `1.82 kB` (gzip)

---

### Known Limitations

- **Demo Authentication is Local-Only**: Authorization relies on simulated header values and is not connected to a production authentication system.
- **No Telephone Integration**: The MVP is browser-based and does not connect to real VoIP/SIP telephony services.
- **No Automated Authority Decisions**: Refunds, returns, or cancellations are marked as pending human review and are never automatically approved.
- **Optional Speech Model**: `faster-whisper` is optional; by default, the app uses a deterministic mock speech-to-text provider.
- **No Text-to-Speech Output**: Actual voice synthesis (audio playback) is not implemented. The `speaking` state visually represents the rendering of final transcription results.
- **Manual Microphone Confirmation**: The browser requires explicit user interaction to grant microphone permissions.
- **Mocked WebGL Tests**: To prevent crashes in headless test runners (like JSDOM), WebGL Canvas rendering is stubbed out in automated tests.
