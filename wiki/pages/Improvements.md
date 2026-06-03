# Improvements

**Type:** concept
**File:** `IMPROVEMENTS.md`
**Layer:** other

## What it does
The living review/backlog of known gaps and improvement areas for the engine, captured during the initial code review.

## Key responsibilities
- Track high/medium/low priority items (no tests, open CORS, no auth, PII at rest)
- Record heuristic limitations (salary median skew, single-EMI cluster, day-granular round-trip window)
- Note follow-ups (validate output against [[AnalysisResponse]] in tests; wire behavioural [[Lexicon]] categories)

## Related to
- [[FastAPIApp]] — CORS/auth/PII items
- [[salary_detector]], [[emi_detector]], [[roundtrip_detector]] — heuristic limits
- [[Lexicon]] — behavioural categories not yet fired

## Notes
Open items as of the latest pass: behavioural AML detectors (smurfing, mule, EMI-stacking, concentration, dormancy) are ported but not yet wired to quantitative tests; `GAMBLING_KEYWORDS`/`CRYPTO_KEYWORDS` in [[Settings]] are now dead.
