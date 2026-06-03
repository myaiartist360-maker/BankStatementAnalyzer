# FeedbackPanel

**Type:** component
**File:** `frontend/src/components/FeedbackPanel.jsx`
**Layer:** api

## What it does
The Feedback tab. Lets an analyst rate overall accuracy, mark each section correct/wrong, supply corrections (e.g. corrected salary, false-positive/missed flags) and comments, then POST to the feedback endpoint as a model-tuning signal.

## Depends on
- [[FastAPIApp]] — `POST /api/v1/feedback`
- [[AnalysisRequest]] — the `FeedbackRequest` shape it builds

## Used by
- [[ResultsPage]] — Feedback tab

## Notes
Feedback is appended per `request_id` under `feedback/` and aggregated by `GET /api/v1/feedback` for a quality view.
