"""Development-only authentication adapter.

THIS IS NOT PRODUCTION AUTHENTICATION. It exists only so the local MVP
has an authenticated customer context to build the in-app voice-support
journey against. The fictional bearer tokens below map directly onto the
existing seed customers.

A real retailer integration would replace this entire module with the
retailer's existing authentication/session provider (their session
cookie, OAuth token, or app-level identity service). No code outside
this file should know how the demo tokens are structured -- that is the
seam a real integration would cut along.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Customer

# Fictional, local-only bearer tokens. Never a real credential and never
# valid outside this development adapter.
DEMO_TOKEN_TO_CUSTOMER_ID = {
    "demo-cust-101": "CUST-101",
    "demo-cust-102": "CUST-102",
    "demo-cust-103": "CUST-103",
}


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if authorization is None:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def get_authenticated_customer(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Customer:
    """FastAPI dependency resolving the caller's Customer from a demo token.

    Never accept a customer_id from the request body -- identity must
    only ever come from this dependency.
    """
    token = _extract_bearer_token(authorization)
    if token is None:
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header.")

    customer_id = DEMO_TOKEN_TO_CUSTOMER_ID.get(token)
    if customer_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")

    customer = db.get(Customer, customer_id)
    if customer is None or not customer.is_active:
        # Same generic response whichever reason applies -- do not reveal
        # whether the account is missing, inactive, or something else.
        raise HTTPException(status_code=403, detail="Customer account is not available.")

    return customer
