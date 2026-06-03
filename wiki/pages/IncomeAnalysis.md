# IncomeAnalysis

**Type:** component
**File:** `frontend/src/components/IncomeAnalysis.jsx`
**Layer:** api

## What it does
The Income tab. Shows headline KPIs (total / regular monthly / regular share), a monthly income trend area chart, a clickable source breakdown with share bars, and a top-payers table.

## Depends on
- [[DrillDownModal]] — opened (via `onDrill`) per income source with formula + rows
- [[income_detector]] — consumes its `income_analysis` output
- recharts (external)

## Used by
- [[ResultsPage]] — Income tab

## Notes
Each source click reveals the exact credits classified into it; recurring sources are chipped. Category icons map the lexicon income keys.
