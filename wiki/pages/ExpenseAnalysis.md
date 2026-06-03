# ExpenseAnalysis

**Type:** component
**File:** `frontend/src/components/ExpenseAnalysis.jsx`
**Layer:** api

## What it does
The Expenses tab (mirror of [[IncomeAnalysis]]). Shows total expense, monthly fixed obligations and obligation share, a monthly expense trend, and a clickable category breakdown with 🛡️ markers on FOIR-relevant obligations.

## Depends on
- [[DrillDownModal]] — opened per category with formula + rows
- [[expense_detector]] — consumes its `expense_analysis` output
- recharts (external)

## Used by
- [[ResultsPage]] — Expenses tab

## Notes
Obligation categories (EMI/CC/insurance/rent/MFI/KCC/education) are visually distinguished because they drive FOIR in [[credit_score]].
