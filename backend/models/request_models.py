"""
BSA Engine — Pydantic Request (Input) Models
"""

from __future__ import annotations
from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional, Any
import base64


class PasswordHint(BaseModel):
    dob: Optional[str] = Field(None, description="DDMMYYYY format")
    account_number_last4: Optional[str] = None
    pan_last4: Optional[str] = None
    mobile_last4: Optional[str] = None
    customer_id: Optional[str] = None
    custom_password: Optional[str] = None


class AnalysisPeriod(BaseModel):
    from_date: str = Field(..., alias="from", description="YYYY-MM-DD")
    to_date: str = Field(..., alias="to", description="YYYY-MM-DD")

    model_config = {"populate_by_name": True}


class StatementMetadata(BaseModel):
    account_holder_name: Optional[str] = None
    account_number: Optional[str] = None
    bank_name: Optional[str] = None


class SectionFeedback(BaseModel):
    """Per-section correctness rating supplied by the reviewing analyst."""
    salary_correct: Optional[bool] = None
    emi_correct: Optional[bool] = None
    tamper_correct: Optional[bool] = None
    risk_flags_correct: Optional[bool] = None
    transactions_parsed_correctly: Optional[bool] = None
    credit_assessment_useful: Optional[bool] = None


class FeedbackRequest(BaseModel):
    """
    Analyst feedback on an analysis result. Persisted as a training/QA signal so
    the detection thresholds and heuristics can be tuned over time.
    """
    request_id: str = Field(..., description="The analysis result this feedback refers to")
    overall_rating: Optional[int] = Field(
        None, ge=1, le=5, description="1 (poor) – 5 (excellent) accuracy rating"
    )
    sections: Optional[SectionFeedback] = None
    corrected_salary_amount: Optional[float] = Field(
        None, description="Analyst-corrected monthly salary, if the engine got it wrong"
    )
    false_positive_flags: list[str] = Field(
        default_factory=list, description="Flags the engine raised that are incorrect"
    )
    missed_flags: list[str] = Field(
        default_factory=list, description="Risks the analyst expected but the engine missed"
    )
    comments: Optional[str] = Field(None, description="Free-text reviewer notes")
    reviewer: Optional[str] = Field(None, description="Analyst name / id")


class AnalysisRequest(BaseModel):
    input_type: Literal["pdf", "zip", "account_aggregator_json"]

    # For pdf / zip
    file: Optional[str] = Field(
        None,
        description="Base64-encoded binary content of the PDF or ZIP file"
    )

    # For account_aggregator_json
    aa_json: Optional[Any] = Field(
        None,
        description="Raw RBI AA payload (FI Type: DEPOSIT)"
    )

    password_hint: Optional[PasswordHint] = None
    analysis_period: Optional[AnalysisPeriod] = None
    metadata: Optional[StatementMetadata] = None

    @model_validator(mode="after")
    def validate_inputs(self) -> "AnalysisRequest":
        if self.input_type in ("pdf", "zip") and not self.file:
            raise ValueError(
                f"'file' (base64) is required when input_type is '{self.input_type}'"
            )
        if self.input_type == "account_aggregator_json" and self.aa_json is None:
            raise ValueError("'aa_json' is required when input_type is 'account_aggregator_json'")
        return self

    def decode_file(self) -> bytes:
        """Decode base64 file content to raw bytes."""
        if not self.file:
            raise ValueError("No file content to decode")
        try:
            return base64.b64decode(self.file)
        except Exception as e:
            raise ValueError(f"Invalid base64 file content: {e}")
