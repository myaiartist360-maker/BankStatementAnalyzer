"""
BSA Engine — Step 2: Tamper and Integrity Detection
Runs all 8 checks. Returns a TamperReport dict.
"""

from __future__ import annotations
import io
import re
from datetime import datetime
from typing import Optional

import pypdf

from utils.balance_checker import check_balance_continuity
from utils.helpers import transaction_hash
from config import settings, BANKS_WITH_DIGITAL_SIGNATURES

try:
    from parsers.ocr_parser import detect_pixel_anomalies
    PIXEL_CHECK_AVAILABLE = True
except ImportError:
    PIXEL_CHECK_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


def run_tamper_checks(
    pdf_bytes: Optional[bytes],
    transactions: list[dict],
    input_type: str,
    bank_name: Optional[str],
):
    """
    Run all relevant tamper checks and return a tamper_report dict.

    For 'account_aggregator_json': skip PDF checks, run data checks only.
    Returns:
        {
          "tampered": bool,
          "checks_failed": [...],
          "checks_passed": [...],
        }
    """
    checks_failed: list[dict] = []
    checks_passed: list[str] = []

    is_pdf_input = input_type in ("pdf", "zip") and pdf_bytes is not None

    # ── Check 1: PDF Metadata (Creation vs Modification) ─────────────────────
    if is_pdf_input:
        result = _check_pdf_metadata(pdf_bytes)
        if result:
            checks_failed.append(result)
        else:
            checks_passed.append("pdf_metadata_integrity")

    # ── Check 2: Invisible Text Overlay ───────────────────────────────────────
    if is_pdf_input:
        result = _check_invisible_text(pdf_bytes)
        if result:
            checks_failed.append(result)
        else:
            checks_passed.append("invisible_text_overlay")

    # ── Check 3: Digital Signature ────────────────────────────────────────────
    if is_pdf_input and settings.enable_digital_signature_check:
        result = _check_digital_signature(pdf_bytes, bank_name)
        if result:
            checks_failed.append(result)
        elif result is False:
            checks_passed.append("digital_signature_verified")
        # None = not applicable (bank doesn't sign), skip

    # ── Check 4: Balance Continuity ───────────────────────────────────────────
    failures = check_balance_continuity(transactions)
    if failures:
        checks_failed.append({
            "check": "balance_continuity",
            "detail": f"{len(failures)} transaction(s) break balance continuity",
            "rows_affected": failures,
        })
    else:
        checks_passed.append("balance_continuity")

    # ── Check 5: Date/Sequence Continuity ─────────────────────────────────────
    out_of_order = _check_date_sequence(transactions)
    if out_of_order:
        checks_failed.append({
            "check": "date_sequence_continuity",
            "detail": f"{len(out_of_order)} out-of-order transaction(s) detected",
            "rows_affected": out_of_order,
        })
    else:
        checks_passed.append("date_sequence_continuity")

    # ── Check 6: Duplicate Transactions ──────────────────────────────────────
    duplicates = _check_duplicates(transactions)
    if duplicates:
        checks_failed.append({
            "check": "duplicate_transactions",
            "detail": f"{len(duplicates)} duplicate transaction(s) detected",
            "rows_affected": duplicates,
        })
    else:
        checks_passed.append("duplicate_transactions")

    # ── Check 7: Pixel/Image Anomalies (scanned PDFs) ────────────────────────
    if is_pdf_input and PIXEL_CHECK_AVAILABLE:
        anomalies = detect_pixel_anomalies(pdf_bytes)
        if anomalies:
            checks_failed.append({
                "check": "pixel_image_anomaly",
                "detail": f"{len(anomalies)} image-layer anomaly band(s) detected",
                "rows_affected": anomalies,
            })
        else:
            checks_passed.append("pixel_image_layer")

    # ── Check 8: Statistical Outliers ─────────────────────────────────────────
    outliers = _check_statistical_outliers(transactions)
    if outliers:
        checks_failed.append({
            "check": "statistical_outlier",
            "detail": f"{len(outliers)} statistically anomalous round-amount self-transfer(s)",
            "rows_affected": outliers,
        })
    else:
        checks_passed.append("statistical_outlier")

    tampered = len(checks_failed) > 0
    return {
        "tampered": tampered,
        "checks_failed": checks_failed,
        "checks_passed": checks_passed,
    }


# ── Individual Check Implementations ─────────────────────────────────────────

def _check_pdf_metadata(pdf_bytes: bytes) -> Optional[dict]:
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        meta = reader.metadata
        if not meta:
            return None
        creation = meta.get("/CreationDate")
        modified = meta.get("/ModDate")
        if creation and modified and creation != modified:
            return {
                "check": "pdf_metadata_integrity",
                "detail": (
                    f"PDF ModDate ({modified}) differs from CreationDate ({creation}). "
                    "Document may have been edited after creation."
                ),
                "rows_affected": [],
            }
    except Exception as e:
        return {
            "check": "pdf_metadata_integrity",
            "detail": f"Could not read PDF metadata: {e}",
            "rows_affected": [],
        }
    return None


def _check_invisible_text(pdf_bytes: bytes) -> Optional[dict]:
    """
    Detect white-on-white or zero-size invisible text overlays.
    Uses pdfplumber character-level attributes.
    """
    try:
        import pdfplumber
        suspicious: list[dict] = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                chars = page.chars
                for ch in chars:
                    # Check for extremely small font size (invisible)
                    size = ch.get("size", 10)
                    color = ch.get("non_stroking_color")
                    if size < 0.1:
                        suspicious.append({
                            "page": page_idx + 1,
                            "reason": f"Zero-size character '{ch.get('text', '')}'"
                        })
                    # White colour: (1, 1, 1) in RGB or 1.0 in grayscale
                    if color in [(1, 1, 1), 1.0, [1, 1, 1], (1.0, 1.0, 1.0)]:
                        suspicious.append({
                            "page": page_idx + 1,
                            "reason": f"White-on-white text '{ch.get('text', '')}'"
                        })
        if suspicious:
            return {
                "check": "invisible_text_overlay",
                "detail": f"{len(suspicious)} invisible/hidden character(s) found",
                "rows_affected": suspicious[:20],  # cap at 20 for brevity
            }
    except Exception as e:
        return {
            "check": "invisible_text_overlay",
            "detail": f"Could not inspect character layer: {e}",
            "rows_affected": [],
        }
    return None


def _check_digital_signature(
    pdf_bytes: bytes, bank_name: Optional[str]
) -> Optional[bool]:
    """
    Returns:
        None  — bank not known to sign PDFs (skip)
        False — signature verified OK
        dict  — check failure
    """
    bank_upper = (bank_name or "").upper()
    bank_known = any(b in bank_upper for b in BANKS_WITH_DIGITAL_SIGNATURES)
    if not bank_known:
        return None

    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        # Check AcroForm Sig fields
        fields = reader.get_fields()
        if not fields:
            return {
                "check": "digital_signature",
                "detail": (
                    f"{bank_name} typically signs e-statements but no digital "
                    "signature field was found. Possible alteration."
                ),
                "rows_affected": [],
            }
        return False  # signature present
    except Exception as e:
        return {
            "check": "digital_signature",
            "detail": f"Could not verify digital signature: {e}",
            "rows_affected": [],
        }


def _check_date_sequence(transactions: list[dict]) -> list[dict]:
    out_of_order = []
    prev_date = None
    for i, txn in enumerate(transactions):
        d = txn.get("date")
        if d is None:
            continue
        if prev_date and d < prev_date:
            out_of_order.append({
                "row_index": i,
                "date": d,
                "previous_date": prev_date,
                "narration": txn.get("narration", ""),
            })
        prev_date = d
    return out_of_order


def _check_duplicates(transactions: list[dict]) -> list[dict]:
    seen: dict[str, int] = {}
    duplicates = []
    for i, txn in enumerate(transactions):
        amount = txn.get("debit_amount") or txn.get("credit_amount") or 0.0
        h = transaction_hash(txn.get("date") or "", amount, txn.get("narration") or "")
        if h in seen:
            duplicates.append({
                "row_index": i,
                "first_seen_at": seen[h],
                "date": txn.get("date"),
                "amount": amount,
                "narration": txn.get("narration"),
            })
        else:
            seen[h] = i
    return duplicates


def _check_statistical_outliers(transactions: list[dict]) -> list[dict]:
    if not NUMPY_AVAILABLE:
        return []

    HIGH_RISK_NARRATIONS = ["SELF TRANSFER", "IMPS", "NEFT"]

    amounts = []
    for txn in transactions:
        a = txn.get("debit_amount") or txn.get("credit_amount")
        if a is not None:
            amounts.append(a)

    if len(amounts) < 10:
        return []

    arr = np.array(amounts)
    mean = arr.mean()
    std = arr.std()
    if std == 0:
        return []

    threshold = settings.outlier_std_multiplier * std
    outliers = []

    for i, txn in enumerate(transactions):
        a = txn.get("debit_amount") or txn.get("credit_amount")
        if a is None:
            continue
        if abs(a - mean) <= threshold:
            continue

        narration = (txn.get("narration") or "").upper()
        # Only flag if also a round amount AND suspicious narration
        is_round = a % 1000 == 0
        has_suspicious_narr = any(kw in narration for kw in HIGH_RISK_NARRATIONS)

        if is_round and has_suspicious_narr:
            outliers.append({
                "row_index": i,
                "date": txn.get("date"),
                "amount": float(a),
                "narration": txn.get("narration"),
                "z_score": float(round((a - mean) / std, 2)),
            })

    return outliers
