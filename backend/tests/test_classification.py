"""Tests for deterministic transcript classification."""

import pytest

from backend.app.services.classification import IntentCategory, classify_transcript


def test_empty_transcript_returns_needs_clarification():
    assert classify_transcript("") == IntentCategory.NEEDS_CLARIFICATION
    assert classify_transcript("   ") == IntentCategory.NEEDS_CLARIFICATION
    assert classify_transcript(None) == IntentCategory.NEEDS_CLARIFICATION


def test_human_agent_priority():
    # Even if it contains other keywords, human request wins
    assert classify_transcript("My order is late but I want to speak to someone") == IntentCategory.HUMAN_AGENT_REQUEST
    assert classify_transcript("Can I talk to a human about my broken item?") == IntentCategory.HUMAN_AGENT_REQUEST


@pytest.mark.parametrize(
    "transcript, expected_category",
    [
        ("What is the status of my order?", IntentCategory.ORDER_STATUS),
        ("Where is my order, it should be here", IntentCategory.ORDER_STATUS),
        ("My delivery is delayed", IntentCategory.DELAYED_DELIVERY),
        ("It's taking too long to arrive", IntentCategory.DELAYED_DELIVERY),
        ("My package never arrived", IntentCategory.MISSING_DELIVERY),
        ("I didn't receive my parcel", IntentCategory.MISSING_DELIVERY),
        ("The item arrived broken", IntentCategory.DAMAGED_PRODUCT),
        ("My product is completely smashed", IntentCategory.DAMAGED_PRODUCT),
        ("I would like to return this", IntentCategory.RETURN_REQUEST),
        ("Can I get a refund please", IntentCategory.RETURN_REQUEST),
        ("I need to cancel my order", IntentCategory.CANCELLATION_REQUEST),
        ("They sent me the wrong item", IntentCategory.WRONG_ITEM),
        ("This is not what I ordered", IntentCategory.WRONG_ITEM),
    ],
)
def test_single_intent_classification(transcript, expected_category):
    assert classify_transcript(transcript) == expected_category


def test_conflicting_intents_return_needs_clarification():
    # Contains both "cancel" and "return"
    assert classify_transcript("I want to cancel or return my order") == IntentCategory.NEEDS_CLARIFICATION
    
    # Contains both "damaged" and "missing"
    assert classify_transcript("Half my items are missing and the rest are broken") == IntentCategory.NEEDS_CLARIFICATION


def test_unknown_intent_returns_needs_clarification():
    assert classify_transcript("I like your products") == IntentCategory.NEEDS_CLARIFICATION
    assert classify_transcript("What time does the store open?") == IntentCategory.NEEDS_CLARIFICATION
