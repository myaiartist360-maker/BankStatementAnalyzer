# parse_aa_json

**Type:** function
**File:** `backend/parsers/aa_parser.py`
**Layer:** infra

## What it does
Parses an RBI Account Aggregator (FI Type: DEPOSIT) JSON payload into the engine's header + transaction shape. Supports both nested `FIDataHeader/Transactions` and flat top-level structures. The cleanest, highest-confidence input path (no extraction guesswork).

## Key responsibilities
- Extract header from `Summary`/`Profile.Holders` variants
- Map each transaction (type, amount, narration, value date, balance, mode)
- Tag `_aa_mode` so the AA-provided mode is preferred over keyword inference

## Depends on
- [[helpers]] — `parse_date`, `parse_amount`, `clean_narration`, `iso_date`

## Used by
- [[ingest]] — for `input_type == account_aggregator_json`

## Notes
AA inputs skip all PDF-level tamper checks (no bytes to inspect) — only the data-level checks in [[run_tamper_checks]] apply. `_aa_mode` is consumed by [[enrich_transactions]] when `aa_mode_override` is set.
