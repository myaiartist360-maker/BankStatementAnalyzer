# income_detector

**Type:** module
**File:** `backend/detectors/income_detector.py`
**Layer:** domain

## What it does
Categorises every credit into an income source using the master narration lexicon, identifies the top payers/counterparties, separates recurring income from one-off inflows, and reports the contributing transactions so each figure is traceable.

## Key responsibilities
- `analyze_income` — per-category totals, monthly averages, recurrence, % share, source rows
- Counterparty extraction (position-aware UPI/IMPS/NEFT parsing) + name-variant merging
- Compute `regular_monthly_income` from recurring sources

## Depends on
- [[Lexicon]] — `classify_income`, `detect_channel`
- [[helpers]] — `parse_date`, `round2`

## Used by
- [[compute_analysis]] — produces `income_analysis`; feeds recurring income to [[credit_score]]
- [[IncomeAnalysis]] — frontend renders its output

## Key logic
Each credit is classified via [[Lexicon]]; cash vs transfer fallback by channel. Payers are parsed by rail position (UPI name after CR/DR, IMPS/NEFT at field 2), honorifics/bank-handles stripped, then folded by word-subset so "Sachin" merges into "Sachin Gupta". Cash deposits are excluded from payers.

## Notes
Counterparty names are heuristic (e.g. fintech sender names like "Instant"); the drill-down always shows raw rows for verification. Salary is treated as one income category, authoritative when [[salary_detector]] also fires.
