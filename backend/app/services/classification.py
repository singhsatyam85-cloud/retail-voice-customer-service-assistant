"""Transcript classification for voice support.

Provides deterministic keyword-based classification of customer voice
transcripts into supported support-case categories.
"""

from enum import Enum


class IntentCategory(str, Enum):
    ORDER_STATUS = "order_status"
    DELAYED_DELIVERY = "delayed_delivery"
    MISSING_DELIVERY = "missing_delivery"
    DAMAGED_PRODUCT = "damaged_product"
    RETURN_REQUEST = "return_request"
    CANCELLATION_REQUEST = "cancellation_request"
    WRONG_ITEM = "wrong_item"
    HUMAN_AGENT_REQUEST = "human_agent_request"
    NEEDS_CLARIFICATION = "needs_clarification"


def _normalise(text: str) -> str:
    """Lower-case and expand common contractions."""
    t = text.lower()
    for contraction, expansion in (
        ("where's", "where is"),
        ("what's", "what is"),
        ("didn't", "did not"),
        ("don't", "do not"),
        ("i'd", "i would"),
        ("i've", "i have"),
        ("it's", "it is"),
        ("that's", "that is"),
        ("wasn't", "was not"),
        ("weren't", "were not"),
        ("hasn't", "has not"),
        ("haven't", "have not"),
        ("isn't", "is not"),
        ("won't", "will not"),
        ("can't", "cannot"),
        ("couldn't", "could not"),
    ):
        t = t.replace(contraction, expansion)
    return t


def classify_transcript(transcript: str | None) -> IntentCategory:
    """Deterministically classify a transcript into a case category.
    
    Rules:
    - Direct human-agent requests take absolute priority.
    - If exactly one category is detected, return it.
    - If multiple categories conflict, return needs_clarification.
    - If no category is detected, return needs_clarification.
    """
    if not transcript or not transcript.strip():
        return IntentCategory.NEEDS_CLARIFICATION
        
    t = _normalise(transcript)
    
    # Priority: Human agent
    human_keywords = [
        "human", "agent", "person", "representative", 
        "speak to someone", "talk to someone", "customer service",
        "real person", "live agent", "speak with someone",
        "talk with someone", "transfer me", "escalate",
    ]
    if any(k in t for k in human_keywords):
        return IntentCategory.HUMAN_AGENT_REQUEST
        
    detected = set()
    
    # 1. Order Status
    if any(k in t for k in [
        "status", "where is my order", "track", "tracking",
        "order update", "shipping update", "where is my package",
        "where is my delivery", "where is my parcel", "check my order",
        "find my order", "order status", "delivery status", "parcel", "package",
    ]):
        detected.add(IntentCategory.ORDER_STATUS)
        
    # 2. Delayed Delivery
    if any(k in t for k in [
        "late", "delayed", "delay", "taking too long",
        "taking forever", "slow delivery", "overdue",
        "not on time", "behind schedule", "expected by",
        "was supposed to arrive", "should have arrived",
        "still waiting", "been waiting",
    ]):
        detected.add(IntentCategory.DELAYED_DELIVERY)
        
    # 3. Missing Delivery
    if any(k in t for k in [
        "missing", "did not receive", "never arrived",
        "not arrived", "never got", "never received",
        "not delivered", "lost package", "lost parcel",
        "lost delivery", "has not arrived", "where is it",
        "did not arrive", "did not get",
    ]):
        detected.add(IntentCategory.MISSING_DELIVERY)
        
    # 4. Damaged Product
    if any(k in t for k in [
        "broken", "damaged", "smashed", "scratched",
        "faulty", "defective", "cracked", "dented",
        "torn", "ripped", "crushed", "shattered",
    ]):
        detected.add(IntentCategory.DAMAGED_PRODUCT)
        
    # 5. Return Request
    if any(k in t for k in [
        "return", "send back", "refund", "send it back",
        "give back", "money back", "exchange",
    ]):
        detected.add(IntentCategory.RETURN_REQUEST)
        
    # 6. Cancellation Request
    if any(k in t for k in ["cancel"]):
        detected.add(IntentCategory.CANCELLATION_REQUEST)
        
    # 7. Wrong Item
    if any(k in t for k in [
        "wrong", "incorrect", "different item",
        "not what i ordered", "wrong product", "wrong thing",
        "wrong one", "mix up", "mixed up", "mixup",
        "not the right", "different product",
    ]):
        detected.add(IntentCategory.WRONG_ITEM)
        
    if len(detected) == 1:
        return detected.pop()
        
    return IntentCategory.NEEDS_CLARIFICATION
