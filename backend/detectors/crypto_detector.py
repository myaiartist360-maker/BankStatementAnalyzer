"""
BSA Engine — Crypto Transaction Detector
"""

from __future__ import annotations
from lexicon import CRYPTO_REGEX


def detect_crypto(transactions: list[dict]) -> dict:
    """
    Returns: {count, total_amount}
    """
    count = 0
    total = 0.0
    for t in transactions:
        narr = t.get("narration") or ""
        if CRYPTO_REGEX.search(narr):
            count += 1
            total += t.get("debit_amount") or t.get("credit_amount") or 0.0
    return {"count": count, "total_amount": round(total, 2)}
