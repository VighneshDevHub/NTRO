from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.operation_record import OperationType


class OperationReportIn(BaseModel):
    """What any module's agent/service sends after completing an
    operation. Untrusted input — the backend re-derives the hash and
    signature; it never trusts a hash/signature the caller might send."""

    operation_type: OperationType
    target_description: str = Field(min_length=1, max_length=256)
    started_at: datetime
    completed_at: datetime
    success: bool
    operator: str = Field(min_length=1, max_length=128)
    details: dict[str, Any] = Field(default_factory=dict)

    @field_validator("completed_at")
    @classmethod
    def completed_after_started(cls, v: datetime, info):
        started = info.data.get("started_at")
        if started and v < started:
            raise ValueError("completed_at cannot be before started_at")
        return v


class OperationRecordOut(BaseModel):
    certificate_id: str
    operation_type: OperationType
    target_description: str
    started_at: datetime
    completed_at: datetime
    success: bool
    operator: str
    details: dict[str, Any]
    report_hash: str
    signature: str
    ledger_sequence_number: int
    created_at: datetime

    model_config = {"from_attributes": True}


class VerificationResult(BaseModel):
    certificate_id: str
    signature_valid: bool
    chain_intact: bool
    overall_verified: bool
    detail: str
