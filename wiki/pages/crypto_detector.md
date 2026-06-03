# crypto_detector

**Type:** module
**File:** `backend/detectors/crypto_detector.py`
**Layer:** domain

## What it does
Counts and totals virtual-digital-asset (crypto) exchange flows by matching narrations against the lexicon's crypto regex (WazirX, CoinDCX, Binance, USDT, …).

## Depends on
- [[Lexicon]] — `CRYPTO_REGEX`

## Used by
- [[compute_analysis]] — crypto analysis + medium-severity flag
- [[RiskFlags]] — frontend renders the summary

## Notes
Thin detector (count + total). Switched from `CRYPTO_KEYWORDS` to the lexicon regex.
