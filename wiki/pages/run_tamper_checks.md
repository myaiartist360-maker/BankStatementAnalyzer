# run_tamper_checks

**Type:** function
**File:** `backend/pipeline/tamper.py`
**Layer:** domain

## What it does
Step 2: runs up to eight integrity checks over the PDF bytes and the parsed transactions, returning a tamper report (`tampered`, `checks_failed`, `checks_passed`). This is what lets the engine reject doctored statements.

## Key responsibilities
- PDF-level checks: metadata CreationDate≠ModDate, invisible/white text overlay, digital signature (optional), pixel/image anomalies (scanned)
- Data-level checks: balance continuity, date-sequence continuity, duplicate transactions, statistical outliers

## Depends on
- [[balance_checker]] — `check_balance_continuity`
- [[helpers]] — `transaction_hash` for duplicate detection
- [[Settings]] — outlier σ multiplier, signature flag, banks-that-sign set
- [[parse_scanned_pdf]] — reuses `detect_pixel_anomalies` from the OCR parser

## Used by
- [[FastAPIApp]] — Step 2; its verdict sets the response status

## Key logic
Each check appends to `checks_failed` or `checks_passed`. `tampered = any failed`. Balance continuity walks rows in order expecting `bal[n] = bal[n-1] + credit - debit`; date-sequence expects ascending order — both rely on [[ensure_chronological]] having run first.

## Notes
- Statistical-outlier check only flags round-amount, suspicious-narration transfers beyond 5σ — deliberately conservative.
- Digital-signature check is off by default (`enable_digital_signature_check`).
