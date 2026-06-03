# password_cracker

**Type:** module
**File:** `backend/utils/password_cracker.py`
**Layer:** utils

## What it does
Attempts to open password-protected bank PDFs by generating candidate passwords from common Indian-bank patterns (DOB, account last-4, PAN, mobile, customer ID) plus the user's hints, using pikepdf.

## Key responsibilities
- `is_encrypted` — detect password protection
- `_patterns` — build ordered `(password, description)` candidates from hints
- `try_decrypt` — attempt each; return decrypted bytes + the successful pattern

## Depends on
- pikepdf (external)

## Used by
- [[ingest]] — decrypts before parsing; failure ⇒ `PDF_DECRYPT_FAILED`

## Design rationale
Hints come from [[AnalysisRequest]]'s `password_hint`; custom password is tried first, then DOB permutations, combinations, and a few weak fallbacks. The list of attempted pattern names is surfaced in processing notes for transparency.

## Notes
Pure pattern brute-force over a small candidate set — not a generic cracker. Order matters for speed.
