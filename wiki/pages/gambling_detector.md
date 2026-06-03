# gambling_detector

**Type:** module
**File:** `backend/detectors/gambling_detector.py`
**Layer:** domain

## What it does
Flags gaming/betting/lottery transactions by matching narrations against the lexicon's gambling regex, with a monthly breakdown and per-instance list. A behavioural red flag for credit decisions.

## Depends on
- [[Lexicon]] — `GAMBLING_REGEX` (Dream11, MPL, Rummy, 1xBet, Winzo, …)
- [[Settings]] — high-severity amount threshold

## Used by
- [[compute_analysis]] — gambling analysis + high-risk flag
- [[RiskFlags]] — frontend renders instances

## Notes
Switched from the narrow `GAMBLING_KEYWORDS` set to the lexicon regex for far broader coverage.
