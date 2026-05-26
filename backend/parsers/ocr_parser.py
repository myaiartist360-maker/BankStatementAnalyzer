"""
BSA Engine — Scanned PDF / OCR Parser
Falls back to pytesseract when no text layer is detected.
Requires: Tesseract installed on system PATH.
"""

from __future__ import annotations
import io
import re
from typing import Optional

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from parsers.pdf_parser import _extract_header, _parse_lines
from utils.helpers import clean_narration, parse_date, parse_amount, iso_date


def is_scanned_pdf(pdf_bytes: bytes) -> bool:
    """
    Heuristic: if pdfplumber extracts < 50 characters per page on average,
    treat as scanned.
    """
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            total_chars = sum(
                len(p.extract_text() or "") for p in pdf.pages
            )
            avg = total_chars / max(len(pdf.pages), 1)
            return avg < 50
    except Exception:
        return False


def parse_scanned_pdf(pdf_bytes: bytes) -> tuple[dict, list[dict], list[str], float]:
    """
    OCR-based parser for image-based PDFs.

    Returns:
        (header, transactions, notes, confidence)
    """
    notes: list[str] = []
    if not OCR_AVAILABLE:
        notes.append(
            "OCR dependencies not installed (pytesseract / pdf2image). "
            "Install them and ensure Tesseract is on PATH."
        )
        return {}, [], notes, 0.0

    try:
        images = convert_from_bytes(pdf_bytes, dpi=300)
    except Exception as e:
        notes.append(f"pdf2image conversion failed: {e}")
        return {}, [], notes, 0.0

    full_text = ""
    for i, img in enumerate(images):
        try:
            text = pytesseract.image_to_string(img, lang="eng")
            full_text += text + "\n"
        except Exception as e:
            notes.append(f"OCR failed on page {i+1}: {e}")

    if not full_text.strip():
        notes.append("OCR produced no text output")
        return {}, [], notes, 0.0

    header = _extract_header(full_text)
    transactions = _parse_lines(full_text)
    confidence = 0.55 if transactions else 0.2  # OCR is inherently lower confidence
    notes.append(f"OCR processed {len(images)} page(s); extracted {len(transactions)} transaction(s)")

    return header, transactions, notes, confidence


def detect_pixel_anomalies(pdf_bytes: bytes) -> list[dict]:
    """
    Detect copy-paste artefacts in scanned PDFs by analysing row-level pixel
    variance. Returns list of anomaly dicts {page, row_fraction, detail}.
    """
    anomalies = []
    if not OCR_AVAILABLE:
        return anomalies

    try:
        images = convert_from_bytes(pdf_bytes, dpi=150)
    except Exception:
        return anomalies

    for page_idx, img in enumerate(images):
        import numpy as np
        arr = np.array(img.convert("L"))  # Grayscale
        h, w = arr.shape
        row_vars = []
        slice_h = max(1, h // 40)  # Split into ~40 horizontal bands
        for r in range(0, h - slice_h, slice_h):
            band = arr[r:r + slice_h, :]
            row_vars.append(float(band.var()))

        if len(row_vars) < 4:
            continue

        mean_var = sum(row_vars) / len(row_vars)
        std_var = (sum((v - mean_var) ** 2 for v in row_vars) / len(row_vars)) ** 0.5

        for i, var in enumerate(row_vars):
            if std_var > 0 and abs(var - mean_var) > 4 * std_var:
                anomalies.append({
                    "page": page_idx + 1,
                    "row_fraction": round(i / len(row_vars), 3),
                    "detail": f"Pixel variance {var:.1f} vs mean {mean_var:.1f} (±{std_var:.1f})"
                })

    return anomalies
