# ingest

**Type:** function
**File:** `backend/pipeline/ingestion.py`
**Layer:** domain

## What it does
Step 1 of the pipeline: detects the input format, decrypts password-protected PDFs, routes to the correct parser, and returns raw transactions plus an extraction confidence and error code. The funnel that turns arbitrary uploads into a normalised transaction list.

## Key responsibilities
- Format sniffing via magic bytes (`%PDF`, `PK`) and `input_type`
- Decrypt encrypted PDFs through [[password_cracker]]
- Route to [[parse_digital_pdf]], [[parse_scanned_pdf]], [[parse_aa_json]] or the [[zip_handler]]
- Recurse over ZIP entries and merge their results

## Depends on
- [[password_cracker]] — `is_encrypted` / `try_decrypt`
- [[parse_digital_pdf]] — text-layer PDFs
- [[parse_scanned_pdf]] — scanned PDFs (OCR), and `is_scanned_pdf`
- [[parse_aa_json]] — RBI Account Aggregator payloads
- [[zip_handler]] — multi-file archives (`extract_zip`, `merge_*`)
- [[Settings]] — `enable_ocr` flag

## Used by
- [[FastAPIApp]] — first stage of `/analyse`

## Key logic
AA JSON returns early with 0.9 confidence. For PDFs: if encrypted, try [[password_cracker]] and fail with `PDF_DECRYPT_FAILED` if no pattern works; then choose OCR vs digital via `is_scanned_pdf`. ZIPs recurse `ingest("pdf", …)` per entry and merge via [[zip_handler]].

## Notes
Returns a 6-tuple `(header, transactions, notes, confidence, error, attempted_patterns)` — the `notes` feed the on-screen Processing Log in [[ResultsPage]].
