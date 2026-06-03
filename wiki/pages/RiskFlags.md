# RiskFlags

**Type:** component
**File:** `frontend/src/components/RiskFlags.jsx`
**Layer:** api

## What it does
The Risk tab. Lists severity-sorted high-risk flags and renders inline reference tables for gambling, crypto, round-trip and high-value-cash detections.

## Depends on
- [[gambling_detector]] — gambling instances
- [[crypto_detector]] — crypto summary
- [[roundtrip_detector]] — round-trip pairs
- [[compute_analysis]] — `high_risk_flags` + high-value-cash analysis

## Used by
- [[ResultsPage]] — Risk tab

## Notes
Reference data is shown inline here (the Risk tab is itself the provenance), unlike KPI cards which open [[DrillDownModal]].
