# CreditAssessment

**Type:** component
**File:** `frontend/src/components/CreditAssessment.jsx`
**Layer:** api

## What it does
The Credit tab. Renders the credit score gauge and risk band, the lending recommendation, key ratio cards (FOIR, surplus, savings rate, inflow/outflow, balance, volatility), weighted sub-score bars, and positive/risk factor lists.

## Depends on
- [[credit_score]] — consumes its `credit_assessment` output

## Used by
- [[ResultsPage]] — Credit tab

## Notes
Mirrors the backend's separation of score (cash-flow strength) and recommendation (gated on hard risk signals).
