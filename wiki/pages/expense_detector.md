# expense_detector

**Type:** module
**File:** `backend/detectors/expense_detector.py`
**Layer:** domain

## What it does
The debit-side mirror of [[income_detector]]. Classifies every outflow into an obligation/spend category via the lexicon, separates fixed obligations from discretionary spend, and sums the genuine credit obligations that drive FOIR.

## Key responsibilities
- `analyze_expenses` — per-category totals, monthly averages, recurrence, % share, rows
- Flag fixed obligations (`is_fixed_obligation`) using `FOIR_OBLIGATION_KEYS`
- Compute `monthly_obligations` (EMI + CC + insurance + rent + MFI + KCC + education)

## Depends on
- [[Lexicon]] — `classify_expense`, `detect_channel`, `FOIR_OBLIGATION_KEYS`
- [[helpers]] — `round2`

## Used by
- [[compute_analysis]] — produces `expense_analysis`; feeds `monthly_obligations` to [[credit_score]]
- [[ExpenseAnalysis]] — frontend renders its output

## Design rationale
FOIR previously used only the single largest EMI cluster from [[emi_detector]]; using the lexicon's full obligation set gives a far more accurate debt-burden ratio. Channel fallback (ATM/POS/UPI/cash) labels uncategorised debits.

## Notes
Investments (SIP/RD/PPF), taxes, utilities, subscriptions and supplier COGS are intentionally excluded from FOIR — they are spend, not credit obligations.
