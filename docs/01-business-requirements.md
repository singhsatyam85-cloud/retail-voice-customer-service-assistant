Retail AI Voice Customer Service Assistant - Business Requirements

Document Information

Item

Details

Document name

Business Requirements

Product

Retail AI Voice Customer Service Assistant

Document status

Draft

Version

0.1

Prepared by

Business Analyst

Delivery phase

MVP Phase 1

Last updated

29 July 2026

1. Document Purpose

This document defines the business requirements for the Retail AI Voice Customer Service Assistant.

It describes:

the business problem

product objectives

users and stakeholders

MVP scope

business requirements

business rules

functional requirements

data requirements

non-functional requirements

escalation conditions

Phase 1 limitations

acceptance conditions

This document will be used by the Product Owner, Developers, AI Engineers, Voice Engineers and QA Engineers during product design, development and testing.

2. Product Overview

The Retail AI Voice Customer Service Assistant is designed to handle common customer-service calls for retail businesses.

The assistant will:

identify the incoming phone number

verify whether the phone number belongs to a registered customer

retrieve the customer record

retrieve linked order information

understand the customer’s complaint or request

provide information that the assistant is authorised to provide

record the interaction

create a transcript

classify the complaint or request

create a pending customer-service case

transfer the customer to a human agent when required

The target product is intended for future integration with a real retail telephone or contact-centre system.

During the MVP, a browser microphone and simulated incoming phone number will be used to test the complete customer-service journey locally.

3. Business Problem

Retail customer-service teams receive repeated calls regarding:

order status

delayed delivery

missing delivery

damaged products

wrong items

return requests

cancellation requests

requests to speak with a human agent

Customer-service agents spend time on repetitive activities such as:

identifying the customer

searching for customer records

finding linked orders

asking standard questions

recording complaint details

writing call notes

creating customer-service cases

transferring calls to another team

This increases call-handling time and reduces the time available for complex customer issues.

The business requires a voice assistant that can complete the early stages of the customer-service process while keeping sensitive decisions under human control.

4. Business Objectives

The objectives of the MVP are to:

demonstrate automated handling of common retail customer-service enquiries

reduce repetitive customer verification and order-search activity

provide customers with available order and delivery information

capture customer complaints and requests consistently

create structured call records and transcripts

create pending cases for human review

transfer customers to a human agent when verification fails

prevent the assistant from making unauthorised financial or eligibility decisions

demonstrate a complete voice interaction without using an external AI API

prepare the product for future telephone and contact-centre integration

5. Target Users

5.1 Retail Customers

Customers who contact the retailer regarding an order, delivery, product problem, return, cancellation or complaint.

5.2 Customer-Service Agents

Agents who receive transferred calls or review cases created by the assistant.

5.3 Customer-Service Team Leaders

Team leaders who review escalations, case quality and assistant performance.

5.4 Complaint-Handling Teams

Teams responsible for investigating damaged products, wrong items, missing deliveries and formal complaints.

5.5 Retail Operations Teams

Teams responsible for order processing, fulfilment and delivery operations.

5.6 Product and Technology Teams

Teams responsible for maintaining, testing and improving the product.

6. Stakeholders

Stakeholder

Main Interest

Retail customers

Fast and accurate customer service

Customer-service agents

Complete call information and clear case details

Customer-service managers

Reduced repetitive work and consistent handling

Complaint teams

Accurate complaint records

Retail operations

Correct order and delivery information

Product Owner

Product priorities and business value

Business Analyst

Requirements, rules, processes and acceptance criteria

Backend Developer

Verification, order retrieval, case and database services

Frontend Developer

Local testing interface and information display

AI Engineer

Conversation understanding and controlled responses

Voice Engineer

Speech-to-text and text-to-speech processing

QA Engineer

Requirement-based testing

Compliance or Data Protection Team

Customer-data handling and recording controls

Contact-Centre Engineer

Future telephone-system integration

7. MVP Scope

7.1 In Scope

The Phase 1 MVP will include:

simulated incoming customer calls

simulated incoming phone-number identification

customer verification through the registered phone number

customer record retrieval

linked order retrieval

clarification when multiple orders are found

browser microphone input

speech-to-text processing

AI-generated customer-service responses

text-to-speech responses

complaint and request identification

complaint category assignment

call recording

transcript creation

structured call-record creation

pending case creation

linking the call to the customer and order

human-agent transfer conditions

customer, order, conversation and case display

local sample data

local application operation

local language-model processing

7.2 Out of Scope

The Phase 1 MVP will not:

connect to a real telephone network

connect to a live contact-centre platform

use real customer data

use a live external AI API

operate as a public cloud service

approve or reject returns

issue refunds

approve cancellations

automatically cancel orders

update payment records

update finance systems

update inventory systems

make final complaint decisions

perform identity verification beyond the agreed phone-number rule

send real customer emails or text messages

make changes to live retail systems

8. Assumptions

The MVP is based on the following assumptions:

Sample customer and order data will be available locally.

Every registered sample customer will have a phone number.

An incoming phone number will be simulated through the testing interface.

One customer may have one or more orders.

Order and delivery information will already exist in the local database.

Human transfer will be simulated during the MVP.

The user’s browser and computer will have microphone access.

The local language model will be available through Ollama.

Speech-to-text and text-to-speech services will run locally.

Only English-language interactions will be supported initially.

Final decisions will remain with authorised human agents.

The MVP will be used for learning, demonstration and testing purposes.

9. Constraints

The MVP has the following constraints:

it must operate locally

it must not depend on an external AI API

it must use sample data only

it must not perform financial transactions

it must not update live business systems

it must not make final eligibility decisions

it must not continue with an unverified customer

it must remain within the agreed Phase 1 complaint categories

the browser is a testing channel, not the final customer channel

10. High-Level Customer Journey

Customer calls retail customer service↓Incoming phone number is identified↓Does the phone number match a registered customer?Yes → Retrieve customer recordNo → Transfer to human↓Retrieve linked orders↓Is more than one order available?Yes → Ask customer to identify the orderNo → Continue with the available order↓Understand complaint or request↓Provide permitted information↓Record the interaction↓Create transcript↓Create pending customer-service case↓Transfer to human when required

11. Business Requirements

BR-001 - Incoming Caller Identification

The product must receive or simulate the incoming customer phone number at the beginning of the interaction.

BR-002 - Customer Verification

The product must verify whether the incoming phone number matches a registered customer record.

BR-003 - Verification Failure

The product must transfer the interaction to a human agent when the phone number is hidden, unavailable or unmatched.

BR-004 - Customer Retrieval

The product must retrieve the customer record after successful phone-number verification.

BR-005 - Order Retrieval

The product must retrieve orders linked to the verified customer.

BR-006 - Order Clarification

The product must ask the customer to identify the relevant order when multiple orders are available.

BR-007 - Complaint Understanding

The product must identify the reason for the customer’s call.

BR-008 - Permitted Information

The product must provide available order and delivery information that it is authorised to share.

BR-009 - Complaint Capture

The product must capture the customer’s complaint or request.

BR-010 - Complaint Classification

The product must assign the interaction to an agreed complaint or request category.

BR-011 - Call Recording

The product must create a recording of the customer-service interaction.

BR-012 - Transcript Creation

The product must create a written transcript of the interaction.

BR-013 - Call Record

The product must create a structured call record for every completed interaction.

BR-014 - Pending Case Creation

The product must create a pending customer-service case when a complaint or request requires further action.

BR-015 - Customer and Order Link

The product must link the call record and case to the verified customer and relevant order.

BR-016 - Human-Agent Request

The product must transfer the interaction when the customer asks to speak with a human agent.

BR-017 - Restricted Decisions

The product must not approve refunds, returns, cancellations or other restricted decisions during Phase 1.

BR-018 - Human Review

The product must leave final decisions for an authorised human agent.

BR-019 - Data Protection

The MVP must use sample customer, order and complaint data only.

BR-020 - Local Operation

The MVP must operate locally without a public cloud deployment.

BR-021 - Local AI Processing

The MVP must use a local language model rather than a live external AI API.

BR-022 - Future Telephone Integration

The product design must allow future integration with a telephone or contact-centre platform.

12. Supported Complaint and Request Categories

Category ID

Category

CAT-001

Order status

CAT-002

Delayed delivery

CAT-003

Missing delivery

CAT-004

Damaged product

CAT-005

Return request

CAT-006

Cancellation request

CAT-007

Wrong item received

CAT-008

Human-agent request

The assistant must not create unsupported categories without an approved requirement change.

13. Business Rules

RULE-001

The incoming phone number must be checked before order information is retrieved.

RULE-002

A matching registered phone number will be treated as successful verification for the Phase 1 MVP.

RULE-003

A hidden, unavailable or unmatched phone number must result in human transfer.

RULE-004

The assistant must not ask for an order number first when the customer has already been verified.

RULE-005

When only one order is available, the assistant may continue using that order.

RULE-006

When multiple orders are available, the assistant must ask the customer which order the call relates to.

RULE-007

The assistant may read available order and delivery information.

RULE-008

The assistant may capture a complaint or request.

RULE-009

The assistant may create a pending case.

RULE-010

The assistant must not approve or reject a return during Phase 1.

RULE-011

The assistant must not issue or approve a refund during Phase 1.

RULE-012

The assistant must not approve or complete a cancellation during Phase 1.

RULE-013

The assistant must not update finance, payment or inventory systems.

RULE-014

The assistant must transfer the interaction when the customer requests a human agent.

RULE-015

The assistant must create a transcript and call record for a completed interaction.

RULE-016

The assistant must clearly explain when a request requires human review.

RULE-017

The assistant must not claim that a refund, return or cancellation has been approved when no authorised decision has occurred.

RULE-018

The assistant must use only information available in the local customer and order data.

RULE-019

The assistant must not invent order information, delivery dates or case outcomes.

RULE-020

The assistant must not disclose one customer’s information to another customer.

14. Functional Requirements

FR-001 - Receive Phone Number

The system must accept a simulated incoming phone number from the testing interface.

FR-002 - Search Customer

The system must search the customer database using the incoming phone number.

FR-003 - Return Verification Result

The system must return one of the following verification results:

verified

unmatched

hidden

unavailable

FR-004 - Retrieve Customer Details

For a verified customer, the system must retrieve:

customer ID

customer name

registered phone number

email address, where available

customer status

FR-005 - Retrieve Orders

The system must retrieve all orders linked to the verified customer.

FR-006 - Display Order Summary

The system must make available:

order ID

order date

order status

delivery status

expected delivery date, where available

items ordered

order value

FR-007 - Select Relevant Order

The system must allow the relevant order to be selected when more than one order exists.

FR-008 - Capture Microphone Input

The testing interface must capture the customer’s voice through the browser microphone.

FR-009 - Convert Speech to Text

The system must convert the customer’s speech into text.

FR-010 - Understand Customer Intent

The system must determine the complaint or request category from the conversation.

FR-011 - Generate Response

The system must generate a response that follows the approved business rules.

FR-012 - Convert Text to Speech

The system must convert the assistant’s response into audible speech.

FR-013 - Display Conversation

The testing interface must display the customer and assistant conversation.

FR-014 - Record Call

The system must store the interaction recording locally.

FR-015 - Create Transcript

The system must create and store a written transcript locally.

FR-016 - Create Call Record

The system must create a call record containing:

call ID

customer ID

order ID, where identified

incoming phone number

verification result

call start time

call end time

complaint category

transcript location

recording location

transfer status

FR-017 - Create Pending Case

The system must create a pending case containing:

case ID

customer ID

order ID

call ID

complaint category

complaint summary

requested action

case status

created date and time

human-review requirement

FR-018 - Transfer to Human

The system must trigger a simulated human transfer when:

verification fails

the phone number is hidden

the phone number is unavailable

the customer asks for a human

the request falls outside the permitted scope

the assistant cannot safely determine the next action

FR-019 - Prevent Restricted Actions

The system must block:

refund approval

return approval or rejection

cancellation approval

finance updates

inventory updates

final complaint decisions

FR-020 - Display Case Result

The testing interface must show whether:

a case was created

the case is pending

a human review is required

the call was transferred

15. Data Requirements

15.1 Customer Data

The customer record may contain:

Field

Description

customer_id

Unique customer identifier

full_name

Customer name

phone_number

Registered phone number

email

Customer email address

customer_status

Active or inactive status

15.2 Order Data

The order record may contain:

Field

Description

order_id

Unique order identifier

customer_id

Linked customer identifier

order_date

Date the order was placed

order_status

Current order status

delivery_status

Current delivery status

expected_delivery_date

Expected delivery date

total_amount

Total order value

15.3 Order-Item Data

The order-item record may contain:

Field

Description

order_item_id

Unique order-item identifier

order_id

Linked order identifier

product_name

Ordered product name

quantity

Number of units

unit_price

Price per unit

15.4 Call Data

The call record may contain:

Field

Description

call_id

Unique call identifier

customer_id

Linked customer

order_id

Linked order, where available

incoming_phone_number

Simulated incoming number

verification_status

Verification result

start_time

Call start time

end_time

Call end time

complaint_category

Assigned category

transcript_path

Transcript file location

recording_path

Recording file location

transfer_status

Whether transfer occurred

15.5 Case Data

The case record may contain:

Field

Description

case_id

Unique case identifier

customer_id

Linked customer

order_id

Linked order

call_id

Linked call

category

Complaint or request category

summary

Summary of the issue

requested_action

What the customer requested

status

Pending, transferred or closed

human_review_required

Yes or no

created_at

Case creation date and time

16. Data Validation Rules

Every customer must have a unique customer ID.

Every order must have a unique order ID.

Every call must have a unique call ID.

Every case must have a unique case ID.

A verified call must be linked to one customer.

An order must be linked to an existing customer.

A case must be linked to a call.

A complaint category must use an approved category value.

A case created by the assistant must initially have a pending status.

Real customer data must not be used in the MVP.

Passwords, API keys and confidential information must not be stored in the repository.

Recordings and transcripts must not be committed to GitHub.

17. Non-Functional Requirements

NFR-001 - Usability

The testing interface must clearly show:

call status

verification status

customer details

order details

conversation

case result

transfer result

NFR-002 - Response Clarity

Assistant responses must use clear and customer-friendly language.

NFR-003 - Accuracy

The assistant must use only the customer and order information available in the local system.

NFR-004 - Privacy

The MVP must use sample data and must not expose confidential information.

NFR-005 - Security

Secrets, passwords and API credentials must not be stored in source-code files or committed to GitHub.

NFR-006 - Traceability

Each important system behaviour must be traceable to a business requirement or business rule.

NFR-007 - Maintainability

The frontend, backend, voice services and local AI components should be organised separately.

NFR-008 - Auditability

Call records, transcripts and case records must make it possible to understand what happened during an interaction.

NFR-009 - Error Handling

The system must display or record a clear error when:

microphone access fails

speech cannot be understood

customer retrieval fails

order retrieval fails

the local model is unavailable

case creation fails

NFR-010 - Controlled Responses

The assistant must not make claims or decisions outside the approved business rules.

NFR-011 - Local Availability

The MVP must be capable of running on the local development computer.

NFR-012 - Testing

Core verification, order retrieval, classification and case-creation rules must support automated testing.

18. Human Transfer Conditions

The assistant must transfer the customer to a human agent when:

the incoming phone number is hidden

the incoming phone number is unavailable

the phone number does not match a registered customer

the customer asks for a human agent

the request is outside the approved Phase 1 scope

the assistant cannot identify the relevant order

the assistant cannot understand the complaint after reasonable clarification

the customer disputes the information provided

a refund, return or cancellation decision is required

a safety, legal or sensitive issue is identified

the system experiences a technical failure

the assistant cannot provide a reliable response

19. Exception Scenarios

EX-001 - Hidden Number

The system must stop automated processing and transfer the interaction.

EX-002 - Unmatched Number

The system must not disclose customer or order information.

EX-003 - No Orders Found

The system must explain that no linked order was found and transfer the interaction where required.

EX-004 - Multiple Orders

The system must ask the customer to identify the relevant order.

EX-005 - Unclear Speech

The assistant must ask the customer to repeat the information.

EX-006 - Unsupported Request

The assistant must explain that the request requires human support.

EX-007 - Local AI Model Unavailable

The system must display an error and stop automated conversation processing.

EX-008 - Case Creation Failure

The system must record the failure and inform the user that human follow-up is required.

EX-009 - Customer Requests Refund

The assistant must capture the request, create a pending case and explain that an authorised agent will review it.

EX-010 - Customer Requests Cancellation

The assistant must capture the request without confirming that the order has been cancelled.

20. Phase 1 Assistant Permissions

The assistant may:

check an incoming phone number

verify a registered phone-number match

retrieve a customer record

retrieve linked orders

provide available order information

provide available delivery information

ask clarification questions

capture a complaint

capture a return request

capture a cancellation request

classify the interaction

record the call

create a transcript

create a pending case

transfer the interaction to a human agent

The assistant may not:

approve a return

reject a return

issue a refund

approve a refund

approve a cancellation

confirm that an order has been cancelled

update a payment

update finance information

update inventory

make a final complaint decision

access another customer’s information

invent unavailable order information

21. Future Phase 2 Requirements

Phase 2 may include:

real telephone-system integration

contact-centre platform integration

additional customer verification

return eligibility checks

cancellation eligibility checks

refund approval workflows

finance-system integration

inventory-system integration

customer notification services

agent dashboard

supervisor dashboard

reporting and performance monitoring

multilingual support

complaint-priority scoring

sentiment detection

automated case assignment

Phase 2 items are not approved for the current MVP unless they are moved into scope through formal change control.

22. High-Level Acceptance Conditions

The MVP will be considered functionally acceptable when:

a simulated incoming phone number can be entered

a matching customer can be identified

an unmatched customer is transferred

linked orders can be retrieved

multiple-order clarification works

customer speech can be converted to text

the complaint category can be identified

the assistant can generate an allowed response

the response can be converted to speech

the interaction can be recorded

a transcript can be created

a structured call record can be created

a pending case can be created

restricted decisions remain blocked

human-transfer conditions work

only sample data is used

the solution operates locally

core business rules pass testing

23. Requirement Traceability Summary

Business Requirement

Related Functional Requirement

BR-001

FR-001

BR-002

FR-002, FR-003

BR-003

FR-003, FR-018

BR-004

FR-004

BR-005

FR-005, FR-006

BR-006

FR-007

BR-007

FR-009, FR-010

BR-008

FR-006, FR-011

BR-009

FR-010, FR-017

BR-010

FR-010

BR-011

FR-014

BR-012

FR-015

BR-013

FR-016

BR-014

FR-017

BR-015

FR-016, FR-017

BR-016

FR-018

BR-017

FR-019

BR-018

FR-017, FR-018

BR-019

FR-004, FR-005

BR-020

All MVP functional requirements

BR-021

FR-010, FR-011

BR-022

Future architecture consideration

24. Risks

Risk

Possible Effect

Initial Control

Speech is transcribed incorrectly

Wrong complaint understanding

Ask the customer to repeat or confirm

Local model generates an incorrect answer

Customer receives unreliable information

Restrict responses to retrieved data and approved rules

Phone number is treated as sufficient verification

Identity risk in a real implementation

Limit this rule to the MVP and define stronger Phase 2 verification

Recording contains personal information

Privacy risk

Use sample data only

Customer has multiple orders

Wrong order may be selected

Require order clarification

Local voice services are slow

Delayed interaction

Measure processing time during testing

Assistant attempts a restricted action

Financial or operational risk

Enforce backend restrictions

Case creation fails

Complaint may not be recorded

Log the failure and transfer to human

Scope expands during development

Delayed delivery

Use agreed scope and change control

25. Dependencies

The MVP depends on:

Python

FastAPI

React

SQLite

Ollama

a suitable local language model

faster-whisper

Piper text-to-speech

browser microphone access

sample customer and order data

local development environment

Git and GitHub

26. Open Decisions

The following decisions may be confirmed during later stages:

exact local language model

recording audio format

transcript file format

data-retention period

exact customer-service response wording

case-priority rules

number of clarification attempts

final simulated transfer behaviour

reporting requirements

future telephone provider

future contact-centre platform

These decisions must not change the agreed Phase 1 business rules without review.

27. Change Control

Any proposed change must identify:

requested change

reason for the change

affected requirements

affected business rules

impact on scope

impact on development

impact on testing

priority

approval decision

The Business Analyst will update requirement IDs and traceability after an approved change.

28. Business Analyst Responsibilities

The Business Analyst is responsible for:

defining the business problem

identifying stakeholders

gathering requirements

analysing the current process

defining the future process

defining MVP scope

documenting exclusions

defining business rules

defining complaint categories

documenting data requirements

defining exception scenarios

defining human-transfer conditions

writing functional requirements

writing non-functional requirements

creating process maps

writing user stories

writing acceptance criteria

maintaining requirement traceability

managing requirement changes

supporting Developers

supporting QA Engineers

preparing UAT scenarios

validating the delivered solution

confirming that the product meets the agreed business need

29. Review and Approval

Role

Responsibility

Status

Business Analyst

Prepare and maintain requirements

Draft

Product Owner

Review scope and priorities

Pending

Technical Lead

Review feasibility

Pending

QA Lead

Review testability

Pending

Data Protection or Compliance Reviewer

Review recording and data controls

Pending

30. Document Status

This document is currently a draft requirements baseline for the Phase 1 MVP.

Requirements may be clarified during development, but material scope or business-rule changes must be reviewed and recorded through change control.