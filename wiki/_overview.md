# Architecture Overview

## What this system does
BSA Engine is a tamper-aware bank-statement analysis engine for Indian financial institutions. A user uploads a statement (digital PDF, scanned PDF, multi-file ZIP, or RBI Account Aggregator JSON); the engine decrypts and parses it, checks it for tampering, then produces a full financial and credit-decision report — income/expense categorisation, FOIR and a 0–100 credit score, risk flags (gambling, crypto, round-tripping, high-value cash), and a feedback loop for tuning.

It is a FastAPI backend ([[FastAPIApp]]) driving a four-stage pipeline, with a React/Vite dashboard ([[ResultsPage]]) that makes every number clickable back to its source transactions.

## Layer map
| Layer | Components | Role |
|-------|-----------|------|
| API | [[FastAPIApp]], [[AnalysisRequest]], [[AnalysisResponse]], [[App]], [[UploadPage]], [[ResultsPage]] | HTTP + UI entry points |
| Domain (pipeline) | [[ingest]], [[run_tamper_checks]], [[enrich_transactions]], [[ensure_chronological]], [[compute_analysis]] | Four-stage orchestration |
| Domain (detectors) | [[income_detector]], [[expense_detector]], [[salary_detector]], [[emi_detector]], [[gambling_detector]], [[crypto_detector]], [[roundtrip_detector]], [[credit_score]] | Financial + risk analysis |
| Infra (parsers) | [[parse_digital_pdf]], [[parse_scanned_pdf]], [[parse_aa_json]], [[zip_handler]] | Format → transactions |
| Config | [[Settings]], [[Lexicon]] | Thresholds + narration vocabulary |
| Utils | [[helpers]], [[balance_checker]], [[password_cracker]] | Shared foundations |
| UI components | [[DrillDownModal]], [[IncomeAnalysis]], [[ExpenseAnalysis]], [[CreditAssessment]], [[RiskFlags]], [[TamperReport]], [[FeedbackPanel]], [[VizComponents]] | Tabbed dashboard views |

## God nodes
Highest-connectivity components — everything flows through these:
- [[compute_analysis]] — fans out to all eight detectors; the analytical hub
- [[FastAPIApp]] — orchestrates the entire pipeline and owns every route
- [[Lexicon]] — feeds income, expense, gambling and crypto classification
- [[helpers]] — shared by every parser and detector
- [[Settings]] — thresholds/patterns referenced almost everywhere
- [[ResultsPage]] — the frontend hub wiring all tab components + the drill-down

## Surprising connections
- [[run_tamper_checks]] imports `detect_pixel_anomalies` from [[parse_scanned_pdf]] — a tamper check reaching into the OCR parser.
- [[ensure_chronological]] is a quiet but critical dependency of correctness: without it [[run_tamper_checks]] and [[balance_checker]] false-positive on newest-first statements.
- [[credit_score]] is pure and receives everything pre-computed — no detector imports, easy to test.
- FOIR now spans two detectors: [[expense_detector]] supplies obligations, [[income_detector]] supplies income, both consumed by [[credit_score]] via [[compute_analysis]].

## Main data flow
What happens on `POST /api/v1/analyse`:
1. [[FastAPIApp]] decodes the payload and calls [[ingest]].
2. [[ingest]] decrypts ([[password_cracker]]) and parses via [[parse_digital_pdf]] / [[parse_scanned_pdf]] / [[parse_aa_json]] / [[zip_handler]].
3. [[ensure_chronological]] reorders newest-first statements.
4. [[run_tamper_checks]] produces the integrity verdict (using [[balance_checker]] + [[helpers]]).
5. [[enrich_transactions]] derives mode/reversal and filters by period.
6. [[compute_analysis]] runs every detector and [[Lexicon]]-driven categorisation, then [[credit_score]].
7. [[FastAPIApp]] assembles the [[AnalysisResponse]] shape and the dashboard ([[ResultsPage]]) renders it with clickable [[DrillDownModal]] provenance.

## Suggested questions
1. How does a single salary credit influence the final credit score? (trace [[salary_detector]] → [[income_detector]] → [[credit_score]])
2. Why would a genuine statement ever be flagged as tampered, and what prevents it? (see [[ensure_chronological]] ↔ [[run_tamper_checks]])
3. Where exactly is FOIR computed and which transactions feed it? ([[expense_detector]] → [[compute_analysis]] → [[credit_score]])
4. If a new bank's narration format appears, which one file usually needs editing? (hint: [[Lexicon]], occasionally [[parse_digital_pdf]])
5. What breaks if [[helpers]].`parse_date` changes its day-first assumption?
