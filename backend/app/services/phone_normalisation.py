"""UK phone-number normalisation for the Phase 1 caller-verification MVP.

Scope is intentionally limited to the agreed UK MVP rule: one registered
phone number maps to one active fictional customer, stored in E.164-style
UK format (e.g. "+447700900101"). This is not a general phone-number
parsing library.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Optional

NormalisationStatus = Literal["valid", "unavailable", "invalid"]

# Values a telephony system may report instead of a real number.
_HIDDEN_VALUES = {"withheld", "private", "unknown"}

# Spaces, hyphens and parentheses are formatting only and are stripped
# before the prefix is inspected.
_FORMATTING_CHARS = re.compile(r"[\s\-()]")


@dataclass(frozen=True)
class PhoneNormalisationResult:
    status: NormalisationStatus
    normalised_number: Optional[str]


def normalise_uk_phone(raw: Optional[str]) -> PhoneNormalisationResult:
    """Normalise a caller-supplied value into the stored UK E.164 format.

    Returns status "unavailable" for missing/blank/hidden values,
    "invalid" for values that cannot be interpreted as a supported UK
    number, or "valid" with the normalised "+44XXXXXXXXXX" number.
    """
    if raw is None:
        return PhoneNormalisationResult("unavailable", None)

    text = raw.strip()
    if text == "":
        return PhoneNormalisationResult("unavailable", None)

    if text.lower() in _HIDDEN_VALUES:
        return PhoneNormalisationResult("unavailable", None)

    cleaned = _FORMATTING_CHARS.sub("", text)

    if cleaned.startswith("+44"):
        remainder = cleaned[3:]
    elif cleaned.startswith("0044"):
        remainder = cleaned[4:]
    elif cleaned.startswith("0") and not cleaned.startswith("00"):
        remainder = cleaned[1:]
    else:
        return PhoneNormalisationResult("invalid", None)

    if not remainder.isdigit() or len(remainder) != 10 or remainder[0] == "0":
        return PhoneNormalisationResult("invalid", None)

    return PhoneNormalisationResult("valid", f"+44{remainder}")