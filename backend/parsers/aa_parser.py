"""
BSA Engine — RBI Account Aggregator JSON Parser
Parses FI Type: DEPOSIT payload per the AA framework standard.
"""

from __future__ import annotations
from typing import Any, Optional
from utils.helpers import parse_date, parse_amount, clean_narration, iso_date


def parse_aa_json(payload: Any) -> tuple[dict, list[dict], list[str]]:
    """
    Parse an RBI AA FIP payload.
    Supports both the nested FIDataHeader/Transactions structure
    and flat top-level arrays.

    Returns:
        (header, transactions, notes)
    """
    notes: list[str] = []
    header: dict = {}
    transactions: list[dict] = []

    if not isinstance(payload, dict):
        notes.append("AA JSON must be a dict at root level")
        return header, transactions, notes

    # ── Header extraction ─────────────────────────────────────────────────────
    # Try common AA response structures
    summary = (
        payload.get("Summary")
        or payload.get("summary")
        or payload.get("Profile", {}).get("Holders", {}).get("Holder", [{}])[0]
        or {}
    )
    if isinstance(summary, list):
        summary = summary[0] if summary else {}

    header["account_holder_name"] = (
        summary.get("name") or summary.get("Name") or summary.get("holderName")
    )
    header["account_number"] = (
        summary.get("accNo") or summary.get("accountNumber") or summary.get("maskedAccNumber")
    )
    header["ifsc_code"] = summary.get("ifscCode") or summary.get("IFSC")
    header["bank_name"] = (
        payload.get("fipId") or payload.get("FIPId") or summary.get("bank")
    )
    header["branch_name"] = summary.get("branch") or summary.get("Branch")

    # Opening / closing balance from Summary
    header["opening_balance"] = _safe_float(
        summary.get("openingBalance") or summary.get("OpeningBalance")
    )
    header["closing_balance"] = _safe_float(
        summary.get("closingBalance") or summary.get("ClosingBalance")
    )

    # Statement period
    header["statement_period_from"] = _safe_date(
        summary.get("startDate") or summary.get("StartDate") or summary.get("from")
    )
    header["statement_period_to"] = _safe_date(
        summary.get("endDate") or summary.get("EndDate") or summary.get("to")
    )

    # ── Transaction extraction ────────────────────────────────────────────────
    txn_array = (
        payload.get("Transactions", {}).get("Transaction")
        or payload.get("transactions")
        or payload.get("Transaction")
        or []
    )

    if isinstance(txn_array, dict):
        txn_array = [txn_array]

    if not txn_array:
        notes.append("No transactions found in AA JSON payload")
        return header, transactions, notes

    for raw in txn_array:
        if not isinstance(raw, dict):
            continue

        txn_type = str(raw.get("type", raw.get("txnType", "DEBIT"))).upper()
        amount = _safe_float(raw.get("amount") or raw.get("Amount"))
        narration = clean_narration(
            str(raw.get("narration") or raw.get("Narration") or raw.get("remarks") or "")
        )
        date_raw = raw.get("valueDate") or raw.get("transactionDate") or raw.get("date") or ""
        d = parse_date(str(date_raw)) if date_raw else None
        bal = _safe_float(raw.get("currentBalance") or raw.get("balance") or raw.get("closingBalance"))
        mode = raw.get("mode") or raw.get("transactionMode") or ""

        transactions.append({
            "date": iso_date(d) if d else None,
            "value_date": None,
            "narration": narration,
            "debit_amount": amount if txn_type == "DEBIT" else None,
            "credit_amount": amount if txn_type == "CREDIT" else None,
            "closing_balance": bal,
            "_aa_mode": mode.upper() if mode else None,
        })

    notes.append(f"Extracted {len(transactions)} transaction(s) from AA JSON")
    return header, transactions, notes


def _safe_float(val: Any) -> Optional[float]:
    try:
        return round(float(val), 2) if val is not None else None
    except (ValueError, TypeError):
        return None


def _safe_date(val: Any) -> Optional[str]:
    if not val:
        return None
    d = parse_date(str(val))
    return iso_date(d) if d else str(val)
