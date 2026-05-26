"""
BSA Engine — Salary Detector
Identifies probable salary credits using recurring pattern matching.
"""

from __future__ import annotations
from collections import defaultdict
from datetime import date
from typing import Optional
from utils.helpers import parse_date, last_n_working_days
from config import settings


SALARY_MODES = {"NEFT", "IMPS", "NACH"}


def detect_salary(transactions: list[dict]) -> dict:
    """
    Returns:
        {
          "identified": bool,
          "probable_amount": float | None,
          "credit_dates": [str, ...]
        }
    """
    # Filter: credits only, salary-relevant modes
    candidates = [
        t for t in transactions
        if t.get("credit_amount") is not None
        and t.get("transaction_mode") in SALARY_MODES
    ]

    if len(candidates) < settings.salary_min_months:
        return {"identified": False, "probable_amount": None, "credit_dates": []}

    # Group by month
    by_month: dict[str, list[float]] = defaultdict(list)
    date_map: dict[str, list[str]] = defaultdict(list)
    for t in candidates:
        d = parse_date(t["date"])
        if not d:
            continue
        mk = f"{d.year}-{d.month:02d}"
        by_month[mk].append(t["credit_amount"])
        date_map[mk].append(t["date"])

    months = sorted(by_month.keys())
    if len(months) < settings.salary_min_months:
        return {"identified": False, "probable_amount": None, "credit_dates": []}

    # Find a candidate base amount: median across all monthly credits
    all_amounts = [a for m in months for a in by_month[m]]
    all_amounts_sorted = sorted(all_amounts)
    mid = len(all_amounts_sorted) // 2
    median_amount = all_amounts_sorted[mid]

    tol = settings.salary_amount_tolerance

    # Check: each month has at least one credit within ±10% of median
    # arriving on day 1–10 OR last N working days
    matching_months: list[tuple[str, float]] = []
    for month in months:
        year_m, mon = map(int, month.split("-"))
        last_days = last_n_working_days(year_m, mon, settings.salary_last_working_day_buffer)
        found = False
        for amount, txn_date_str in zip(by_month[month], date_map[month]):
            d = parse_date(txn_date_str)
            if not d:
                continue
            amount_ok = abs(amount - median_amount) / max(median_amount, 1) <= tol
            day_ok = (
                settings.salary_day_start <= d.day <= settings.salary_day_end
                or d.day in last_days
            )
            if amount_ok and day_ok:
                found = True
                break
        if found:
            matching_months.append(month)

    if len(matching_months) < settings.salary_min_months:
        return {"identified": False, "probable_amount": None, "credit_dates": []}

    # Collect the exact credit dates
    credit_dates = []
    for month in matching_months:
        year_m, mon = map(int, month.split("-"))
        last_days = last_n_working_days(year_m, mon, settings.salary_last_working_day_buffer)
        for amount, txn_date_str in zip(by_month[month], date_map[month]):
            d = parse_date(txn_date_str)
            if not d:
                continue
            amount_ok = abs(amount - median_amount) / max(median_amount, 1) <= tol
            day_ok = (
                settings.salary_day_start <= d.day <= settings.salary_day_end
                or d.day in last_days
            )
            if amount_ok and day_ok:
                credit_dates.append(txn_date_str)
                break

    return {
        "identified": True,
        "probable_amount": round(median_amount, 2),
        "credit_dates": credit_dates,
    }
