"""
BSA Engine — ZIP File Handler
Extracts multiple statements from a ZIP, processes each, then merges.
"""

from __future__ import annotations
import io
import zipfile
from typing import Optional
from utils.helpers import transaction_hash


def extract_zip(zip_bytes: bytes) -> list[tuple[str, bytes]]:
    """
    Extract all files from a ZIP archive.
    Returns list of (filename, file_bytes) tuples.
    Skips __MACOSX, .DS_Store, Thumbs.db.
    """
    files: list[tuple[str, bytes]] = []
    SKIP_PATTERNS = ("__MACOSX", ".DS_Store", "Thumbs.db", ".gitkeep")

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for name in zf.namelist():
                if any(p in name for p in SKIP_PATTERNS):
                    continue
                if name.endswith("/"):
                    continue
                with zf.open(name) as f:
                    files.append((name, f.read()))
    except zipfile.BadZipFile as e:
        raise ValueError(f"Invalid ZIP file: {e}")

    return files


def merge_transactions(
    all_transactions: list[list[dict]],
) -> list[dict]:
    """
    Deduplicate and merge transaction lists from multiple files.
    Deduplication key: hash(date + amount + narration).
    Returns merged list sorted by date.
    """
    seen: set[str] = set()
    merged: list[dict] = []

    for txn_list in all_transactions:
        for txn in txn_list:
            h = transaction_hash(
                txn.get("date") or "",
                (txn.get("debit_amount") or txn.get("credit_amount") or 0.0),
                txn.get("narration") or "",
            )
            if h not in seen:
                seen.add(h)
                merged.append(txn)

    # Sort by date
    def sort_key(t: dict) -> str:
        return t.get("date") or "0000-00-00"

    merged.sort(key=sort_key)
    return merged


def merge_headers(headers: list[dict]) -> dict:
    """
    Merge multiple statement headers, preferring non-None values.
    Updates period to span the full range.
    """
    merged: dict = {}
    period_froms = []
    period_tos = []

    for h in headers:
        for k, v in h.items():
            if k == "statement_period_from":
                if v:
                    period_froms.append(v)
            elif k == "statement_period_to":
                if v:
                    period_tos.append(v)
            elif v is not None and merged.get(k) is None:
                merged[k] = v

    if period_froms:
        merged["statement_period_from"] = min(period_froms)
    if period_tos:
        merged["statement_period_to"] = max(period_tos)

    return merged
