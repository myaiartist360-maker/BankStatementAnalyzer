# AnalysisRequest

**Type:** module
**File:** `backend/models/request_models.py`
**Layer:** api

## What it does
Pydantic input contracts. `AnalysisRequest` validates the `/analyse` body (input type, base64 file or AA JSON, password hints, period, cross-validation metadata). Also defines `FeedbackRequest` and `SectionFeedback` for the feedback endpoint.

## Key responsibilities
- Validate input_type-specific requirements (file vs aa_json)
- `decode_file()` — base64 → bytes
- `PasswordHint` shape consumed by [[password_cracker]]
- `FeedbackRequest` — analyst rating, section correctness, corrections

## Used by
- [[FastAPIApp]] — request validation for `/analyse` and `/feedback`
- [[password_cracker]] — receives `password_hint`
- [[UploadPage]] — frontend builds this payload
- [[FeedbackPanel]] — frontend builds the feedback payload

## Notes
`aa_json` is `Any` to tolerate the many real-world AA payload shapes that [[parse_aa_json]] normalises.
