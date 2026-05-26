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
        r"(?:account\s*holder|customer\s*name|name)[:\s]+([A-Z\s]{3,60})",
        r"^Name\s*[:\-]\s*(.+)$",
    ],
    "account_number": [
        r"(?:account\s*(?:no|number|num))[:\s.#]+([0-9Xx\*\-]{6,20})",
        r"A/C\s*No[.:\s]+([0-9X\-]+)",
    ],
    "ifsc_code": [
        r"IFSC(?:\s*Code)?[:\s]+([A-Z]{4}0[A-Z0-9]{6})",
    ],
    "bank_name": [
        r"^(.*BANK.*|.*FINANCE.*|.*CREDIT UNION.*)$",
    ],
    "branch_name": [
        r"(?:branch)[:\s]+(.+?)(?:\n|IFSC|$)",
    ],
    "statement_period_from": [
        r"(?:from|period\s*from|statement\s*from)[:\s]+(\d{1,2}[\-/]\w+[\-/]\d{2,4})",
        r"(\d{2}/\d{2}/\d{4})\s*to\s*\d{2}/\d{2}/\d{4}",
    ],
    "statement_period_to": [
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


# ── Table / Transaction Row Extraction ────────────────────────────────────────

# Common column name synonyms
_COL_DATE     = {"date", "txn date", "transaction date", "trans date", "value date", "posting date"}
_COL_NARR     = {"narration", "description", "particulars", "details", "remarks", "transaction details"}
_COL_DEBIT    = {"debit", "dr", "withdrawal", "withdrawals", "debit amount", "dr amount"}
_COL_CREDIT   = {"credit", "cr", "deposit", "deposits", "credit amount", "cr amount"}
_COL_BALANCE  = {"balance", "closing balance", "running balance", "available balance"}
_COL_VALDATE  = {"value date", "val date"}


def _normalise_col(name: str) -> str:
    return name.strip().lower()


def _match_col(name: str, group: set[str]) -> bool:
    return _normalise_col(name) in group


def _parse_table_rows(table: list[list], header_row: list) -> list[dict]:
    """Map table rows to structured transaction dicts using header names."""
    cols = [_normalise_col(h or "") for h in header_row]
    rows_out = []

    for row in table:
        if not any(row):
            continue
        rec: dict = {}
        for i, cell in enumerate(row):
            if i >= len(cols):
                break
            col = cols[i]
            val = str(cell or "").strip()
            if not val:
                continue
            if any(_match_col(col, g) and not _match_col(col, _COL_VALDATE) for g in [_COL_DATE]):
                rec["_raw_date"] = val
            elif _match_col(col, _COL_VALDATE):
                rec["_raw_value_date"] = val
            elif _match_col(col, _COL_NARR):
                rec["narration"] = clean_narration(val)
            elif _match_col(col, _COL_DEBIT):
                rec["_raw_debit"] = val
            elif _match_col(col, _COL_CREDIT):
                rec["_raw_credit"] = val
            elif _match_col(col, _COL_BALANCE):
                rec["_raw_balance"] = val

        date_val = parse_date(rec.get("_raw_date", ""))
        vdate_val = parse_date(rec.get("_raw_value_date", ""))
        debit = parse_amount(rec.get("_raw_debit", ""))
        credit = parse_amount(rec.get("_raw_credit", ""))
        balance = parse_amount(rec.get("_raw_balance", ""))
        narration = rec.get("narration", "")

        # Skip header repetitions and empty rows
        if not date_val and not narration:
            continue
        if not date_val:
            continue

        rows_out.append({
            "date": iso_date(date_val),
            "value_date": iso_date(vdate_val) if vdate_val else None,
            "narration": narration,
            "debit_amount": debit,
            "credit_amount": credit,
            "closing_balance": balance,
        })

    return rows_out


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
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                full_text += page_text + "\n"

                # Try table extraction
                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    # First row as header if it contains known column names
                    header_row = table[0]
                    if any(
                        _match_col(str(h or ""), s)
                        for h in header_row
                        for s in [_COL_DATE, _COL_NARR, _COL_DEBIT, _COL_CREDIT]
                    ):
                        rows = _parse_table_rows(table[1:], header_row)
                        transactions.extend(rows)

            header = _extract_header(full_text)

            if not transactions:
                notes.append("No table structures detected; attempting line-by-line parsing")
                transactions = _parse_lines(full_text)

            # Confidence heuristic
            if transactions:
                filled = sum(
                    1 for t in transactions
                    if t.get("closing_balance") is not None
                )
                confidence = min(0.95, 0.5 + (filled / len(transactions)) * 0.45)
            else:
                confidence = 0.1
                notes.append("No transactions could be extracted from digital PDF")

    except Exception as e:
        notes.append(f"pdfplumber error: {e}")
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
