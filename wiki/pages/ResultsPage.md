# ResultsPage

**Type:** component
**File:** `frontend/src/pages/ResultsPage.jsx`
**Layer:** api

## What it does
The analysis dashboard. Renders the status header, confidence bar, clickable KPI stat cards, a severity-tagged Processing Log, and tabbed views (Overview, Income, Expenses, Credit, Transactions, Risk, Tamper, Feedback). Owns the drill-down provenance state. The frontend god node.

## Key responsibilities
- Fetch result by id (or use router state) from [[FastAPIApp]]
- Build `DERIVE` descriptors — formula + source rows for each KPI
- Show a prominent failure banner + auto-expanded log on non-SUCCESS
- Route each tab to its component and mount the drill-down modal

## Depends on
- [[DrillDownModal]] — provenance modal it opens for every KPI
- [[IncomeAnalysis]] — Income tab
- [[ExpenseAnalysis]] — Expenses tab
- [[CreditAssessment]] — Credit tab
- [[RiskFlags]] — Risk tab
- [[TamperReport]] — Tamper tab
- [[FeedbackPanel]] — Feedback tab
- [[VizComponents]] — Overview charts + transaction table
- [[FastAPIApp]] — `GET /result/{id}`
- [[AnalysisResponse]] — the data shape it renders

## Used by
- [[App]] — route `/results/:requestId`

## Key logic
`DERIVE` maps each KPI key to a `{title, formula, columns, rows}` descriptor by filtering `raw_transactions` or pulling detector `instances`, so every headline number is traceable via [[DrillDownModal]].

## Notes
Every stat card carries the `clickable` affordance; the same modal is reused by [[IncomeAnalysis]] and [[ExpenseAnalysis]] via an `onDrill` callback.
