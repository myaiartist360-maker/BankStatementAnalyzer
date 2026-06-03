"""
BSA Engine — Gambling Transaction Detector
"""

from __future__ import annotations
from collections import defaultdict
from config import settings
from lexicon import GAMBLING_REGEX


def detect_gambling(transactions: list[dict]) -> dict:
    """
    Returns:
        {
          count, total_amount,
          monthly_breakdown: [{month, amount, count}],
          instances: [{date, amount, narration}]
        }
    """
    instances: list[dict] = []
    monthly: dict[str, dict] = defaultdict(lambda: {"amount": 0.0, "count": 0})

    for t in transactions:
        narr = t.get("narration") or ""
        if not GAMBLING_REGEX.search(narr):
            continue

        amount = t.get("debit_amount") or t.get("credit_amount") or 0.0
        date_str = t.get("date", "")
        month = date_str[:7] if date_str else "unknown"

        instances.append({
            "date": date_str,
            "amount": amount,
            "narration": t.get("narration", ""),
        })
        monthly[month]["amount"] = round(monthly[month]["amount"] + amount, 2)
        monthly[month]["count"] += 1

    total = round(sum(i["amount"] for i in instances), 2)
    monthly_breakdown = [
        {"month": m, "amount": v["amount"], "count": v["count"]}
        for m, v in sorted(monthly.items())
    ]

    return {
        "count": len(instances),
        "total_amount": total,
        "monthly_breakdown": monthly_breakdown,
        "instances": instances,
    }
