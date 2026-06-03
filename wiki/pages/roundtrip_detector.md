# roundtrip_detector

**Type:** module
**File:** `backend/detectors/roundtrip_detector.py`
**Layer:** domain

## What it does
Detects fund-cycling: a credit followed by a near-equal debit (±2%) within a 48-hour window — a signal of turnover inflation or accommodation entries.

## Depends on
- [[Settings]] — `round_trip_amount_tolerance`, `round_trip_window_hours`

## Used by
- [[compute_analysis]] — round-trip analysis + medium-severity flag
- [[RiskFlags]] — frontend renders the pairs

## Notes
Parses only `YYYY-MM-DD` dates, so the configured hour window is effectively day-granular (no timestamps in statements) — a known limitation in [[Improvements]].
