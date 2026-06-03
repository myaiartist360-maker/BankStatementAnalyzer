# ensure_chronological

**Type:** function
**File:** `backend/pipeline/extraction.py`
**Layer:** domain

## What it does
Detects whether parsed transactions are in newest-first order and, if so, reverses the list to restore chronological order before integrity checks and analysis. Prevents legitimate descending-order statements from being falsely flagged as tampered.

## Key responsibilities
- Count ascending vs descending adjacent date pairs
- Reverse the whole list (which also fixes intra-day order) when descending dominates
- Emit a processing note when reordering happens

## Depends on
- (none beyond stdlib)

## Used by
- [[FastAPIApp]] — called right after [[ingest]], before [[run_tamper_checks]]

## Design rationale
[[run_tamper_checks]] and [[balance_checker]] assume oldest-first order. IOB/IDFC-style statements print newest-first; a plain date sort would not fix intra-day sequencing, so a full reverse of a fully-descending list is the correct, minimal fix.

## Notes
Surfaced as the diagnostic "Statement was in newest-first order; reordered chronologically…" in the [[ResultsPage]] Processing Log.
