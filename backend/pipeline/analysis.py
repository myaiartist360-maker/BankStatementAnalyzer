"""
BSA Engine — Step 4: Financial Analysis Computation
Computes all metrics over the analysis period.
"""

from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

from utils.helpers import parse_date, iso_date, date_range, month_key, round2
from config import (
    settings,
    INWARD_BOUNCE_PATTERNS,
    OUTWARD_BOUNCE_PATTERNS,
    EMI_BOUNCE_PATTERNS,
)
from detectors.salary_detector import detect_salary
from detectors.emi_detector import detect_emi, detect_emi_bounces
from detectors.gambling_detector import detect_gambling
from detectors.crypto_detector import detect_crypto
from detectors.roundtrip_detector import detect_round_trips


def compute_analysis(
    transactions: list[dict],
    from_date: Optional[str],
    to_date: Optional[str],
    notes: list[str],
) -> dict:
    """
    Master analysis function. Returns a dict matching the full output contract.
    """

    # ── Date bounds ──────────────────────────────────────────────────────────
    if transactions:
        dates = [t["date"] for t in transactions if t.get("date")]
        period_from = from_date or (min(dates) if dates else None)
        period_to   = to_date   or (max(dates) if dates else None)
    else:
        period_from = from_date
        period_to = to_date

    # ── Transaction aggregates ────────────────────────────────────────────────
    credit_txns  = [t for t in transactions if t.get("credit_amount") is not None]
    debit_txns   = [t for t in transactions if t.get("debit_amount")  is not None]
    reversal_txns = [t for t in transactions if t.get("is_reversal")]

    total_credit = round2(sum(t["credit_amount"] for t in credit_txns)) or 0.0
    total_debit  = round2(sum(t["debit_amount"]  for t in debit_txns))  or 0.0

    # ── Monthly breakdowns ────────────────────────────────────────────────────
    monthly_credits = _monthly_breakdown(credit_txns, "credit_amount")
    monthly_debits  = _monthly_breakdown(debit_txns,  "debit_amount")

    avg_monthly_credit = (
        round2(sum(m["amount"] for m in monthly_credits) / len(monthly_credits))
        if monthly_credits else 0.0
    )
    avg_monthly_debit = (
        round2(sum(m["amount"] for m in monthly_debits) / len(monthly_debits))
        if monthly_debits else 0.0
    )

    # ── Largest single credit ─────────────────────────────────────────────────
    largest_credit = None
    if credit_txns:
        best = max(credit_txns, key=lambda t: t["credit_amount"])
        largest_credit = {
            "amount": best["credit_amount"],
            "date": best.get("date"),
            "narration": best.get("narration"),
        }

    # ── EOD Balance time-series ───────────────────────────────────────────────
    eod_series, min_eod, max_eod, avg_eod = _compute_eod_balance(
        transactions, period_from, period_to, notes
    )

    # ── Months below MAB ─────────────────────────────────────────────────────
    months_below_mab = _count_months_below_mab(eod_series)

    # ── Balance utilisation ratio ─────────────────────────────────────────────
    if avg_eod and avg_monthly_debit:
        balance_util = round2(avg_eod / (avg_eod + avg_monthly_debit))
    else:
        balance_util = None

    # ── Bounce Analysis ───────────────────────────────────────────────────────
    bounce_analysis = _compute_bounce_analysis(transactions)
    emi_bounce = detect_emi_bounces(transactions)

    # ── High-value cash withdrawals ───────────────────────────────────────────
    hv_cash = _compute_high_value_cash(transactions)

    # ── Detectors ─────────────────────────────────────────────────────────────
    salary      = detect_salary(transactions)
    emi         = detect_emi(transactions)
    gambling    = detect_gambling(transactions)
    crypto      = detect_crypto(transactions)
    round_trips = detect_round_trips(transactions)

    # ── Obligation indicators ─────────────────────────────────────────────────
    loan_kw = ["EMI", "LOAN", "REPAY", "PRINCIPAL", "INTEREST PAID"]
    ins_kw  = ["LIC", "INSURANCE", "PREMIUM", "LIFE INS", "HEALTH INS"]
    util_kw = ["ELECTRICITY", "WATER", "GAS", "BROADBAND", "MOBILE RECHARGE",
                "POSTPAID", "TATA POWER", "BESCOM", "MSEDCL", "BSES"]

    loan_detected  = any(kw in (t.get("narration") or "").upper() for t in transactions for kw in loan_kw)
    ins_detected   = any(kw in (t.get("narration") or "").upper() for t in transactions for kw in ins_kw)
    util_count     = sum(
        1 for t in transactions
        if any(kw in (t.get("narration") or "").upper() for kw in util_kw)
    )

    # ── High-risk flags ────────────────────────────────────────────────────────
    flags = _build_flags(
        bounce_analysis,
        emi_bounce,
        gambling,
        crypto,
        round_trips,
        hv_cash,
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    summary = {
        "total_transactions": len(transactions),
        "total_credit_transactions": len(credit_txns),
        "total_debit_transactions": len(debit_txns),
        "total_reversal_transactions": len(reversal_txns),
        "total_credit_amount": total_credit,
        "total_debit_amount": total_debit,
        "average_eod_balance": avg_eod or 0.0,
        "minimum_eod_balance": min_eod,
        "maximum_eod_balance": max_eod,
        "average_monthly_credit": avg_monthly_credit,
        "average_monthly_debit": avg_monthly_debit,
        "months_below_minimum_balance": months_below_mab,
        "balance_utilisation_ratio": balance_util,
        "inward_cheque_bounces": bounce_analysis["inward"]["count"],
        "outward_cheque_bounces": bounce_analysis["outward"]["count"],
        "emi_bounces": emi_bounce["count"],
        "gambling_transaction_count": gambling["count"],
        "gambling_total_amount": gambling["total_amount"],
        "salary_identified": salary["identified"],
        "probable_salary_amount": salary.get("probable_amount"),
        "largest_single_credit": largest_credit,
    }

    return {
        "analysis_period": {"from": period_from, "to": period_to},
        "summary": summary,
        "monthly_credits": monthly_credits,
        "monthly_debits": monthly_debits,
        "salary_analysis": salary,
        "emi_analysis": emi,
        "bounce_analysis": {
            "inward_cheque_bounces": bounce_analysis["inward"],
            "outward_cheque_bounces": bounce_analysis["outward"],
            "emi_bounces": emi_bounce,
        },
        "gambling_analysis": gambling,
        "crypto_analysis": crypto,
        "round_trip_analysis": round_trips,
        "high_value_cash_analysis": hv_cash,
        "high_risk_flags": flags,
        "obligation_indicators": {
            "loan_repayments_detected": loan_detected,
            "insurance_premiums_detected": ins_detected,
            "recurring_utility_payments": util_count,
        },
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _monthly_breakdown(txns: list[dict], amount_field: str) -> list[dict]:
    monthly: dict[str, dict] = defaultdict(lambda: {"amount": 0.0, "count": 0})
    for t in txns:
        d = t.get("date", "")
        mk = d[:7] if d and len(d) >= 7 else "unknown"
        monthly[mk]["amount"] = round(monthly[mk]["amount"] + (t.get(amount_field) or 0.0), 2)
        monthly[mk]["count"] += 1
    return [
        {"month": m, "amount": v["amount"], "count": v["count"]}
        for m, v in sorted(monthly.items())
    ]


def _compute_eod_balance(
    transactions: list[dict],
    from_date: Optional[str],
    to_date: Optional[str],
    notes: list[str],
) -> tuple[dict, Optional[dict], Optional[dict], Optional[float]]:
    """
    Build a daily EOD balance map by carrying forward the last known balance.
    Returns: (eod_map, min_point, max_point, average)
    """
    if not transactions:
        return {}, None, None, None

    # Build date→last_balance map from transactions
    date_balance: dict[str, float] = {}
    for t in transactions:
        d = t.get("date")
        bal = t.get("closing_balance")
        if d and bal is not None:
            date_balance[d] = bal

    if not date_balance:
        notes.append("No closing balance data available for EOD calculation")
        return {}, None, None, None

    start = parse_date(from_date) if from_date else parse_date(min(date_balance))
    end   = parse_date(to_date)   if to_date   else parse_date(max(date_balance))

    if not start or not end:
        return {}, None, None, None

    eod: dict[str, float] = {}
    last_known = None

    for day in date_range(start, end):
        day_str = iso_date(day)
        if day_str in date_balance:
            last_known = date_balance[day_str]
        if last_known is not None:
            eod[day_str] = last_known

    if not eod:
        return {}, None, None, None

    vals = list(eod.values())
    avg = round2(sum(vals) / len(vals))

    min_date = min(eod, key=eod.get)
    max_date = max(eod, key=eod.get)

    return (
        eod,
        {"amount": round2(eod[min_date]), "date": min_date},
        {"amount": round2(eod[max_date]), "date": max_date},
        avg,
    )


def _count_months_below_mab(eod: dict) -> int:
    threshold = settings.min_balance_threshold
    monthly: dict[str, list[float]] = defaultdict(list)
    for d, bal in eod.items():
        monthly[d[:7]].append(bal)
    return sum(
        1 for vals in monthly.values()
        if vals and (sum(vals) / len(vals)) < threshold
    )


def _compute_bounce_analysis(transactions: list[dict]) -> dict:
    inward: list[dict] = []
    outward: list[dict] = []

    for t in transactions:
        narr = (t.get("narration") or "").upper()
        amount = t.get("debit_amount") or t.get("credit_amount") or 0.0
        inst = {"date": t.get("date", ""), "amount": amount, "narration": t.get("narration", "")}

        if any(p in narr for p in INWARD_BOUNCE_PATTERNS):
            inward.append(inst)
        elif any(p in narr for p in OUTWARD_BOUNCE_PATTERNS):
            outward.append(inst)

    return {
        "inward": {
            "count": len(inward),
            "total_amount": round2(sum(i["amount"] for i in inward)) or 0.0,
            "instances": inward,
        },
        "outward": {
            "count": len(outward),
            "total_amount": round2(sum(i["amount"] for i in outward)) or 0.0,
            "instances": outward,
        },
    }


def _compute_high_value_cash(transactions: list[dict]) -> dict:
    threshold = settings.high_value_cash_threshold
    daily: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "txns": []})

    for t in transactions:
        mode = t.get("transaction_mode", "")
        debit = t.get("debit_amount")
        if mode not in ("ATM", "CASH") or debit is None:
            continue
        d = t.get("date", "")
        daily[d]["total"] = round(daily[d]["total"] + debit, 2)
        daily[d]["txns"].append({"amount": debit, "narration": t.get("narration", "")})

    instances = []
    for day, data in sorted(daily.items()):
        if data["total"] >= threshold:
            instances.append({
                "date": day,
                "total_amount": data["total"],
                "transactions": data["txns"],
            })

    return {
        "count": len(instances),
        "total_amount": round2(sum(i["total_amount"] for i in instances)) or 0.0,
        "instances": instances,
    }


def _build_flags(
    bounce_analysis: dict,
    emi_bounce: dict,
    gambling: dict,
    crypto: dict,
    round_trips: dict,
    hv_cash: dict,
) -> list[dict]:
    flags = []

    # Inward bounces
    if bounce_analysis["inward"]["count"] > 0:
        total = bounce_analysis["inward"]["total_amount"]
        flags.append({
            "flag": "INWARD_CHEQUE_BOUNCE",
            "severity": "HIGH" if total > 50_000 else "MEDIUM",
            "detail": f"{bounce_analysis['inward']['count']} inward cheque bounce(s) totalling ₹{total:,.2f}",
        })

    # Outward bounces
    if bounce_analysis["outward"]["count"] > 0:
        total = bounce_analysis["outward"]["total_amount"]
        flags.append({
            "flag": "OUTWARD_CHEQUE_BOUNCE",
            "severity": "HIGH" if total > 50_000 else "MEDIUM",
            "detail": f"{bounce_analysis['outward']['count']} outward cheque bounce(s) totalling ₹{total:,.2f}",
        })

    # EMI bounces
    if emi_bounce["count"] > 0:
        flags.append({
            "flag": "EMI_NACH_BOUNCE",
            "severity": "MEDIUM",
            "detail": f"{emi_bounce['count']} EMI/NACH bounce(s) detected",
        })

    # Gambling
    if gambling["count"] > 0:
        sev = "HIGH" if gambling["total_amount"] > 50_000 else "LOW"
        flags.append({
            "flag": "GAMBLING_TRANSACTIONS",
            "severity": sev,
            "detail": (
                f"{gambling['count']} gambling transaction(s) totalling "
                f"₹{gambling['total_amount']:,.2f}"
            ),
        })

    # Crypto
    if crypto["count"] > 0:
        flags.append({
            "flag": "CRYPTO_EXCHANGE_TRANSACTIONS",
            "severity": "MEDIUM",
            "detail": f"{crypto['count']} crypto exchange transaction(s) totalling ₹{crypto['total_amount']:,.2f}",
        })

    # Round-trip
    if round_trips["count"] > 0:
        flags.append({
            "flag": "ROUND_TRIP_FUND_CYCLING",
            "severity": "MEDIUM",
            "detail": f"{round_trips['count']} potential round-trip fund cycling pair(s) detected",
        })

    # High-value cash
    if hv_cash["count"] > 0:
        flags.append({
            "flag": "HIGH_VALUE_CASH_WITHDRAWAL",
            "severity": "HIGH" if hv_cash["total_amount"] > 1_00_000 else "MEDIUM",
            "detail": (
                f"{hv_cash['count']} day(s) with cash withdrawals over ₹"
                f"{settings.high_value_cash_threshold:,.0f}"
            ),
        })

    return flags
