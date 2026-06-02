"""
BSA Engine — Income Categorisation & Source Detection

Treats salary as one category of *income* and classifies every credit into an
income type, identifies the counterparties (payers), separates regular/recurring
income from one-off inflows, and reports the contributing transactions so each
figure can be traced back to its source rows.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Optional

from utils.helpers import parse_date, round2


# Category → (label, narration keywords). Order matters: first match wins.
INCOME_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("SALARY",            "Salary / Payroll",        ("salary", "sal cr", "payroll", "wages", "stipend", "remuneration", "sal ")),
    ("INTEREST",          "Interest Income",         ("interest", "int.pd", "int cr", "int credit", "int pd")),
    ("INVESTMENT",        "Investments & Maturity",  ("dividend", "maturity", "redemption", "redeem", "mutual fund", " mf ", "fd ", "rd ", "sip", "tds refund")),
    ("RENTAL",            "Rental Income",           ("rent",)),
    ("REFUND",            "Refunds & Cashback",      ("refund", "cashback", "reversal", "reimbursement", "rev ")),
    ("CASH_DEPOSIT",      "Cash Deposits",           ("cash dep", "cash deposit", "cdm", "by cash", "cash/")),
    ("LOAN_DISBURSAL",    "Loan Disbursal",          ("loan disb", "disbursement", "loan credit", "od limit")),
]

# Modes that, for credits, usually represent peer/business transfers in.
TRANSFER_MODES = {"UPI", "IMPS", "NEFT", "RTGS"}

_STOPWORDS = {
    "UPI", "IMPS", "NEFT", "RTGS", "CR", "DR", "REF", "PAYMENT", "PAYME", "FROM",
    "SENT", "USING", "FUND", "FUNDT", "TRANSFER", "ACH", "BANK", "LTD", "PVT",
    "INDIA", "ONLINE", "RECD", "RECEIVED", "NA", "YES", "BAR", "IOB", "IDFB",
    "HDFC", "ICIC", "SBIN", "AXIS", "KKBK", "PUNB", "UTIB",
}


def _extract_counterparty(narration: str) -> Optional[str]:
    """
    Pull a likely payer name out of a UPI/IMPS/NEFT narration.
    e.g. 'IMPS/517814292140/SARATHI/IDIB/XXXXXX4164/Fund' -> 'SARATHI'
         'NEFT-AXIS-ACME CORP SALARY' -> 'ACME CORP SALARY'
    """
    if not narration:
        return None
    parts = re.split(r"[\/\-\|]", narration.upper())
    candidates: list[str] = []
    for p in parts:
        token = re.sub(r"[^A-Z &.]", " ", p).strip()
        token = re.sub(r"\s+", " ", token)
        if not token:
            continue
        words = [w for w in token.split(" ") if len(w) >= 3 and w not in _STOPWORDS]
        if words:
            candidates.append(" ".join(words))
    if not candidates:
        return None
    # Prefer the longest meaningful candidate (usually the actual name).
    return max(candidates, key=len).title()


def _categorise(txn: dict) -> tuple[str, str]:
    narr = (txn.get("narration") or "").lower()
    for cat, label, keywords in INCOME_RULES:
        if any(kw in narr for kw in keywords):
            return cat, label
    mode = txn.get("transaction_mode")
    if mode in TRANSFER_MODES:
        return "TRANSFER_IN", "Transfers In (UPI/IMPS/NEFT)"
    return "OTHER", "Other Credits"


def analyze_income(transactions: list[dict], salary: Optional[dict] = None) -> dict:
    """
    Build the income_analysis block.

    Returns:
        {
          total_income, monthly_breakdown, regular_monthly_income,
          regular_income_share, sources: [ {category,...,transactions:[...]} ],
          top_payers: [ {name, count, total_amount} ]
        }
    """
    credits = [t for t in transactions if t.get("credit_amount")]
    if not credits:
        return {
            "total_income": 0.0,
            "regular_monthly_income": 0.0,
            "regular_income_share": 0.0,
            "monthly_breakdown": [],
            "sources": [],
            "top_payers": [],
        }

    total_income = round2(sum(t["credit_amount"] for t in credits)) or 0.0

    # Distinct months in the statement (for monthly averaging / recurrence).
    all_months = sorted({(t.get("date") or "")[:7] for t in credits if t.get("date")})
    n_months = max(len(all_months), 1)

    # Group credits by category.
    grouped: dict[str, dict] = defaultdict(lambda: {"label": "", "txns": [], "months": set()})
    for t in credits:
        cat, label = _categorise(t)
        g = grouped[cat]
        g["label"] = label
        g["txns"].append(t)
        mk = (t.get("date") or "")[:7]
        if mk:
            g["months"].add(mk)

    sources: list[dict] = []
    regular_monthly = 0.0
    for cat, g in grouped.items():
        txns = g["txns"]
        amt = round2(sum(t["credit_amount"] for t in txns)) or 0.0
        months_present = len(g["months"])
        # "Recurring" = appears in at least half the statement's months (min 2).
        recurring = months_present >= max(2, (n_months + 1) // 2)
        monthly_avg = round2(amt / n_months) or 0.0

        # Salary is authoritative if the dedicated detector identified it.
        if cat == "SALARY" and salary and salary.get("identified"):
            recurring = True

        if recurring:
            regular_monthly += monthly_avg

        sources.append({
            "category": cat,
            "label": g["label"],
            "count": len(txns),
            "total_amount": amt,
            "monthly_average": monthly_avg,
            "months_present": months_present,
            "recurring": recurring,
            "share_pct": round2(amt / total_income * 100) if total_income else 0.0,
            "transactions": sorted(
                ({"date": t.get("date"), "amount": t["credit_amount"],
                  "narration": t.get("narration", ""), "mode": t.get("transaction_mode")}
                 for t in txns),
                key=lambda x: x["amount"], reverse=True,
            ),
        })

    sources.sort(key=lambda s: s["total_amount"], reverse=True)

    # Monthly income trend.
    monthly: dict[str, dict] = defaultdict(lambda: {"amount": 0.0, "count": 0})
    for t in credits:
        mk = (t.get("date") or "")[:7]
        if mk:
            monthly[mk]["amount"] = round(monthly[mk]["amount"] + t["credit_amount"], 2)
            monthly[mk]["count"] += 1
    monthly_breakdown = [
        {"month": m, "amount": monthly[m]["amount"], "count": monthly[m]["count"]}
        for m in sorted(monthly)
    ]

    # Top payers / income sources by counterparty.
    payers: dict[str, dict] = defaultdict(lambda: {"count": 0, "total": 0.0})
    for t in credits:
        name = _extract_counterparty(t.get("narration", ""))
        if not name:
            continue
        payers[name]["count"] += 1
        payers[name]["total"] = round(payers[name]["total"] + t["credit_amount"], 2)
    top_payers = sorted(
        ({"name": k, "count": v["count"], "total_amount": v["total"]} for k, v in payers.items()),
        key=lambda x: x["total_amount"], reverse=True,
    )[:10]

    return {
        "total_income": total_income,
        "regular_monthly_income": round2(regular_monthly) or 0.0,
        "regular_income_share": round2(regular_monthly * n_months / total_income * 100) if total_income else 0.0,
        "monthly_breakdown": monthly_breakdown,
        "sources": sources,
        "top_payers": top_payers,
    }
