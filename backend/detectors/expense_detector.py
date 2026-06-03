"""
BSA Engine — Expense & Obligation Categorisation

Mirror of the income detector for the debit side. Classifies every outflow into
an obligation / spend category using the master narration lexicon, separates
recurring fixed commitments from discretionary spend, and sums the genuine
credit obligations that feed FOIR / debt-burden in the credit assessment.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional

from utils.helpers import round2
from lexicon import classify_expense, detect_channel, FOIR_OBLIGATION_KEYS


_CHANNEL_LABEL = {
    "atm": "ATM / Cash Withdrawal",
    "pos": "Card / POS Spend",
    "upi": "UPI / Wallet Spend",
    "cash": "Cash Payments",
    "cheque": "Cheque / Clearing",
    "transfer": "Transfers Out",
    "dd_sweep": "DD / Sweep",
    "aeps": "AEPS / BC Cash-out",
}


def _categorise(txn: dict) -> tuple[str, str]:
    narr = txn.get("narration") or ""
    hit = classify_expense(narr)
    if hit:
        key, label = hit
        return key.upper(), label
    channel = detect_channel(narr)
    if channel and channel in _CHANNEL_LABEL:
        return channel.upper(), _CHANNEL_LABEL[channel]
    return "OTHER", "Other Payments"


def analyze_expenses(transactions: list[dict]) -> dict:
    """Build the expense_analysis block (parallels income_analysis)."""
    debits = [t for t in transactions if t.get("debit_amount")]
    if not debits:
        return {
            "total_expense": 0.0,
            "monthly_obligations": 0.0,
            "fixed_obligation_share": 0.0,
            "monthly_breakdown": [],
            "categories": [],
        }

    total_expense = round2(sum(t["debit_amount"] for t in debits)) or 0.0
    all_months = sorted({(t.get("date") or "")[:7] for t in debits if t.get("date")})
    n_months = max(len(all_months), 1)

    grouped: dict[str, dict] = defaultdict(lambda: {"label": "", "txns": [], "months": set()})
    for t in debits:
        key, label = _categorise(t)
        g = grouped[key]
        g["label"] = label
        g["txns"].append(t)
        mk = (t.get("date") or "")[:7]
        if mk:
            g["months"].add(mk)

    categories: list[dict] = []
    monthly_obligations = 0.0
    for key, g in grouped.items():
        txns = g["txns"]
        amt = round2(sum(t["debit_amount"] for t in txns)) or 0.0
        months_present = len(g["months"])
        recurring = months_present >= max(2, (n_months + 1) // 2)
        monthly_avg = round2(amt / n_months) or 0.0
        is_obligation = key.lower() in FOIR_OBLIGATION_KEYS
        if is_obligation:
            monthly_obligations += monthly_avg

        categories.append({
            "category": key,
            "label": g["label"],
            "count": len(txns),
            "total_amount": amt,
            "monthly_average": monthly_avg,
            "months_present": months_present,
            "recurring": recurring,
            "is_fixed_obligation": is_obligation,
            "share_pct": round2(amt / total_expense * 100) if total_expense else 0.0,
            "transactions": sorted(
                ({"date": t.get("date"), "amount": t["debit_amount"],
                  "narration": t.get("narration", ""), "mode": t.get("transaction_mode")}
                 for t in txns),
                key=lambda x: x["amount"], reverse=True,
            ),
        })

    categories.sort(key=lambda c: c["total_amount"], reverse=True)

    monthly: dict[str, dict] = defaultdict(lambda: {"amount": 0.0, "count": 0})
    for t in debits:
        mk = (t.get("date") or "")[:7]
        if mk:
            monthly[mk]["amount"] = round(monthly[mk]["amount"] + t["debit_amount"], 2)
            monthly[mk]["count"] += 1
    monthly_breakdown = [
        {"month": m, "amount": monthly[m]["amount"], "count": monthly[m]["count"]}
        for m in sorted(monthly)
    ]

    fixed_total = sum(c["total_amount"] for c in categories if c["is_fixed_obligation"])

    return {
        "total_expense": total_expense,
        "monthly_obligations": round2(monthly_obligations) or 0.0,
        "fixed_obligation_share": round2(fixed_total / total_expense * 100) if total_expense else 0.0,
        "monthly_breakdown": monthly_breakdown,
        "categories": categories,
    }
