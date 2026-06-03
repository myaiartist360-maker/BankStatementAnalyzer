# Lexicon

**Type:** module
**File:** `backend/lexicon.py`
**Layer:** config

## What it does
The single source of truth for Indian bank-statement narration vocabulary — a port of the Master Narration Lexicon v5. Holds 53 categories across five layers (Income, Obligation, Channel, Return, Forensic/AML), each backed by a compiled case-insensitive regex tuned for private, PSU (Finacle/BaNCS) and cooperative formats and the NPCI rails. It turns free-text narrations into canonical categories.

## Key responsibilities
- Compile and store all category regexes (`LEXICON`, `BY_TYPE`)
- `classify()` — all matches ordered by engine precedence (return > forensic > obligation > income > channel)
- `classify_income()` / `classify_expense()` / `detect_channel()` — direction-aware, most-specific-first helpers
- Export ready regexes (`GAMBLING_REGEX`, `CRYPTO_REGEX`, …) and `FOIR_OBLIGATION_KEYS`

## Depends on
- (none — pure stdlib `re`)

## Used by
- [[income_detector]] — `classify_income` + `detect_channel`
- [[expense_detector]] — `classify_expense` + `detect_channel` + `FOIR_OBLIGATION_KEYS`
- [[gambling_detector]] — `GAMBLING_REGEX`
- [[crypto_detector]] — `CRYPTO_REGEX`

## Design rationale
Most-specific-first ordering (`_INCOME_ORDER`, `_EXPENSE_ORDER`) ensures purpose categories (e.g. Insurance) beat the generic EMI/auto-debit catch-all, whose regex also matches bare `NACH/ACH/ECS` channel tokens. Behavioural ("B") categories are stored for reference but never fired by words alone.

## Notes
- `FOIR_OBLIGATION_KEYS` deliberately excludes investments, taxes, supplier COGS, utilities and subscriptions — they are spend, not credit obligations.
- Behavioural categories (smurfing, mule, EMI-stacking, concentration, dormancy) are ported but not yet wired to quantitative tests — a known gap.
- Supersedes the now-unused `GAMBLING_KEYWORDS`/`CRYPTO_KEYWORDS` constants in [[Settings]].
