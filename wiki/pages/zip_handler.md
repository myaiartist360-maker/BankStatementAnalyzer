# zip_handler

**Type:** module
**File:** `backend/parsers/zip_handler.py`
**Layer:** infra

## What it does
Handles multi-file ZIP uploads: extracts entries, then deduplicates and merges transactions and headers across the contained statements.

## Key responsibilities
- `extract_zip` — list `(filename, bytes)`, skipping macOS/system cruft
- `merge_transactions` — dedupe by `transaction_hash(date+amount+narration)`, sort by date
- `merge_headers` — prefer non-null fields, span the widest statement period

## Depends on
- [[helpers]] — `transaction_hash` for the dedupe key

## Used by
- [[ingest]] — recurses per ZIP entry then merges

## Notes
Dedupe is essential because overlapping monthly PDFs in one ZIP repeat boundary transactions.
