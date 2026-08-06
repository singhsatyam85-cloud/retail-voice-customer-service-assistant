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


def classify_transcript(transcript: str | None) -> IntentCategory:
    """Deterministically classify a transcript into a case category.
    
    Rules:
    - Direct human-agent requests take absolute priority.
    - If exactly one category is detected, return it.
    - If multiple categories conflict, return needs_clarification.
    - If no category is detected, return needs_clarification.
    """
    if not transcript:
        return IntentCategory.NEEDS_CLARIFICATION
        
    t = transcript.lower()
    
    # Priority: Human agent
    human_keywords = [
        "human", "agent", "person", "representative", 
        "speak to someone", "talk to someone", "customer service"
    ]
    if any(k in t for k in human_keywords):
        return IntentCategory.HUMAN_AGENT_REQUEST
        
    detected = set()
    
    # 1. Order Status
    if any(k in t for k in ["status", "where is my order", "track my order"]):
        detected.add(IntentCategory.ORDER_STATUS)
        
    # 2. Delayed Delivery
    if any(k in t for k in ["late", "delayed", "taking too long"]):
        detected.add(IntentCategory.DELAYED_DELIVERY)
        
    # 3. Missing Delivery
    if any(k in t for k in ["missing", "didn't receive", "did not receive", "never arrived", "not arrived", "never got"]):
        detected.add(IntentCategory.MISSING_DELIVERY)
        
    # 4. Damaged Product
    if any(k in t for k in ["broken", "damaged", "smashed", "scratched", "faulty", "defective"]):
        detected.add(IntentCategory.DAMAGED_PRODUCT)
        
    # 5. Return Request
    if any(k in t for k in ["return", "send back", "refund"]):
        detected.add(IntentCategory.RETURN_REQUEST)
        
    # 6. Cancellation Request
    if any(k in t for k in ["cancel"]):
        detected.add(IntentCategory.CANCELLATION_REQUEST)
        
    # 7. Wrong Item
    if any(k in t for k in ["wrong", "incorrect", "different item", "not what i ordered"]):
        detected.add(IntentCategory.WRONG_ITEM)
        
    if len(detected) == 1:
        return detected.pop()
        
    return IntentCategory.NEEDS_CLARIFICATION
