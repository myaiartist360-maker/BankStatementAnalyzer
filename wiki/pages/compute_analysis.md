# compute_analysis

**Type:** function
**File:** `backend/pipeline/analysis.py`
**Layer:** domain

## What it does
The master financial-analysis function (Step 4). Takes the enriched, period-filtered transactions and produces every metric in the output contract: summary aggregates, monthly breakdowns, EOD balance series, all detector outputs, income/expense categorisation, risk flags and the credit assessment. This is the analytical heart of the engine.

## Key responsibilities
- Aggregate credits/debits, monthly breakdowns, averages, largest single credit
- Build the daily EOD balance time-series and months-below-MAB count
- Invoke every detector and assemble `high_risk_flags`
- Compute obligation indicators and feed FOIR inputs into the credit score

## Depends on
- [[helpers]] — date/amount parsing, `round2`, `date_range`
- [[Settings]] — thresholds (MAB, high-value cash, outlier σ)
- [[salary_detector]] — recurring salary credit
- [[income_detector]] — categorised income sources + regular monthly income
- [[expense_detector]] — categorised obligations + monthly fixed obligations
- [[emi_detector]] — EMI cluster + EMI/NACH bounces
- [[gambling_detector]] — gaming spend
- [[crypto_detector]] — VDA exchange flows
- [[roundtrip_detector]] — fund-cycling pairs
- [[credit_score]] — final creditworthiness assessment
- [[Lexicon]] — indirectly, via the detectors it calls

## Used by
- [[FastAPIApp]] — Step 4 of the `/analyse` pipeline

## Key logic
EOD balance: builds a date→last-known-balance map and carries it forward across every calendar day in the period (`_compute_eod_balance`). Bounce analysis splits inward/outward via [[Settings]] patterns. `_build_flags` converts detector outputs into severity-tagged flags. Finally it calls [[credit_score]] passing recurring income (from [[income_detector]]) and monthly obligations (from [[expense_detector]]).

## Notes
- Income basis priority: detected salary → recurring income → average credit.
- FOIR now uses lexicon-derived total obligations, not just the single EMI cluster.
