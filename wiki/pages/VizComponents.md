# VizComponents

**Type:** component
**File:** `frontend/src/components/{BalanceChart,MonthlyBreakdown,TransactionTable}.jsx`
**Layer:** api

## What it does
The presentational building blocks of the Overview and Transactions tabs: `BalanceChart` (EOD balance line over time), `MonthlyBreakdown` (credit-vs-debit bars), and `TransactionTable` (filterable raw transaction grid).

## Depends on
- recharts (external) — charts
- [[compute_analysis]] — consumes monthly breakdowns and raw transactions

## Used by
- [[ResultsPage]] — Overview tab (charts) and Transactions tab (table)

## Notes
Stateless and reusable; they render data already computed by the backend, doing no analysis themselves.
