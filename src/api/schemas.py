
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


InvestigationStatus = Literal[
    "PENDING_HUMAN_REVIEW",
    "COMPLETED",
    "FAILED",
]


class InvestigationRequest(BaseModel):
    transaction_id: int = Field(gt=0)


class HumanDecisionRequest(BaseModel):
    thread_id: str = Field(min_length=1)
    decision: Literal["APPROVED", "REJECTED", "ESCALATED"]

    @field_validator("thread_id")
    @classmethod
    def validate_thread_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("thread_id cannot be empty.")

        return value


class InvestigationResponse(BaseModel):
    thread_id: str
    status: InvestigationStatus
    transaction_id: int

    risk_analysis: dict[str, Any] | None = None
    case_id: int | None = None

    human_review_required: bool = False
    report: str | None = None
    error: str | None = None
