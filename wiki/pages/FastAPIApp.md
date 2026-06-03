# FastAPIApp

**Type:** module
**File:** `backend/main.py`
**Layer:** api

## What it does
The HTTP entry point and request orchestrator for the BSA Engine. Exposes the analysis and feedback REST endpoints, decodes the incoming payload, and drives the four-stage pipeline (ingest → tamper → enrich → analyse) before assembling the JSON response. Without it there is no API surface.

## Key responsibilities
- Define routes: `POST /api/v1/analyse`, `GET /api/v1/result/{id}`, `POST/GET /api/v1/feedback`, `GET /api/v1/health`
- Orchestrate the pipeline and map pipeline outcomes to response statuses (`SUCCESS`, `PARTIAL`, `TAMPER_DETECTED`, `PDF_DECRYPT_FAILED`, `EXTRACTION_FAILED`)
- Persist every result to `results/{request_id}.json` and feedback to `feedback/`
- Configure permissive CORS (flagged for tightening in production)

## Depends on
- [[AnalysisRequest]] — validates and decodes the request body
- [[AnalysisResponse]] — output contract (documentary; route returns a raw dict)
- [[ingest]] — Step 1: turn bytes/JSON into raw transactions
- [[ensure_chronological]] — normalise newest-first statements before checks
- [[run_tamper_checks]] — Step 2: integrity verdict
- [[enrich_transactions]] — Step 3: derive mode / reversal / filter by period
- [[compute_analysis]] — Step 4: all financial metrics
- [[Settings]] — results/feedback dirs, version, port

## Used by
- [[App]] — the React frontend calls these endpoints via the Vite proxy
- [[UploadPage]] — `POST /analyse`
- [[ResultsPage]] — `GET /result/{id}`
- [[FeedbackPanel]] — `POST /feedback`

## Design rationale
Pipeline stages are kept as separate imported functions so each can be tested in isolation and the orchestration stays linear and readable. Results are written to disk (not a DB) for a zero-infra deployment.

## Key logic
`analyse()`: decode base64 file → `ingest()` → short-circuit on decrypt/extraction failure → `ensure_chronological()` → `run_tamper_checks()` → `enrich_transactions()` + `filter_by_period()` → `compute_analysis()`. Status is derived from the tamper report, with a PARTIAL allowance when only balance-continuity fails on <5% of rows.

## Notes
- CORS is `allow_origins=["*"]` with credentials — unsafe for production PII (see [[Improvements]]).
- No auth / rate limiting; results are readable by UUID guess.
- The `AnalysisResponse` model is not used to validate the outgoing payload — the route returns a raw dict via `JSONResponse`.
