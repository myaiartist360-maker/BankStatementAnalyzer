# salary_detector

**Type:** module
**File:** `backend/detectors/salary_detector.py`
**Layer:** domain

## What it does
Identifies a probable recurring salary credit using pattern matching over NEFT/IMPS/NACH credits: a consistent amount (±10%) arriving early in the month or in the last few working days, across ≥3 months.

## Key responsibilities
- Filter salary-mode credits and group by month
- Find a median base amount and verify month-over-month consistency
- Return `identified`, `probable_amount`, `credit_dates`

## Depends on
- [[helpers]] — `parse_date`, `last_n_working_days`
- [[Settings]] — tolerance, day windows, `salary_min_months`

## Used by
- [[compute_analysis]] — populates salary summary fields and is passed to [[income_detector]]
- [[credit_score]] — detected salary is the top-priority income basis

## Notes
Uses the median of *all* monthly salary-mode credits as the base, which a noisy month can skew — a candidate for clustering (see [[Improvements]]). Relies on `transaction_mode` from [[enrich_transactions]].
