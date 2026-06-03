"""
BSA Engine — Digital PDF Parser (pdfplumber)
Extracts header metadata and transaction rows from text-layer PDFs.
"""

from __future__ import annotations
import re
import io
from typing import Optional
import pdfplumber
from utils.helpers import parse_date, parse_amount, clean_narration, iso_date


# ── Header Extraction ─────────────────────────────────────────────────────────

_HEADER_PATTERNS: dict[str, list[str]] = {
    "account_holder_name": [
        r"account\s*holder\s*name\s*[:\-]\s*([A-Za-z][A-Za-z &.\-]{2,60})",
        r"(?:customer\s*name|name)[:\s]+([A-Z][A-Z\s]{3,60})",
    ],
    "account_number": [
        r"account\s*(?:no|number|num)[:\s.#]+([0-9Xx\*\-]{6,20})",
        r"A/C\s*No[.:\s]+([0-9X\-]+)",
    ],
    "ifsc_code": [
        # Matches both "IFSC Code" and IOB-style "IFS Code"
        r"IFSC?(?:\s*Code)?[:\s]+([A-Z]{4}0[A-Z0-9]{6})",
    ],
    "bank_name": [
        r"^(.*BANK.*|.*FINANCE.*|.*CREDIT UNION.*)$",
    ],
    "branch_name": [
        r"(?:branch)[:\s]+(.+?)(?:\n|IFSC|$)",
    ],
    "statement_period_from": [
        r"period\s*of\s*[:\s]+(\d{4}-\d{2}-\d{2})\s*to",
        r"(?:from|period\s*from|statement\s*from)[:\s]+(\d{1,2}[\-/]\w+[\-/]\d{2,4})",
        r"(\d{2}/\d{2}/\d{4})\s*to\s*\d{2}/\d{2}/\d{4}",
    ],
    "statement_period_to": [
        r"period\s*of\s*[:\s]+\d{4}-\d{2}-\d{2}\s*to\s*(\d{4}-\d{2}-\d{2})",
        r"to[:\s]+(\d{1,2}[\-/]\w+[\-/]\d{2,4})(?:\s|$)",
        r"\d{2}/\d{2}/\d{4}\s*to\s*(\d{2}/\d{2}/\d{4})",
    ],
    "opening_balance": [
        r"(?:opening\s*balance|open\s*bal)[:\s]+(?:INR\s*)?([0-9,]+\.?\d*)",
    ],
    "closing_balance": [
        r"(?:closing\s*balance|close\s*bal)[:\s]+(?:INR\s*)?([0-9,]+\.?\d*)",
    ],
}


def _extract_header(text: str) -> dict:
    header: dict[str, Optional[str]] = {k: None for k in _HEADER_PATTERNS}
    for field, patterns in _HEADER_PATTERNS.items():
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
            if m:
                raw = m.group(1).strip()
                if field in ("opening_balance", "closing_balance"):
                    val = parse_amount(raw)
                    header[field] = val
                elif field in ("statement_period_from", "statement_period_to"):
                    d = parse_date(raw)
                    header[field] = iso_date(d) if d else raw
                else:
                    header[field] = raw
                break
    return header


# ── Column Classification ──────────────────────────────────────────────────────
# Header cells are messy in the wild: "Debit(Rs)", "Date(Value\nDate)",
# "Balance (INR)", "Withdrawal Amt." etc. We normalise aggressively (drop
# parentheticals, newlines, punctuation) and then match by *substring* keywords
# instead of exact equality so these real-world variants are recognised.

_ROLE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    # order matters — most specific first
    ("balance",   ("balance",)),
    ("debit",     ("debit", "withdrawal", "withdraw", "dr amount")),
    ("credit",    ("credit", "deposit", "cr amount")),
    ("narration", ("particular", "narration", "description", "remark", "detail", "transaction remarks")),
    ("value_date", ("value date",)),
]


def _clean_col(name: str) -> str:
    s = (name or "").replace("\n", " ").lower()
    s = re.sub(r"\(.*?\)", " ", s)        # drop "(rs)", "(value date)", "(inr)"
    s = re.sub(r"[^a-z ]", " ", s)        # drop digits/punctuation
    return re.sub(r"\s+", " ", s).strip()


def _column_role(name: str) -> Optional[str]:
    """Return the canonical role for a header cell, or None to ignore it."""
    clean = _clean_col(name)
    if not clean:
        return None
    for role, keywords in _ROLE_KEYWORDS:
        if any(kw in clean for kw in keywords):
            return role
    # A column mentioning "value" + "date" → value_date; any other "date" → date.
    if "value" in clean and "date" in clean:
        return "value_date"
    if "date" in clean:
        return "date"
    return None  # ref no, cheque no, transaction type, etc.


def _classify_columns(header_row: list) -> dict[int, str]:
    """Map column index → role. First occurrence of each role wins."""
    roles: dict[int, str] = {}
    seen: set[str] = set()
    for i, cell in enumerate(header_row):
        role = _column_role(str(cell or ""))
        if role and role not in seen:
            roles[i] = role
            seen.add(role)
    return roles


def _looks_like_header(header_row: list) -> bool:
    roles = set(_classify_columns(header_row).values())
    # Need at least a date/narration plus one money column to be a txn table.
    has_money = bool(roles & {"debit", "credit", "balance"})
    has_anchor = bool(roles & {"date", "narration"})
    return has_money and has_anchor


def _clean_date_cell(raw: str) -> str:
    """IOB & others pack 'Txn(Value)' into one cell: '30-Jun-25\\n(30-Jun-25)'."""
    if not raw:
        return ""
    first = raw.replace("\n", " ")
    first = re.sub(r"\(.*?\)", " ", first)   # drop the value-date in parentheses
    first = first.strip()
    return first.split(" ")[0] if first else ""


# ── Table / Transaction Row Extraction ────────────────────────────────────────

def _parse_table_rows(rows: list[list], roles: dict[int, str]) -> tuple[list[dict], int]:
    """Map table rows to structured transaction dicts. Returns (rows, skipped)."""
    rows_out: list[dict] = []
    skipped = 0

    for row in rows:
        if not any(row):
            continue
        rec: dict = {}
        for i, role in roles.items():
            if i >= len(row):
                continue
            val = str(row[i] or "").strip()
            if not val:
                continue
            if role == "date":
                rec["_raw_date"] = val
            elif role == "value_date":
                rec["_raw_value_date"] = val
            elif role == "narration":
                rec["narration"] = clean_narration(val)
            elif role == "debit":
                rec["_raw_debit"] = val
            elif role == "credit":
                rec["_raw_credit"] = val
            elif role == "balance":
                rec["_raw_balance"] = val

        date_val = parse_date(_clean_date_cell(rec.get("_raw_date", "")))
        vdate_val = parse_date(_clean_date_cell(rec.get("_raw_value_date", "")))
        debit = parse_amount(rec.get("_raw_debit", ""))
        credit = parse_amount(rec.get("_raw_credit", ""))
        balance = parse_amount(rec.get("_raw_balance", ""))
        narration = rec.get("narration", "")

        if not date_val:
            # repeated header rows / totals / wrapped continuation lines
            if narration or debit or credit:
                skipped += 1
            continue

        rows_out.append({
            "date": iso_date(date_val),
            "value_date": iso_date(vdate_val) if vdate_val else None,
            "narration": narration,
            "debit_amount": debit,
            "credit_amount": credit,
            "closing_balance": balance,
        })

    return rows_out, skipped


_ROLE_LABEL = {"date": "Date", "value_date": "ValueDate", "narration": "Narration",
               "debit": "Debit", "credit": "Credit", "balance": "Balance"}


def parse_digital_pdf(pdf_bytes: bytes) -> tuple[dict, list[dict], list[str], float]:
    """
    Parse a digital (text-layer) PDF bank statement.

    Returns:
        (header, transactions, notes, confidence)
    """
    notes: list[str] = []
    transactions: list[dict] = []
    header: dict = {}
    confidence = 0.0

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            notes.append(f"Opened PDF: {len(pdf.pages)} page(s)")
            full_text = ""
            total_skipped = 0
            tables_seen = 0
            # Carry the last recognised column mapping forward so that
            # continuation tables on later pages (which often omit the header
            # row) are still parsed correctly.
            last_roles: Optional[dict[int, str]] = None
            last_ncols: Optional[int] = None

            for pidx, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""
                full_text += page_text + "\n"

                tables = page.extract_tables() or []
                for tidx, table in enumerate(tables):
                    if not table or len(table) < 1:
                        continue
                    header_row = table[0]

                    if _looks_like_header(header_row):
                        roles = _classify_columns(header_row)
                        data_rows = table[1:]
                        last_roles = roles
                        last_ncols = len(header_row)
                        mapped = ", ".join(
                            f"{_ROLE_LABEL[r]}→col{i}" for i, r in sorted(roles.items())
                        )
                        notes.append(
                            f"Page {pidx} table {tidx + 1}: header found; "
                            f"{len(data_rows)} data row(s); columns [{mapped}]"
                        )
                    elif last_roles and last_ncols and len(header_row) == last_ncols:
                        # Headerless continuation of the previous transaction table.
                        roles = last_roles
                        data_rows = table  # the first row is already data
                        notes.append(
                            f"Page {pidx} table {tidx + 1}: continuation "
                            f"(reusing prior column mapping); {len(data_rows)} data row(s)"
                        )
                    else:
                        continue

                    tables_seen += 1
                    rows, skipped = _parse_table_rows(data_rows, roles)
                    total_skipped += skipped
                    notes.append(f"Page {pidx} table {tidx + 1}: parsed {len(rows)} transaction(s)")
                    transactions.extend(rows)

            header = _extract_header(full_text)
            ident = header.get("bank_name") or header.get("account_holder_name")
            if ident:
                notes.append(f"Header identified: {ident}")

            if total_skipped:
                notes.append(f"Skipped {total_skipped} unparseable/continuation row(s)")

            if not transactions:
                notes.append(
                    f"No rows from table extraction ({tables_seen} candidate table(s)); "
                    f"trying line-by-line parser on {len(full_text)} chars of text"
                )
                transactions = _parse_lines(full_text)
                if transactions:
                    notes.append(f"Line parser recovered {len(transactions)} transaction(s)")

            # Confidence heuristic
            if transactions:
                filled = sum(1 for t in transactions if t.get("closing_balance") is not None)
                confidence = min(0.95, 0.5 + (filled / len(transactions)) * 0.45)
                notes.append(
                    f"Extracted {len(transactions)} transaction(s); "
                    f"{filled} carry a running balance (confidence {confidence:.2f})"
                )
            else:
                confidence = 0.1
                notes.append(
                    "No transactions could be extracted. The PDF may be scanned "
                    "(enable OCR), use an unusual layout, or be image-only."
                )

    except Exception as e:
        notes.append(f"pdfplumber error: {type(e).__name__}: {e}")
        confidence = 0.0

    return header, transactions, notes, confidence


# ── Fallback line-by-line parser ──────────────────────────────────────────────

_LINE_PATTERN = re.compile(
    r"(\d{1,2}[\-/]\w+[\-/]\d{2,4})"   # date
    r"\s+"
    r"(.+?)"                             # narration (non-greedy)
    r"\s{2,}"
    r"([0-9,]+\.?\d*|-)"                 # debit or -
    r"\s+"
    r"([0-9,]+\.?\d*|-)"                 # credit or -
    r"\s+"
    r"([0-9,]+\.?\d*)"                   # closing balance
)


def _parse_lines(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        m = _LINE_PATTERN.search(line)
        if not m:
            continue
        d = parse_date(m.group(1))
        if not d:
            continue
        narr = clean_narration(m.group(2))
        debit_raw, credit_raw, bal_raw = m.group(3), m.group(4), m.group(5)
        debit = parse_amount(debit_raw) if debit_raw != "-" else None
        credit = parse_amount(credit_raw) if credit_raw != "-" else None
        balance = parse_amount(bal_raw)
        rows.append({
            "date": iso_date(d),
            "value_date": None,
            "narration": narr,
            "debit_amount": debit,
            "credit_amount": credit,
            "closing_balance": balance,
        })
    return rows
