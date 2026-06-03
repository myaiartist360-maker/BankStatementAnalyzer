# parse_scanned_pdf

**Type:** function
**File:** `backend/parsers/ocr_parser.py`
**Layer:** infra

## What it does
OCR fallback for image-only PDFs. Renders pages to images via pdf2image and runs Tesseract, then reuses the digital parser's header/line extraction. Also provides `is_scanned_pdf` and `detect_pixel_anomalies`.

## Key responsibilities
- `is_scanned_pdf` — heuristic: <50 chars/page average ⇒ scanned
- OCR each page with pytesseract, then `_extract_header` + `_parse_lines`
- `detect_pixel_anomalies` — row-variance analysis for copy-paste artefacts

## Depends on
- [[parse_digital_pdf]] — reuses `_extract_header` and `_parse_lines`
- [[helpers]] — date/amount/narration helpers

## Used by
- [[ingest]] — when `enable_ocr` and the PDF looks scanned
- [[run_tamper_checks]] — imports `detect_pixel_anomalies`

## Notes
- All OCR features are gated behind optional deps (`pytesseract`, `pdf2image`, `PIL`); absent → returns empty with a note.
- OCR confidence is fixed low (0.55 with rows, else 0.2) since OCR is inherently noisier than text extraction.
