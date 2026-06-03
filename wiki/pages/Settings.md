# Settings

**Type:** config
**File:** `backend/config.py`
**Layer:** config

## What it does
Central configuration: numeric thresholds (MAB, outlier σ, round-trip window, salary/EMI tolerances, high-value cash), feature flags (OCR, signature check), directories, and the legacy keyword/pattern lists for transaction modes, reversals and bounces.

## Key responsibilities
- `Settings` (pydantic-settings) — env-overridable thresholds and flags
- `TRANSACTION_MODE_PATTERNS`, `REVERSAL_KEYWORDS` — used by [[enrich_transactions]]
- `INWARD/OUTWARD/EMI_BOUNCE_PATTERNS` — used by [[run_tamper_checks]] and [[emi_detector]]

## Used by
- Nearly every backend module — [[FastAPIApp]], [[compute_analysis]], [[run_tamper_checks]], [[salary_detector]], [[emi_detector]], [[roundtrip_detector]], [[gambling_detector]], [[balance_checker]], [[ingest]]

## Notes
`GAMBLING_KEYWORDS`/`CRYPTO_KEYWORDS` here are now superseded by [[Lexicon]] and effectively dead. Bounce patterns were widened to mirror the lexicon's Returns layer. All values are overridable via `.env`.
