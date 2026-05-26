"""
BSA Engine — FastAPI Application Entry Point
"""

from __future__ import annotations
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure backend/ is on path when running from project root
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from models.request_models import AnalysisRequest
from models.response_models import AnalysisResponse
from utils.helpers import generate_request_id
from pipeline.ingestion import ingest
from pipeline.tamper import run_tamper_checks
from pipeline.extraction import enrich_transactions, filter_by_period, build_metadata_out
from pipeline.analysis import compute_analysis

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="Production-grade tamper-aware bank statement analysis engine for Indian FIs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESULTS_DIR = Path(settings.results_dir)
RESULTS_DIR.mkdir(exist_ok=True)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": settings.app_version, "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/v1/result/{request_id}")
async def get_result(request_id: str):
    path = RESULTS_DIR / f"{request_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Result not found")
    return JSONResponse(content=json.loads(path.read_text(encoding="utf-8")))


@app.post("/api/v1/analyse")
async def analyse(request: AnalysisRequest):
    request_id = generate_request_id()
    notes: list[str] = []

    try:
        # ── Decode file ──────────────────────────────────────────────────────
        file_bytes = None
        if request.input_type in ("pdf", "zip"):
            try:
                file_bytes = request.decode_file()
            except ValueError as e:
                return _error_response(request_id, "EXTRACTION_FAILED", str(e))

        # ── Step 1: Ingestion ────────────────────────────────────────────────
        password_hint = request.password_hint.model_dump() if request.password_hint else {}
        aa_json = request.aa_json

        header, raw_transactions, ingest_notes, confidence, ingest_error, attempted_patterns = ingest(
            input_type=request.input_type,
            file_bytes=file_bytes,
            aa_json=aa_json,
            password_hint=password_hint,
        )
        notes.extend(ingest_notes)

        if ingest_error == "PDF_DECRYPT_FAILED":
            return _save_and_return(request_id, {
                "request_id": request_id,
                "status": "PDF_DECRYPT_FAILED",
                "tamper_report": None,
                "statement_metadata": None,
                "analysis_period": None,
                "summary": None,
                "monthly_credits": [],
                "monthly_debits": [],
                "high_risk_flags": [],
                "raw_transactions": [],
                "confidence_score": 0.0,
                "processing_notes": notes + [
                    f"Attempted patterns: {', '.join(attempted_patterns)}"
                ],
            })

        if ingest_error == "EXTRACTION_FAILED" or not raw_transactions:
            if not raw_transactions:
                notes.append("No transactions could be extracted from the provided input")
            return _save_and_return(request_id, {
                "request_id": request_id,
                "status": "EXTRACTION_FAILED",
                "tamper_report": None,
                "statement_metadata": build_metadata_out(header) if header else None,
                "analysis_period": None,
                "summary": None,
                "monthly_credits": [],
                "monthly_debits": [],
                "high_risk_flags": [],
                "raw_transactions": [],
                "confidence_score": confidence,
                "processing_notes": notes,
            })

        # ── Step 2: Tamper Detection ─────────────────────────────────────────
        tamper_report = run_tamper_checks(
            pdf_bytes=file_bytes if request.input_type in ("pdf", "zip") else None,
            transactions=raw_transactions,
            input_type=request.input_type,
            bank_name=header.get("bank_name"),
        )

        # ── Step 3: Extraction / Enrichment ──────────────────────────────────
        aa_mode = request.input_type == "account_aggregator_json"
        enriched = enrich_transactions(raw_transactions, aa_mode_override=aa_mode)

        # Parse analysis period
        period_from = period_to = None
        if request.analysis_period:
            period_from = request.analysis_period.from_date
            period_to   = request.analysis_period.to_date

        filtered = filter_by_period(enriched, period_from, period_to)

        if not filtered:
            notes.append(
                f"No transactions found within the requested analysis period "
                f"({period_from} → {period_to})"
            )

        cross_val = request.metadata.model_dump() if request.metadata else None
        metadata_out = build_metadata_out(header, cross_validation=cross_val, notes=notes)

        # ── Step 4: Analysis ────────────────────────────────────────────────
        analysis = compute_analysis(filtered, period_from, period_to, notes)

        # ── Determine status ─────────────────────────────────────────────────
        tampered = tamper_report.get("tampered", False)
        failed_checks = tamper_report.get("checks_failed", [])

        if tampered:
            # Allow PARTIAL if only balance continuity failures and <5% rows
            balance_failures = [c for c in failed_checks if c["check"] == "balance_continuity"]
            other_failures = [c for c in failed_checks if c["check"] != "balance_continuity"]

            if not other_failures and balance_failures:
                fail_count = len(balance_failures[0].get("rows_affected", []))
                total_count = len(filtered) or 1
                if fail_count / total_count > 0.05:
                    status = "TAMPER_DETECTED"
                    notes.append(f"Balance continuity failed on {fail_count}/{total_count} rows (>5%)")
                else:
                    status = "PARTIAL"
                    notes.append(f"Balance continuity failed on {fail_count}/{total_count} rows (<5%)")
            else:
                status = "TAMPER_DETECTED"
        else:
            status = "SUCCESS"

        # ── Confidence downgrade on PARTIAL ──────────────────────────────────
        if status == "PARTIAL":
            confidence = min(confidence, 0.75)

        # ── Assemble response ────────────────────────────────────────────────
        response = {
            "request_id": request_id,
            "status": status,
            "tamper_report": tamper_report,
            "statement_metadata": metadata_out,
            "analysis_period": analysis["analysis_period"],
            "summary": analysis["summary"],
            "monthly_credits": analysis["monthly_credits"],
            "monthly_debits": analysis["monthly_debits"],
            "salary_analysis": analysis["salary_analysis"],
            "emi_analysis": analysis["emi_analysis"],
            "bounce_analysis": analysis["bounce_analysis"],
            "gambling_analysis": analysis["gambling_analysis"],
            "crypto_analysis": analysis["crypto_analysis"],
            "round_trip_analysis": analysis["round_trip_analysis"],
            "high_value_cash_analysis": analysis["high_value_cash_analysis"],
            "high_risk_flags": analysis["high_risk_flags"],
            "raw_transactions": filtered,
            "confidence_score": round(confidence, 3),
            "processing_notes": notes,
        }

        return _save_and_return(request_id, response)

    except Exception as exc:
        tb = traceback.format_exc()
        notes.append(f"Unhandled engine error: {type(exc).__name__}: {exc}")
        return _save_and_return(request_id, {
            "request_id": request_id,
            "status": "EXTRACTION_FAILED",
            "tamper_report": None,
            "statement_metadata": None,
            "analysis_period": None,
            "summary": None,
            "monthly_credits": [],
            "monthly_debits": [],
            "high_risk_flags": [],
            "raw_transactions": [],
            "confidence_score": 0.0,
            "processing_notes": notes,
        })


# ── Helpers ───────────────────────────────────────────────────────────────────

def _error_response(request_id: str, status: str, detail: str) -> JSONResponse:
    body = {
        "request_id": request_id,
        "status": status,
        "processing_notes": [detail],
    }
    return JSONResponse(content=body, status_code=422)


def _save_and_return(request_id: str, data: dict) -> JSONResponse:
    # Safely convert everything via json.dumps (which handles Numpy via default=str)
    try:
        safe_data = json.loads(json.dumps(data, default=str))
    except Exception as e:
        safe_data = data  # fallback if anything inexplicably fails
        
    path = RESULTS_DIR / f"{request_id}.json"
    try:
        path.write_text(
            json.dumps(safe_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass
    return JSONResponse(content=safe_data)


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.backend_port, reload=True)
