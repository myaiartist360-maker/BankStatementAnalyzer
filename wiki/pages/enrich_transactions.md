# enrich_transactions

**Type:** module
**File:** `backend/pipeline/extraction.py`
**Layer:** domain

## What it does
Step 3: normalises raw parser output and derives per-transaction fields used downstream — `transaction_mode` and `is_reversal`. Also home to `ensure_chronological` (ordering fix) and `filter_by_period` / `build_metadata_out`.

## Key responsibilities
- `derive_transaction_mode` — first-match against [[Settings]] mode patterns (UPI/NEFT/ATM/…)
- `is_reversal` — flag reversal/return narrations
- [[ensure_chronological]] — reverse newest-first statements before checks/analysis
- `filter_by_period` — clip to the requested analysis window
- `build_metadata_out` — statement metadata + cross-validation warnings

## Depends on
- [[Settings]] — `TRANSACTION_MODE_PATTERNS`, `REVERSAL_KEYWORDS`

## Used by
- [[FastAPIApp]] — Step 3 (`enrich_transactions`, `filter_by_period`, `build_metadata_out`, `ensure_chronological`)
- [[compute_analysis]] — consumes the enriched + filtered rows
- [[salary_detector]] / [[emi_detector]] — rely on the derived `transaction_mode`

## Design rationale
`ensure_chronological` exists because many banks (IOB, IDFC) print newest-first, which would make balance-continuity and date-sequence tamper checks false-positive. It reverses the list when descending order dominates.

## Notes
`transaction_mode` keeps the legacy mode vocabulary (NEFT/IMPS/NACH/…) that [[salary_detector]] and [[emi_detector]] depend on — it is intentionally NOT replaced by the [[Lexicon]] channel keys.
