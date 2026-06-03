# DrillDownModal

**Type:** component
**File:** `frontend/src/components/DrillDownModal.jsx`
**Layer:** api

## What it does
A generic provenance modal. Given a `detail` descriptor it shows how a metric was derived (formula + note) and the contributing reference transactions in a table, with a summed total. The mechanism behind "click any element to see how it was derived".

## Depends on
- (presentational; driven by descriptors)

## Used by
- [[ResultsPage]] — opened from every KPI stat card and the EMI card
- [[IncomeAnalysis]] — opened per income source
- [[ExpenseAnalysis]] — opened per expense category

## Design rationale
Kept fully generic (`{title, formula, columns, rows}`) so any metric can be made traceable without bespoke modals. Closes on overlay click or Escape; locks body scroll.

## Notes
Column `type` controls cell rendering (date/amount/credit/debit/text).
