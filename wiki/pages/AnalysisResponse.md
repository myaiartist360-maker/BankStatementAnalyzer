# AnalysisResponse

**Type:** module
**File:** `backend/models/response_models.py`
**Layer:** api

## What it does
The full output contract: tamper report, statement metadata, summary, monthly breakdowns, every detector block (salary, income, expense, EMI, gambling, crypto, bounce, round-trip, high-value cash), obligation indicators, credit assessment, raw transactions, confidence and notes.

## Key responsibilities
- Define all nested response models (Summary, IncomeAnalysis, ExpenseAnalysis, CreditAssessment, …)
- Serve as the documented schema for the engine output

## Used by
- [[FastAPIApp]] — declares the contract (route returns a raw dict, not model-validated)
- [[ResultsPage]] — frontend consumes this shape
- [[compute_analysis]] — produces dicts matching these models

## Notes
Because `/analyse` returns a raw dict via `JSONResponse`, these models are documentary rather than enforced — schema drift is possible if a detector's dict diverges. Validating against this model in tests is recommended (see [[Improvements]]).
