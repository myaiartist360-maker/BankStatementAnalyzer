# balance_checker

**Type:** module
**File:** `backend/utils/balance_checker.py`
**Layer:** utils

## What it does
Verifies running-balance continuity: for each row, `closing_balance == previous_closing + credit − debit` within a small tolerance. Failures indicate edited amounts or balances.

## Depends on
- [[Settings]] — `balance_continuity_tolerance`

## Used by
- [[run_tamper_checks]] — Check 4 (balance continuity)

## Notes
Walks rows in list order, so it depends on [[ensure_chronological]] having put rows oldest-first. Resets `prev_balance` when a row lacks a closing balance.
