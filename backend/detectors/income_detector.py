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

# Honorifics stripped before grouping so "Mr Sachin Gupta" == "SACHIN GUPTA".
_HONORIFICS = {"MR", "MRS", "MS", "SHRI", "SMT", "DR", "SRI", "M S", "MS S"}

# Bank/PSP handles that appear in the field right after the name.
_BANK_HANDLES = {
    "IOB", "KKB", "IDI", "UTI", "YESB", "BAR", "IND", "RATN", "IDFB", "IDIB",
    "PUN", "HDFC", "ICIC", "SBIN", "AXIS", "KKBK", "PUNB", "UTIB", "YES", "PUNB",
    "CNRB", "BARB", "KVBL", "FDRL", "INDB",
}

# Note / filler tokens that are never a payer name.
_NOTE_TOKENS = {
    "", "-", "NA", "SENT", "USING", "USIN", "US", "FROM", "PAYMENT", "PAYME",
    "FUND", "FUNDT", "TRANSFER", "REF", "ONLINE", "INSTANT PAYMENT", "IMMEDIATE",
    "RECD", "RECEIVED", "PAYMENT F", "SENT US", "SENT FROM", "PAYMENT FROM",
}


def _clean_name(s: str) -> str:
    """Normalise a raw name fragment: drop non-alpha, honorifics, collapse spaces."""
    s = re.sub(r"[^A-Za-z ]", " ", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    words = [w for w in s.split(" ") if w.upper() not in _HONORIFICS]
    return " ".join(words).strip()


def _extract_counterparty(narration: str) -> Optional[str]:
    """
    Pull the payer name out of a structured Indian-bank narration using the
    field position for each rail (more reliable than a longest-token heuristic):

      UPI:  UPI / <ref> / CR|DR / <NAME> / <handle> / <note>   -> field after CR/DR
      IMPS: IMPS / <ref> / <NAME> / <bankcode> / <acct> / <note> -> field 2
      NEFT: NEFT / <ref> / <NAME> / ...                          -> field 2

    Returns a Title-Cased display name, or None when no clean name is present
    (e.g. cash deposits, charges, interest).
    """
    if not narration:
        return None
    parts = [p.strip() for p in narration.split("/")]
    up = narration.strip().upper()
    name: Optional[str] = None

    if up.startswith("UPI"):
        for i, p in enumerate(parts):
            if p.upper() in ("CR", "DR") and i + 1 < len(parts):
                name = parts[i + 1]
                break
        if name is None and len(parts) >= 4:
            name = parts[3]
    elif up.startswith(("IMPS", "NEFT", "RTGS", "IFT")) and len(parts) >= 3:
        name = parts[2]

    name = _clean_name(name or "")
    if not name:
        return None
    upper = name.upper()
    if upper in _BANK_HANDLES or upper in _NOTE_TOKENS or len(upper) < 3:
        return None
    return name.title()


def _merge_subset_names(payers: dict[str, dict]) -> dict[str, dict]:
    """
    Fold partial names into their fuller form, e.g. 'SACHIN' -> 'SACHIN GUPTA',
    when one name's word-set is a strict subset of another's. The longer name's
    display is kept; counts and totals are summed.
    """
    keys = sorted(payers.keys(), key=lambda k: len(k.split()), reverse=True)
    canonical: list[str] = []
    remap: dict[str, str] = {}
    for k in keys:
        ktokens = set(k.split())
        target = None
        for c in canonical:
            ctokens = set(c.split())
            if ktokens < ctokens or ktokens == ctokens:
                target = c
                break
        if target:
            remap[k] = target
        else:
            canonical.append(k)
            remap[k] = k

    merged: dict[str, dict] = {}
    for k, v in payers.items():
        tgt = remap[k]
        m = merged.setdefault(tgt, {"display": payers[tgt]["display"], "count": 0, "total": 0.0})
        m["count"] += v["count"]
        m["total"] = round(m["total"] + v["total"], 2)
    return merged


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
    # Grouped by an UPPERCASE key so name variants merge; a Title-Case display
    # name is kept for presentation. Cash deposits have no external payer.
    payers: dict[str, dict] = defaultdict(lambda: {"display": "", "count": 0, "total": 0.0})
    for t in credits:
        if _categorise(t)[0] == "CASH_DEPOSIT":
            continue
        name = _extract_counterparty(t.get("narration", ""))
        if not name:
            continue
        key = name.upper()
        payers[key]["display"] = name
        payers[key]["count"] += 1
        payers[key]["total"] = round(payers[key]["total"] + t["credit_amount"], 2)
    payers = _merge_subset_names(payers)
    top_payers = sorted(
        ({"name": v["display"], "count": v["count"], "total_amount": v["total"]}
         for v in payers.values()),
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
