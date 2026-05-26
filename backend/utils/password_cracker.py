"""
BSA Engine — Indian Bank Password Cracker
Attempts common password patterns used by Indian banks for PDF protection.
"""

from __future__ import annotations
from typing import Optional
import io
import pikepdf


# Pattern functions: each returns a list of candidate passwords
def _patterns(hint: dict) -> list[tuple[str, str]]:
    """
    Returns list of (password, pattern_description) tuples.
    hint keys: dob, account_number_last4, pan_last4, mobile_last4,
               customer_id, custom_password
    """
    candidates: list[tuple[str, str]] = []
    dob = hint.get("dob", "")            # DDMMYYYY
    acc4 = hint.get("account_number_last4", "")
    pan4 = hint.get("pan_last4", "")
    mob4 = hint.get("mobile_last4", "")
    cid  = hint.get("customer_id", "")
    cust = hint.get("custom_password", "")

    # Custom password — try first
    if cust:
        candidates.append((cust, "custom_password"))

    # DOB variations
    if dob and len(dob) == 8:
        dd, mm, yyyy = dob[:2], dob[2:4], dob[4:]
        yy = yyyy[2:]
        candidates += [
            (dob,                           "dob_DDMMYYYY"),
            (f"{dd}{mm}{yy}",               "dob_DDMMYY"),
            (f"{dd}/{mm}/{yyyy}",            "dob_DD/MM/YYYY"),
            (f"{dd}/{mm}/{yy}",              "dob_DD/MM/YY"),
            (yyyy + mm + dd,                 "dob_YYYYMMDD"),
        ]

    # Account last 4 + DOB
    if acc4 and dob:
        candidates += [
            (acc4 + dob,                    "acc4+dob_DDMMYYYY"),
            (acc4 + dob[:2] + dob[2:4],    "acc4+DDMM"),
        ]

    # PAN (uppercase) — many banks use PAN number directly
    if pan4:
        candidates += [
            (pan4.upper(),                  "pan4_upper"),
            (pan4.lower(),                  "pan4_lower"),
        ]
        if dob:
            candidates.append((pan4.upper() + dob, "pan4+dob"))

    # Mobile last 4 + DOB
    if mob4 and dob:
        candidates += [
            (mob4 + dob,                    "mobile4+dob_DDMMYYYY"),
            (mob4 + dob[:2] + dob[2:4],    "mobile4+DDMM"),
        ]

    # Customer ID
    if cid:
        candidates.append((cid, "customer_id"))
        if dob:
            candidates.append((cid + dob, "customer_id+dob"))

    # Fallback common weak passwords
    candidates += [
        ("password",   "weak_password"),
        ("123456",     "weak_123456"),
        ("bank123",    "weak_bank123"),
    ]

    return candidates


def try_decrypt(pdf_bytes: bytes, hint: Optional[dict]) -> tuple[bytes, list[str], str | None]:
    """
    Attempt to decrypt the PDF using generated password candidates.

    Returns:
        (decrypted_bytes, attempted_patterns, successful_pattern | None)
    """
    if not hint:
        hint = {}

    candidates = _patterns(hint)
    attempted: list[str] = []

    for password, pattern in candidates:
        attempted.append(pattern)
        try:
            pdf = pikepdf.open(io.BytesIO(pdf_bytes), password=password)
            out = io.BytesIO()
            pdf.save(out)
            return out.getvalue(), attempted, pattern
        except pikepdf.PasswordError:
            continue
        except Exception:
            continue

    return pdf_bytes, attempted, None


def is_encrypted(pdf_bytes: bytes) -> bool:
    try:
        pikepdf.open(io.BytesIO(pdf_bytes))
        return False
    except pikepdf.PasswordError:
        return True
    except Exception:
        return False
