from typing import TypedDict, Any


class InvestigationState(TypedDict, total=False):
    transaction_id: int

    transaction: dict[str, Any]
    risk_analysis: dict[str, Any]

    policy_query: str
    policy_context: list[dict[str, Any]]
    policy_retrieval_success: bool

    requires_review: bool

    case_id: int
    case_result: dict[str, Any]

    human_decision: str
    report: str

    error: str
    report_error: str