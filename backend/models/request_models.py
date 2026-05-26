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
