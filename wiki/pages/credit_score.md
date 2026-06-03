# credit_score

**Type:** module
**File:** `backend/detectors/credit_score.py`
**Layer:** domain

## What it does
Derives lending-decision metrics from already-computed figures and produces a composite credit score (0–100), a risk band, sub-scores, explainable factors and an advisory recommendation. The credit-decision brain of the engine.

## Key responsibilities
- Compute FOIR, net surplus, savings rate, inflow/outflow ratio, income & balance volatility, negative-balance days
- Weighted composite of five sub-scores (income stability, savings capacity, balance health, obligation burden, conduct)
- Build positive/negative factors and a recommendation that independently gates on hard risk signals

## Depends on
- (pure function — receives pre-computed inputs from [[compute_analysis]])

## Used by
- [[compute_analysis]] — produces `credit_assessment`
- [[CreditAssessment]] — frontend renders score, ratios, factors

## Design rationale
Income basis priority: detected salary → recurring income (from [[income_detector]]) → average credit. FOIR uses total monthly obligations from [[expense_detector]] when available, else the single EMI cluster. Score reflects cash-flow strength; the recommendation can still say DECLINE/REVIEW at a high score when bounces, high-severity flags or FOIR>65% are present — an intentional separation.

## Notes
Pure and dependency-free, so it is easy to unit-test and re-tune; all weights live in `SUB_SCORE_WEIGHTS`.
