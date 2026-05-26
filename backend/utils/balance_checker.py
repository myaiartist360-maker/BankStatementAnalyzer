"""
BSA Engine — Balance Continuity Checker
Verifies: closing_balance[n] == closing_balance[n-1] + credit[n] - debit[n]
"""

from __future__ import annotations
from typing import Optional
from config import settings


def check_balance_continuity(
    transactions: list[dict],
) -> list[dict]:
    """
    Runs balance continuity check on a list of transaction dicts.
    Each dict must have: date, closing_balance, credit_amount, debit_amount.

    Returns a list of failed-row dicts with:
        {row_index, date, expected_balance, actual_balance, delta}
    """
    failures: list[dict] = []
    tol = settings.balance_continuity_tolerance

    prev_balance: Optional[float] = None

    for i, txn in enumerate(transactions):
        cb = txn.get("closing_balance")
        credit = txn.get("credit_amount") or 0.0
        debit = txn.get("debit_amount") or 0.0

        if cb is None:
            prev_balance = None  # can't carry forward
            continue

        if prev_balance is not None:
            expected = round(prev_balance + credit - debit, 2)
            delta = abs(cb - expected)
            if delta > tol:
                failures.append({
                    "row_index": i,
                    "date": txn.get("date"),
                    "narration": txn.get("narration", ""),
                    "expected_balance": expected,
                    "actual_balance": cb,
                    "delta": round(delta, 2),
                })

        prev_balance = cb

    return failures
