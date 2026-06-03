# parse_digital_pdf

**Type:** function
**File:** `backend/parsers/pdf_parser.py`
**Layer:** infra

## What it does
Extracts header metadata and transaction rows from text-layer PDFs using pdfplumber. The primary, highest-fidelity extraction path; handles real-world Indian bank table layouts.

## Key responsibilities
- Header extraction via regex (`account_holder_name`, `account_number`, IFSC, period, balances)
- Column classification tolerant of `(Rs)` suffixes, embedded newlines and combined `Date(Value Date)` cells
- Parse headerless continuation tables on later pages by reusing the prior page's column mapping
- Emit granular processing notes (pages, column mapping, parsed vs skipped, confidence)

## Depends on
- [[helpers]] — `parse_date`, `parse_amount`, `clean_narration`, `iso_date`

## Used by
- [[ingest]] — chosen for digital PDFs
- [[parse_scanned_pdf]] — reuses `_extract_header` and `_parse_lines`

## Design rationale
Column matching uses normalised substring keywords (not exact set membership) because headers appear as `Debit(Rs)`, `Balance(Rs)`, `Date(Value Date)` — the original exact match dropped every row on IOB statements. Continuation-table handling recovers transactions on pages where the header row is printed only once.

## Key logic
For each page table: if the first row looks like a header, classify columns and parse the rest; otherwise, if column count matches the last header, treat it as a continuation and parse all rows. Falls back to a regex line-parser (`_parse_lines`) when no table is found.

## Notes
Confidence = 0.5 + fraction-of-rows-with-balance × 0.45 (capped 0.95). Bank name is not always detected (e.g. IOB has no literal "BANK" line).
