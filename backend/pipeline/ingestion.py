"""
BSA Engine — Step 1: File Ingestion and Decryption
Detects format, decrypts if needed, routes to the correct parser.
"""

from __future__ import annotations
import io
import struct
from typing import Optional

import pdfplumber

from parsers.pdf_parser import parse_digital_pdf
from parsers.ocr_parser import parse_scanned_pdf, is_scanned_pdf
from parsers.aa_parser import parse_aa_json
from parsers.zip_handler import extract_zip, merge_transactions, merge_headers
from utils.password_cracker import is_encrypted, try_decrypt
from config import settings


def _is_pdf(data: bytes) -> bool:
    return data[:4] == b"%PDF"


def _is_zip(data: bytes) -> bool:
    return data[:2] == b"PK"


def ingest(
    input_type: str,
    file_bytes: Optional[bytes],
    aa_json: Optional[dict],
    password_hint: Optional[dict],
) -> tuple[dict, list[dict], list[str], float, Optional[str], list[str]]:
    """
    Entry point for Step 1.

    Returns:
        header         — extracted statement header fields
        transactions   — raw transaction list
        notes          — processing notes / warnings
        confidence     — extraction confidence 0.0–1.0
        decrypt_error  — error code if decryption failed, else None
        attempted_patterns — list of password patterns tried (for error reporting)
    """
    notes: list[str] = []
    attempted_patterns: list[str] = []
    confidence = 0.0

    # ── Account Aggregator JSON ───────────────────────────────────────────────
    if input_type == "account_aggregator_json":
        header, transactions, aa_notes = parse_aa_json(aa_json)
        return header, transactions, aa_notes, 0.9, None, []

    if not file_bytes:
        notes.append("No file bytes provided")
        return {}, [], notes, 0.0, "EXTRACTION_FAILED", []

    # ── ZIP ───────────────────────────────────────────────────────────────────
    if input_type == "zip" or _is_zip(file_bytes):
        try:
            file_list = extract_zip(file_bytes)
        except ValueError as e:
            notes.append(str(e))
            return {}, [], notes, 0.0, "EXTRACTION_FAILED", []

        all_headers: list[dict] = []
        all_transactions: list[list[dict]] = []
        for fname, fbytes in file_list:
            notes.append(f"Processing ZIP entry: {fname}")
            h, t, n, c, err, ap = ingest("pdf", fbytes, None, password_hint)
            all_headers.append(h)
            all_transactions.append(t)
            notes.extend(n)
            attempted_patterns.extend(ap)
            if err == "PDF_DECRYPT_FAILED":
                return {}, [], notes, 0.0, "PDF_DECRYPT_FAILED", attempted_patterns
            confidence = max(confidence, c)

        merged_header = merge_headers(all_headers)
        merged_txns = merge_transactions(all_transactions)
        notes.append(
            f"ZIP: merged {sum(len(t) for t in all_transactions)} rows "
            f"into {len(merged_txns)} after deduplication"
        )
        return merged_header, merged_txns, notes, confidence, None, attempted_patterns

    # ── PDF ───────────────────────────────────────────────────────────────────
    if not _is_pdf(file_bytes):
        notes.append("File does not appear to be a valid PDF (missing %PDF header)")
        return {}, [], notes, 0.0, "EXTRACTION_FAILED", []

    # Decrypt if needed
    if is_encrypted(file_bytes):
        notes.append("PDF is password-protected; attempting decryption")
        hint_dict = password_hint if isinstance(password_hint, dict) else {}
        file_bytes, attempted_patterns, success_pattern = try_decrypt(file_bytes, hint_dict)
        if success_pattern is None:
            notes.append(f"Decryption failed after {len(attempted_patterns)} attempts")
            return {}, [], notes, 0.0, "PDF_DECRYPT_FAILED", attempted_patterns
        notes.append(f"Decrypted successfully using pattern: {success_pattern}")

    # Scanned vs digital
    if settings.enable_ocr and is_scanned_pdf(file_bytes):
        notes.append("Scanned PDF detected — using OCR parser")
        header, transactions, parse_notes, confidence = parse_scanned_pdf(file_bytes)
    else:
        notes.append("Digital PDF detected — using text-layer parser")
        header, transactions, parse_notes, confidence = parse_digital_pdf(file_bytes)

    notes.extend(parse_notes)
    return header, transactions, notes, confidence, None, attempted_patterns
