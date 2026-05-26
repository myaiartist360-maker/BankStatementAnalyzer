"""
BSA Engine — Step 3: Data Extraction
Derives transaction_mode and is_reversal; normalises raw parser output.
"""

from __future__ import annotations
import re
from typing import Optional

from config import TRANSACTION_MODE_PATTERNS, REVERSAL_KEYWORDS


def derive_transaction_mode(narration: str) -> str:
    """
    First-match wins against TRANSACTION_MODE_PATTERNS.
    Falls back to 'OTHER'.
    """
    upper = narration.upper()
    for mode, keywords in TRANSACTION_MODE_PATTERNS:
        if any(kw in upper for kw in keywords):
            return mode
    return "OTHER"


def is_reversal(narration: str) -> bool:
    upper = narration.upper()
    return any(kw in upper for kw in REVERSAL_KEYWORDS)


def enrich_transactions(
    transactions: list[dict],
    aa_mode_override: bool = False,
) -> list[dict]:
    """
    Enrich raw transactions with derived fields:
    - transaction_mode
    - is_reversal

    If aa_mode_override=True, prefer the _aa_mode field set by the AA parser.
    """
    enriched = []
    for txn in transactions:
        narration = txn.get("narration") or ""
        mode = txn.get("_aa_mode") if aa_mode_override and txn.get("_aa_mode") else None
        if not mode:
            mode = derive_transaction_mode(narration)

        enriched.append({
            "date": txn.get("date"),
            "value_date": txn.get("value_date"),
            "narration": narration,
            "debit_amount": txn.get("debit_amount"),
            "credit_amount": txn.get("credit_amount"),
            "closing_balance": txn.get("closing_balance"),
            "transaction_mode": mode,
            "is_reversal": is_reversal(narration),
        })
    return enriched


def filter_by_period(
    transactions: list[dict],
    from_date: Optional[str],
    to_date: Optional[str],
) -> list[dict]:
    """
    Filter transactions to only those within [from_date, to_date].
    Both are ISO date strings (YYYY-MM-DD).
    None means unbounded.
    """
    if not from_date and not to_date:
        return transactions

    filtered = []
    for txn in transactions:
        d = txn.get("date")
        if d is None:
            continue
        if from_date and d < from_date:
            continue
        if to_date and d > to_date:
            continue
        filtered.append(txn)
    return filtered


def build_metadata_out(
    header: dict,
    cross_validation: Optional[dict] = None,
    notes: Optional[list[str]] = None,
) -> dict:
    """
    Produce the statement_metadata output block.
    Optionally cross-validate against caller-supplied metadata.
    """
    out = {
        "account_holder_name": header.get("account_holder_name"),
        "account_number": header.get("account_number"),
        "ifsc_code": header.get("ifsc_code"),
        "bank_name": header.get("bank_name"),
        "branch_name": header.get("branch_name"),
        "statement_period_from": header.get("statement_period_from"),
        "statement_period_to": header.get("statement_period_to"),
        "opening_balance": header.get("opening_balance"),
        "closing_balance": header.get("closing_balance"),
    }

    if cross_validation and notes is not None:
        if cross_validation.get("account_number") and out.get("account_number"):
            supplied = str(cross_validation["account_number"]).replace(" ", "")
            extracted = str(out["account_number"]).replace(" ", "")
            if supplied not in extracted and extracted not in supplied:
                notes.append(
                    f"CROSS-VALIDATION WARNING: Supplied account number '{supplied}' "
                    f"does not match extracted '{extracted}'"
                )
        if cross_validation.get("bank_name") and out.get("bank_name"):
            if cross_validation["bank_name"].upper() not in (out["bank_name"] or "").upper():
                notes.append(
                    f"CROSS-VALIDATION WARNING: Supplied bank '{cross_validation['bank_name']}' "
                    f"does not match extracted '{out['bank_name']}'"
                )

    return out
