# Wiki Index

> Last updated: 2026-06-03 · 37 pages · ingested from `D:\My Projects\BSA`

## By layer

### API & UI
- [[FastAPIApp]] — routes + four-stage pipeline orchestration
- [[AnalysisRequest]] — request/feedback input contracts
- [[AnalysisResponse]] — full output contract
- [[App]] — React shell + router
- [[UploadPage]] — upload + analyse screen
- [[ResultsPage]] — tabbed analysis dashboard (frontend hub)

### Domain — Pipeline
- [[ingest]] — Step 1: detect, decrypt, parse, route
- [[run_tamper_checks]] — Step 2: 8 integrity checks
- [[enrich_transactions]] — Step 3: derive mode/reversal, filter
- [[ensure_chronological]] — ordering fix before checks/analysis
- [[compute_analysis]] — Step 4: all metrics (analytical hub)

### Domain — Detectors
- [[income_detector]] — categorised income + payers
- [[expense_detector]] — categorised obligations/spend + FOIR inputs
- [[salary_detector]] — recurring salary
- [[emi_detector]] — EMI clusters + bounces
- [[gambling_detector]] — gaming/betting spend
- [[crypto_detector]] — VDA exchange flows
- [[roundtrip_detector]] — fund-cycling pairs
- [[credit_score]] — composite credit assessment

### Infra — Parsers
- [[parse_digital_pdf]] — text-layer PDFs
- [[parse_scanned_pdf]] — OCR + pixel anomalies
- [[parse_aa_json]] — RBI Account Aggregator JSON
- [[zip_handler]] — multi-file merge

### Config
- [[Settings]] — thresholds, flags, legacy patterns
- [[Lexicon]] — master narration vocabulary

### Utils
- [[helpers]] — dates/amounts/hashing (shared foundation)
- [[balance_checker]] — running-balance continuity
- [[password_cracker]] — Indian-bank PDF passwords

### UI Components
- [[DrillDownModal]] — generic provenance modal
- [[IncomeAnalysis]] — Income tab
- [[ExpenseAnalysis]] — Expenses tab
- [[CreditAssessment]] — Credit tab
- [[RiskFlags]] — Risk tab
- [[TamperReport]] — Tamper tab
- [[FeedbackPanel]] — Feedback tab
- [[VizComponents]] — charts + transaction table

### Meta
- [[Improvements]] — known gaps / backlog

## Sources
| File | Wiki pages |
|------|-----------|
| `backend/main.py` | [[FastAPIApp]] |
| `backend/lexicon.py` | [[Lexicon]] |
| `backend/config.py` | [[Settings]] |
| `backend/pipeline/*.py` | [[ingest]], [[run_tamper_checks]], [[enrich_transactions]], [[ensure_chronological]], [[compute_analysis]] |
| `backend/parsers/*.py` | [[parse_digital_pdf]], [[parse_scanned_pdf]], [[parse_aa_json]], [[zip_handler]] |
| `backend/detectors/*.py` | [[income_detector]], [[expense_detector]], [[salary_detector]], [[emi_detector]], [[gambling_detector]], [[crypto_detector]], [[roundtrip_detector]], [[credit_score]] |
| `backend/utils/*.py` | [[helpers]], [[balance_checker]], [[password_cracker]] |
| `backend/models/*.py` | [[AnalysisRequest]], [[AnalysisResponse]] |
| `frontend/src/**` | [[App]], [[UploadPage]], [[ResultsPage]], [[DrillDownModal]], [[IncomeAnalysis]], [[ExpenseAnalysis]], [[CreditAssessment]], [[RiskFlags]], [[TamperReport]], [[FeedbackPanel]], [[VizComponents]] |
