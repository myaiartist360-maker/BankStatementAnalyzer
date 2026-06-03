# UploadPage

**Type:** component
**File:** `frontend/src/pages/UploadPage.jsx`
**Layer:** api

## What it does
The landing screen: choose input type (PDF / ZIP / AA JSON), drag-drop a file, optionally supply password hints, analysis period and cross-validation metadata, then POST to the analyse endpoint and navigate to results.

## Key responsibilities
- File → base64; build the [[AnalysisRequest]] payload
- Submit to `POST /api/v1/analyse`; handle/diagnose network errors
- Navigate to [[ResultsPage]] with the result in router state

## Depends on
- [[FastAPIApp]] — calls `/analyse`
- [[AnalysisRequest]] — payload shape
- [[ResultsPage]] — destination on success

## Used by
- [[App]] — route `/`

## Notes
Includes a helpful "backend not running" diagnosis on `Failed to fetch`.
