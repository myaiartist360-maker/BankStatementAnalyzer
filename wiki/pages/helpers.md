# helpers

**Type:** module
**File:** `backend/utils/helpers.py`
**Layer:** utils

## What it does
Shared low-level utilities used across the backend: multi-format Indian date parsing, amount parsing (commas, ₹, Dr/Cr), narration cleaning, deterministic transaction hashing, date ranges and rounding.

## Key responsibilities
- `parse_date` / `iso_date` / `date_range` / `last_n_working_days`
- `parse_amount` / `round2`
- `clean_narration`, `transaction_hash`, `generate_request_id`

## Used by
- [[parse_digital_pdf]], [[parse_scanned_pdf]], [[parse_aa_json]] — parsing
- [[zip_handler]], [[run_tamper_checks]] — `transaction_hash`
- [[compute_analysis]], [[salary_detector]], [[income_detector]], [[expense_detector]] — dates/amounts
- [[FastAPIApp]] — `generate_request_id`

## Notes
The most-depended-on utility module — a true shared foundation. Changes here ripple widely, so behaviour (e.g. `dayfirst=True`) must stay stable.
