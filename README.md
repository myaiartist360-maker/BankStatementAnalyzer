# 🏦 BSA Engine — Bank Statement Analysis Engine

Production-grade, tamper-aware bank statement analysis engine for Indian financial institutions.

## Features

| Capability | Detail |
|---|---|
| **Input formats** | Digital PDF, Scanned PDF (OCR), ZIP multi-file, RBI Account Aggregator JSON |
| **Password cracking** | 15+ Indian bank patterns (DOB, PAN, account last-4, mobile, customer ID) |
| **Tamper detection** | 8 checks: PDF metadata, invisible text, digital signature, balance continuity, date sequence, duplicates, pixel anomalies, statistical outliers |
| **Financial analysis** | EOD balance time-series, salary detection, EMI clustering, monthly breakdowns |
| **Risk detection** | Gambling (24 keywords), crypto (7 exchanges), round-trip cycling, high-value cash, cheque/EMI bounces |
| **Dashboard** | Dark-mode React/Vite UI with charts, filterable transaction table, tamper report |

---

## Quick Start

### 1. Backend

```powershell
# Create virtual environment
cd "d:\My Projects\BSA\backend"
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Copy env file
Copy-Item .env.example .env

# Generate a test statement
python generate_sample.py --months 6 --with-gambling --with-bounces

# Start the API
python main.py
# → http://localhost:8000
# → Swagger UI: http://localhost:8000/docs
```

> **OCR support**: Install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and ensure `tesseract` is on your PATH for scanned PDF support.

### 2. Frontend

```powershell
cd "d:\My Projects\BSA\frontend"
npm install
npm run dev
# → http://localhost:5173
```

---

## API Reference

### `POST /api/v1/analyse`

```json
{
  "input_type": "pdf" | "zip" | "account_aggregator_json",
  "file": "<base64-encoded PDF or ZIP>",
  "aa_json": { ... },
  "password_hint": {
    "dob": "15081990",
    "account_number_last4": "9876",
    "pan_last4": "1234P",
    "custom_password": "mypassword"
  },
  "analysis_period": { "from": "2024-01-01", "to": "2024-06-30" },
  "metadata": { "account_holder_name": "John Doe", "bank_name": "HDFC Bank" }
}
```

**Response statuses:** `SUCCESS` | `TAMPER_DETECTED` | `PDF_DECRYPT_FAILED` | `EXTRACTION_FAILED` | `PARTIAL`

### `GET /api/v1/result/{request_id}`
Fetch a previously cached analysis result.

### `GET /api/v1/health`
Health check.

---

## Test with the AA JSON sample

```powershell
# Generate test data
python backend/generate_sample.py --months 6 --with-gambling --with-bounces

# Run analysis
$json = Get-Content backend/samples/sample_statement_aa.json -Raw | ConvertFrom-Json
$body = @{ input_type = "account_aggregator_json"; aa_json = $json } | ConvertTo-Json -Depth 20
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/api/v1/analyse" `
  -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 20
```

---

## Architecture

```
BSA/
├── backend/
│   ├── main.py              FastAPI app (routes + orchestration)
│   ├── config.py            Thresholds + keyword lists
│   ├── models/              Pydantic request/response models
│   ├── pipeline/
│   │   ├── ingestion.py     Step 1: ingest + decrypt
│   │   ├── tamper.py        Step 2: 8 tamper checks
│   │   ├── extraction.py    Step 3: enrich + filter
│   │   └── analysis.py      Step 4: financial metrics
│   ├── parsers/             PDF / OCR / AA JSON / ZIP parsers
│   ├── detectors/           Salary / EMI / gambling / crypto / round-trip
│   └── utils/               Helpers / password cracker / balance checker
└── frontend/
    └── src/
        ├── pages/           UploadPage + ResultsPage
        └── components/      BalanceChart, TransactionTable, RiskFlags, TamperReport
```

---

## Configuration

Edit `backend/.env` to tune thresholds:

| Variable | Default | Description |
|---|---|---|
| `MIN_BALANCE_THRESHOLD` | 10000 | MAB threshold in ₹ |
| `OUTLIER_STD_MULTIPLIER` | 5.0 | σ multiplier for outlier detection |
| `ROUND_TRIP_WINDOW_HOURS` | 48 | Window for round-trip detection |
| `HIGH_VALUE_CASH_THRESHOLD` | 50000 | Daily ATM/CASH flag threshold |
| `ENABLE_DIGITAL_SIGNATURE_CHECK` | false | Enable pyhanko dig-sig verification |
| `ENABLE_OCR` | true | Enable Tesseract OCR for scanned PDFs |
