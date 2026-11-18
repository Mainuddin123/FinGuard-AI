
from typing import Any

from langchain_core.tools import tool

from src.database.db import (
    create_investigation_case,
    get_investigation_case,
    update_case_status,
)


ALLOWED_DECISIONS = {
    "APPROVED",
    "REJECTED",
    "ESCALATED",
}

ALLOWED_RISK_LEVELS = {
    "LOW",
    "MEDIUM",
    "HIGH",
}


@tool
def create_case(
    transaction_id: int,
    risk_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Create a persistent investigation case from risk analysis.
    """

    # 1. Validate transaction ID
    if (
        isinstance(transaction_id, bool)
        or not isinstance(transaction_id, int)
        or transaction_id <= 0
    ):
        return {
            "success": False,
            "error": "Transaction ID must be a positive integer.",
        }

    # 2. Validate risk result
    if not isinstance(risk_result, dict):
        return {
            "success": False,
            "error": "Risk result must be a dictionary.",
        }

    required_fields = {
        "risk_score",
        "risk_level",
        "signals",
    }

    missing_fields = required_fields - risk_result.keys()

    if missing_fields:
        return {
            "success": False,
            "error": (
                f"Missing risk fields: {sorted(missing_fields)}"
            ),
        }

    risk_score = risk_result["risk_score"]
    risk_level = risk_result["risk_level"]
    signals = risk_result["signals"]

    if (
        isinstance(risk_score, bool)
        or not isinstance(risk_score, int)
        or not 0 <= risk_score <= 100
    ):
        return {
            "success": False,
            "error": "Risk score must be an integer between 0 and 100.",
        }

    if (
        not isinstance(risk_level, str)
        or risk_level.upper() not in ALLOWED_RISK_LEVELS
    ):
        return {
            "success": False,
            "error": "Invalid risk level.",
        }

    if not isinstance(signals, list):
        return {
            "success": False,
            "error": "Risk signals must be a list.",
        }

    # 3. Create database case
    try:
        case_id = create_investigation_case(
            transaction_id=transaction_id,
            risk_result={
                "risk_score": risk_score,
                "risk_level": risk_level.upper(),
                "signals": signals,
            },
        )

        return {
            "success": True,
            "case_id": case_id,
            "transaction_id": transaction_id,
            "status": "PENDING_REVIEW",
            "message": "Investigation case created successfully.",
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"Case creation failed: {str(exc)}",
        }


@tool
def retrieve_case(case_id: int) -> dict[str, Any]:
    """
    Retrieve an existing investigation case by its ID.
    """

    # 1. Validate case ID
    if (
        isinstance(case_id, bool)
        or not isinstance(case_id, int)
        or case_id <= 0
    ):
        return {
            "success": False,
            "error": "Case ID must be a positive integer.",
        }

    # 2. Retrieve database record
    try:
        case = get_investigation_case(case_id)

        if case is None:
            return {
                "success": False,
                "error": f"Investigation case {case_id} not found.",
            }

        return {
            "success": True,
            "case": case,
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"Case retrieval failed: {str(exc)}",
        }


@tool
def record_human_decision(
    case_id: int,
    decision: str,
    report: str = "",
) -> dict[str, Any]:
    """
    Validate and persist an explicit human review decision.
    """

    # 1. Validate case ID
    if (
        isinstance(case_id, bool)
        or not isinstance(case_id, int)
        or case_id <= 0
    ):
        return {
            "success": False,
            "error": "Case ID must be a positive integer.",
        }

    # 2. Validate decision
    if not isinstance(decision, str):
        return {
            "success": False,
            "error": "Decision must be a string.",
        }

    decision = decision.strip().upper()

    if decision not in ALLOWED_DECISIONS:
        return {
            "success": False,
            "error": (
                "Decision must be APPROVED, REJECTED, or ESCALATED."
            ),
        }

    # 3. Validate report
    if not isinstance(report, str):
        return {
            "success": False,
            "error": "Investigation report must be a string.",
        }

    # 4. Persist decision
    try:
        update_case_status(
            case_id=case_id,
            status=decision,
            human_decision=decision,
            report=report,
        )

        return {
            "success": True,
            "case_id": case_id,
            "status": decision,
            "human_decision": decision,
            "message": "Human decision recorded successfully.",
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to record human decision: {str(exc)}",
        }
