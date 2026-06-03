# TamperReport

**Type:** component
**File:** `frontend/src/components/TamperReport.jsx`
**Layer:** api

## What it does
The Tamper tab. Renders the integrity verdict banner, failed checks with affected rows, and passed checks, using friendly labels for each check key.

## Depends on
- [[run_tamper_checks]] — consumes its `tamper_report` output

## Used by
- [[ResultsPage]] — Tamper tab

## Notes
Shows a graceful "not available" message for AA JSON inputs (which skip PDF-level checks).
