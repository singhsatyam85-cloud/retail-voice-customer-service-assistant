# Retail AI Voice Customer Service Assistant

## Product Purpose

The Retail AI Voice Customer Service Assistant is designed to handle customer-service calls for retail businesses.

The assistant verifies the caller using the registered phone number, retrieves linked order information, understands the customer’s complaint or request, provides permitted information and creates a pending customer-service case for human review.

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
                ↓
Incoming phone number is identified
                ↓
Phone number matches a registered customer?
          Yes                    No
           ↓                      ↓
Retrieve customer record     Transfer to human
           ↓
Retrieve linked orders
           ↓
One order or multiple orders?
           ↓
Identify the relevant order
           ↓
Understand complaint or request
           ↓
Provide permitted information
           ↓
Create recording and transcript
           ↓
Create pending customer-service case
           ↓
Human agent reviews the case when required