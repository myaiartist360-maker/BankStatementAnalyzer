"""
BSA Engine — Pydantic Response (Output) Models
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Literal, Any
from datetime import date


# ── Tamper Report ─────────────────────────────────────────────────────────────

class TamperCheckFailed(BaseModel):
    check: str
    detail: str
    rows_affected: list[Any] = Field(default_factory=list)


class TamperReport(BaseModel):
    tampered: bool
    checks_failed: list[TamperCheckFailed] = Field(default_factory=list)
    checks_passed: list[str] = Field(default_factory=list)


# ── Statement Metadata ────────────────────────────────────────────────────────

class StatementMetadataOut(BaseModel):
    account_holder_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_name: Optional[str] = None
    branch_name: Optional[str] = None
    statement_period_from: Optional[str] = None
    statement_period_to: Optional[str] = None
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None


# ── Transaction ───────────────────────────────────────────────────────────────

class Transaction(BaseModel):
    date: Optional[str] = None
    value_date: Optional[str] = None
    narration: Optional[str] = None
    debit_amount: Optional[float] = None
    credit_amount: Optional[float] = None
    closing_balance: Optional[float] = None
    transaction_mode: Optional[str] = None
    is_reversal: bool = False


# ── Monthly Breakdown ─────────────────────────────────────────────────────────

class MonthlyBreakdown(BaseModel):
    month: str                    # "YYYY-MM"
    amount: float
    count: int


# ── Balance ───────────────────────────────────────────────────────────────────

class BalancePoint(BaseModel):
    amount: float
    date: Optional[str] = None


# ── Salary Analysis ───────────────────────────────────────────────────────────

class SalaryAnalysis(BaseModel):
    identified: bool
    probable_amount: Optional[float] = None
    credit_dates: list[str] = Field(default_factory=list)


# ── EMI Analysis ─────────────────────────────────────────────────────────────

class EMIInstance(BaseModel):
    date: str
    amount: float
    narration: str


class EMIAnalysis(BaseModel):
    count: int
    probable_emi_amount: Optional[float] = None
    lender_hint: Optional[str] = None
    instances: list[EMIInstance] = Field(default_factory=list)


# ── Bounce Analysis ───────────────────────────────────────────────────────────

class BounceInstance(BaseModel):
    date: str
    amount: float
    narration: str


class BounceGroup(BaseModel):
    count: int
    total_amount: float
    instances: list[BounceInstance] = Field(default_factory=list)


class EMIBounceGroup(BaseModel):
    count: int
    instances: list[BounceInstance] = Field(default_factory=list)


class BounceAnalysis(BaseModel):
    inward_cheque_bounces: BounceGroup
    outward_cheque_bounces: BounceGroup
    emi_bounces: EMIBounceGroup


# ── Gambling Analysis ─────────────────────────────────────────────────────────

class GamblingInstance(BaseModel):
    date: str
    amount: float
    narration: str


class GamblingAnalysis(BaseModel):
    count: int
    total_amount: float
    monthly_breakdown: list[MonthlyBreakdown] = Field(default_factory=list)
    instances: list[GamblingInstance] = Field(default_factory=list)


# ── Crypto Analysis ───────────────────────────────────────────────────────────

class CryptoAnalysis(BaseModel):
    count: int
    total_amount: float


# ── Round-Trip Analysis ───────────────────────────────────────────────────────

class RoundTripPair(BaseModel):
    credit_date: str
    debit_date: str
    amount: float
    credit_narration: str
    debit_narration: str


class RoundTripAnalysis(BaseModel):
    count: int
    instances: list[RoundTripPair] = Field(default_factory=list)


# ── High-Value Cash ───────────────────────────────────────────────────────────

class CashWithdrawalDay(BaseModel):
    date: str
    total_amount: float
    transactions: list[dict] = Field(default_factory=list)


class HighValueCashAnalysis(BaseModel):
    count: int
    total_amount: float
    instances: list[CashWithdrawalDay] = Field(default_factory=list)


# ── High-Risk Flags ───────────────────────────────────────────────────────────

class HighRiskFlag(BaseModel):
    flag: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    detail: str


# ── Summary ───────────────────────────────────────────────────────────────────

class Summary(BaseModel):
    total_transactions: int = 0
    total_credit_transactions: int = 0
    total_debit_transactions: int = 0
    total_reversal_transactions: int = 0
    total_credit_amount: float = 0.0
    total_debit_amount: float = 0.0
    average_eod_balance: float = 0.0
    minimum_eod_balance: Optional[BalancePoint] = None
    maximum_eod_balance: Optional[BalancePoint] = None
    average_monthly_credit: float = 0.0
    average_monthly_debit: float = 0.0
    months_below_minimum_balance: int = 0
    balance_utilisation_ratio: Optional[float] = None
    inward_cheque_bounces: int = 0
    outward_cheque_bounces: int = 0
    emi_bounces: int = 0
    gambling_transaction_count: int = 0
    gambling_total_amount: float = 0.0
    salary_identified: bool = False
    probable_salary_amount: Optional[float] = None
    largest_single_credit: Optional[dict] = None


# ── Root Response ─────────────────────────────────────────────────────────────

class AnalysisPeriodOut(BaseModel):
    from_date: Optional[str] = Field(None, alias="from")
    to_date: Optional[str] = Field(None, alias="to")

    model_config = {"populate_by_name": True}


class AnalysisResponse(BaseModel):
    request_id: str
    status: Literal[
        "SUCCESS",
        "TAMPER_DETECTED",
        "PDF_DECRYPT_FAILED",
        "EXTRACTION_FAILED",
        "PARTIAL"
    ]
    tamper_report: Optional[TamperReport] = None
    statement_metadata: Optional[StatementMetadataOut] = None
    analysis_period: Optional[AnalysisPeriodOut] = None
    summary: Optional[Summary] = None
    monthly_credits: list[MonthlyBreakdown] = Field(default_factory=list)
    monthly_debits: list[MonthlyBreakdown] = Field(default_factory=list)
    salary_analysis: Optional[SalaryAnalysis] = None
    emi_analysis: Optional[EMIAnalysis] = None
    gambling_analysis: Optional[GamblingAnalysis] = None
    crypto_analysis: Optional[CryptoAnalysis] = None
    bounce_analysis: Optional[BounceAnalysis] = None
    round_trip_analysis: Optional[RoundTripAnalysis] = None
    high_value_cash_analysis: Optional[HighValueCashAnalysis] = None
    high_risk_flags: list[HighRiskFlag] = Field(default_factory=list)
    raw_transactions: list[Transaction] = Field(default_factory=list)
    confidence_score: float = 0.0
    processing_notes: list[str] = Field(default_factory=list)
