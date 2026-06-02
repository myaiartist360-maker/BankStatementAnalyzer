# BSA Engine — Project Review & Improvement Areas

Review date: 2026-06-02. Scope: full backend pipeline + React frontend.

The engine is well-structured (clean pipeline stages, configurable thresholds,
typed Pydantic contracts). The items below are improvement areas found during
review, ordered by impact. Items marked ✅ were addressed in this change set.

---

## ✅ Delivered in this change set

1. **Credit-decision analysis** (`backend/detectors/credit_score.py`) — derives
   the lending metrics that were missing: FOIR, net monthly surplus, savings
   rate, inflow/outflow ratio, income volatility, balance volatility, negative-
   balance days, a weighted composite **credit score (0–100)** with a risk band,
   explainable positive/negative factors, and an advisory recommendation.
   Surfaced via a new **Credit** tab and an overview stat card.
2. **Feedback loop** — `POST /api/v1/feedback`, `GET /api/v1/feedback[/{id}]`
   plus a **Feedback** tab so analysts rate accuracy per section, flag false
   positives / missed risks, and correct values. Stored under `feedback/` as a
   quality signal for tuning.
3. **Bug fix** — `obligation_indicators` was computed in `analysis.py` but never
   added to the API response, so the frontend "Obligation Indicators" card was
   always empty. Now included (and typed in `response_models.py`).

---

## High priority

- **No automated tests.** There is no `tests/` directory anywhere. The detectors
  (salary, EMI, round-trip, credit score) are pure functions and ideal for unit
  tests with fixtures. Add `pytest` + golden-file tests over `generate_sample.py`
  output to prevent threshold regressions.
- **CORS is wide open** (`allow_origins=["*"]` with `allow_credentials=True`).
  This combination is rejected by browsers and is unsafe for a tool handling
  financial PII. Restrict to the known frontend origin via config.
- **PII at rest, unencrypted & unbounded.** Every analysis is written to
  `results/{uuid}.json` in cleartext with full transactions and names, and never
  expires. Add encryption-at-rest or a TTL/purge job, and document retention.
- **No authentication / rate limiting** on any endpoint. Anyone who can reach the
  API can submit statements and read any result by guessing/enumerating UUIDs.

## Medium priority

- **Salary detector picks the median of *all* monthly credits**, not the
  recurring amount. A month with many small credits can drag the "probable
  salary" off the true figure. Prefer clustering recurring same-amount credits
  (like the EMI detector already does) rather than a global median.
- **EMI detection keeps only the single largest cluster** — a borrower with two
  loans reports only one EMI, understating obligations (and FOIR). Return all
  qualifying clusters and sum them for the obligation estimate.
- **Keyword lists are hard-coded constants** (`GAMBLING_KEYWORDS`,
  `CRYPTO_KEYWORDS`, bounce patterns). The README implies they're tunable but
  they aren't env-configurable. Move to config/data files so ops can update
  without a deploy — and so the new feedback data can drive additions.
- **`json.dumps(..., default=str)`** in `_save_and_return` silently stringifies
  anything unexpected (e.g. NaN/Inf floats become `"nan"`), which can corrupt
  numeric fields downstream. Sanitise numerics explicitly.
- **Frontend bundle is 712 kB** (single chunk). Recharts + the whole app load
  eagerly. Code-split the chart/results route with `React.lazy`.
- **`useEffect` in ResultsPage is missing `data` from its dependency array** and
  relies on `requestId` only; fine today but fragile.

## Low priority / polish

- `round_trip_window_hours` is configured but the data only carries day-level
  granularity (no timestamps), so the 48h window can't actually be enforced.
- Largest-single-credit and reversal handling don't feed the credit score; large
  one-off credits inflate "average monthly credit" and could be excluded from the
  income basis.
- No `GET /api/v1/results` listing or pagination — every result is fire-and-forget.
- Health endpoint uses `datetime.utcnow()` (deprecated in 3.12+); prefer
  `datetime.now(timezone.utc)`.
- README documents `customer_id` password hint and OCR but there's no test fixture
  exercising the OCR/ZIP paths.

---

## Suggested next steps

1. Add a `tests/` suite covering the five detectors + the new credit scorer.
2. Aggregate the new feedback (`GET /api/v1/feedback`) into a small admin view to
   watch precision/recall of flags over time, then feed corrections back into the
   keyword lists and thresholds.
3. Lock down CORS + add API-key auth before any non-local deployment.
