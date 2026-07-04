from __future__ import annotations

import re

from .constants import FORBIDDEN_TERMS


def blocked_terms(*values: str) -> list[str]:
    text = " ".join(value or "" for value in values).lower()
    return [term for term in FORBIDDEN_TERMS if re.search(rf"\b{re.escape(term)}\b", text)]


def safety_note(*values: str) -> str:
    terms = blocked_terms(*values)
    if terms:
        return "Human review required. Restricted or risky terms detected: " + ", ".join(sorted(set(terms)))
    return "No obvious restricted brand, celebrity, logo or trademark terms detected."
