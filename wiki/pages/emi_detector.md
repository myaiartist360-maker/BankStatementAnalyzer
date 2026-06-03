# emi_detector

**Type:** module
**File:** `backend/detectors/emi_detector.py`
**Layer:** domain

## What it does
Detects recurring loan instalments by clustering NACH/ECS/SI debits on amount (±5%) and day-of-month (±3) across ≥2 months, and separately detects EMI/NACH bounce events.

## Key responsibilities
- `detect_emi` — cluster instalments, pick the largest, infer a lender hint
- `detect_emi_bounces` — match EMI bounce narrations

## Depends on
- [[helpers]] — `parse_date`
- [[Settings]] — tolerances and `EMI_BOUNCE_PATTERNS`

## Used by
- [[compute_analysis]] — EMI analysis + bounce flags

## Notes
Keeps only the single largest cluster, so a borrower with two loans reports one EMI — FOIR is now better served by [[expense_detector]]'s full obligation total instead. Bounce patterns were widened from the [[Lexicon]] Returns layer.
