"""
BSA Engine — Shared Utility Helpers
"""

from __future__ import annotations
import hashlib
import re
import uuid
from datetime import date, datetime, timedelta
from typing import Optional
from dateutil import parser as dateutil_parser


def generate_request_id() -> str:
    return str(uuid.uuid4())


def parse_date(raw: str) -> Optional[date]:
    """Parse a date string in multiple common Indian bank formats."""
    if not raw or not raw.strip():
        return None
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d-%b-%Y",
        "%d %B %Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y",
        "%d %b %y", "%d-%b-%y",
    ]
    raw = raw.strip()
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    # Fallback to dateutil
    try:
        return dateutil_parser.parse(raw, dayfirst=True).date()
    except Exception:
        return None


def parse_amount(raw: str) -> Optional[float]:
    """Parse an Indian number string to float. Handles commas, Dr/Cr suffixes."""
    if not raw or not raw.strip():
        return None
    raw = raw.strip().upper()
    # Remove Dr/Cr suffix
    raw = re.sub(r"\s*(DR|CR)\s*$", "", raw)
    # Remove commas and currency symbols
    raw = re.sub(r"[₹,\s]", "", raw)
    try:
        return round(float(raw), 2)
    except ValueError:
        return None


def transaction_hash(date_str: str, amount: float, narration: str) -> str:
    """Deterministic hash for deduplication."""
    key = f"{date_str}|{amount:.2f}|{narration.strip().upper()}"
    return hashlib.sha256(key.encode()).hexdigest()


def clean_narration(raw: str) -> str:
    """Collapse whitespace and strip control characters from narration."""
    if not raw:
        return ""
    return " ".join(raw.split())


def iso_date(d: date) -> str:
    return d.isoformat()


def date_range(start: date, end: date) -> list[date]:
    """Generate every calendar day between start and end (inclusive)."""
    days = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += timedelta(days=1)
    return days


def month_key(d: date) -> str:
    return d.strftime("%Y-%m")


def last_n_working_days(year: int, month: int, n: int) -> list[int]:
    """Return the last N weekday day-of-month numbers in the given month."""
    # Go from end of month backwards
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)
    last_day = next_month_first - timedelta(days=1)
    working_days = []
    cur = last_day
    while len(working_days) < n and cur.month == month:
        if cur.weekday() < 5:  # Mon–Fri
            working_days.append(cur.day)
        cur -= timedelta(days=1)
    return working_days


def round2(val: Optional[float]) -> Optional[float]:
    if val is None:
        return None
    return round(val, 2)
