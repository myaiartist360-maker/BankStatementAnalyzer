"""
BSA Engine — Round-Trip / Fund-Cycling Detector
Credits followed by equal debits (±2%) within 48 hours.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from config import settings


def detect_round_trips(transactions: list[dict]) -> dict:
    """
    For each credit, look for a debit within ROUND_TRIP_WINDOW_HOURS
    with amount within ±ROUND_TRIP_AMOUNT_TOLERANCE.

    Returns: {count, instances: [{credit_date, debit_date, amount, ...}]}
    """
    tol = settings.round_trip_amount_tolerance
    window_hours = settings.round_trip_window_hours

    credits = [t for t in transactions if t.get("credit_amount") is not None]
    debits  = [t for t in transactions if t.get("debit_amount") is not None]

    instances: list[dict] = []

    for credit in credits:
        c_amount = credit["credit_amount"]
        c_date = _parse_dt(credit.get("date", ""))
        if c_date is None:
            continue

        for debit in debits:
            d_amount = debit["debit_amount"]
            d_date = _parse_dt(debit.get("date", ""))
            if d_date is None:
                continue

            # Debit must come AFTER credit
            if d_date <= c_date:
                continue
            if (d_date - c_date) > timedelta(hours=window_hours):
                continue

            if c_amount == 0:
                continue
            rel_diff = abs(d_amount - c_amount) / c_amount
            if rel_diff <= tol:
                instances.append({
                    "credit_date": credit.get("date"),
                    "debit_date": debit.get("date"),
                    "amount": round((c_amount + d_amount) / 2, 2),
                    "credit_narration": credit.get("narration", ""),
                    "debit_narration": debit.get("narration", ""),
                })

    return {"count": len(instances), "instances": instances}


def _parse_dt(date_str: str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None
