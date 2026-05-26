"""
BSA Engine — EMI Detector
Identifies recurring debit patterns (NACH/ECS/SI) and bounce events.
"""

from __future__ import annotations
from collections import defaultdict
from utils.helpers import parse_date
from config import settings, EMI_BOUNCE_PATTERNS


EMI_MODES = {"NACH", "ECS", "SI"}


def detect_emi(transactions: list[dict]) -> dict:
    """
    Returns:
        {
          count, probable_emi_amount, lender_hint,
          instances: [{date, amount, narration}, ...]
        }
    """
    # Filter debits with EMI-relevant modes
    emi_debits = [
        t for t in transactions
        if t.get("debit_amount") is not None
        and t.get("transaction_mode") in EMI_MODES
    ]

    if not emi_debits:
        return {
            "count": 0,
            "probable_emi_amount": None,
            "lender_hint": None,
            "instances": [],
        }

    # Group by (amount ±5%, day-of-month ±3)
    tol = settings.emi_amount_tolerance
    day_tol = settings.emi_day_tolerance
    clusters: list[list[dict]] = []

    for txn in emi_debits:
        amount = txn["debit_amount"]
        d = parse_date(txn["date"])
        if not d:
            continue
        placed = False
        for cluster in clusters:
            ref = cluster[0]
            ref_d = parse_date(ref["date"])
            if not ref_d:
                continue
            ref_amt = ref["debit_amount"]
            amt_ok = abs(amount - ref_amt) / max(ref_amt, 1) <= tol
            day_ok = abs(d.day - ref_d.day) <= day_tol
            if amt_ok and day_ok:
                cluster.append(txn)
                placed = True
                break
        if not placed:
            clusters.append([txn])

    # Keep clusters spanning ≥2 months
    valid_clusters = []
    for cluster in clusters:
        months = set()
        for t in cluster:
            d = parse_date(t["date"])
            if d:
                months.add(f"{d.year}-{d.month:02d}")
        if len(months) >= 2:
            valid_clusters.append(cluster)

    if not valid_clusters:
        return {
            "count": 0,
            "probable_emi_amount": None,
            "lender_hint": None,
            "instances": [],
        }

    # Pick largest cluster
    best = max(valid_clusters, key=len)
    amounts = [t["debit_amount"] for t in best]
    median_emi = sorted(amounts)[len(amounts) // 2]

    # Lender hint: common words in narrations
    narrations = [t.get("narration", "") for t in best]
    lender_hint = _extract_lender(narrations)

    instances = [
        {"date": t["date"], "amount": t["debit_amount"], "narration": t.get("narration", "")}
        for t in best
    ]

    return {
        "count": len(instances),
        "probable_emi_amount": round(median_emi, 2),
        "lender_hint": lender_hint,
        "instances": instances,
    }


def detect_emi_bounces(transactions: list[dict]) -> dict:
    """
    Identify NACH/ECS/SI reversal events.
    Returns: {count, instances: [{date, amount, narration}]}
    """
    bounces = []
    for t in transactions:
        narr = (t.get("narration") or "").upper()
        if any(pat in narr for pat in EMI_BOUNCE_PATTERNS):
            amount = t.get("debit_amount") or t.get("credit_amount") or 0.0
            bounces.append({
                "date": t.get("date", ""),
                "amount": amount,
                "narration": t.get("narration", ""),
            })
    return {"count": len(bounces), "instances": bounces}


def _extract_lender(narrations: list[str]) -> str | None:
    """Extract a likely lender name fragment from narrations."""
    from collections import Counter
    words: list[str] = []
    for n in narrations:
        parts = n.upper().split()
        words.extend(p for p in parts if len(p) > 3 and not p.isdigit())
    if not words:
        return None
    common = Counter(words).most_common(3)
    return " ".join(w for w, _ in common) or None
