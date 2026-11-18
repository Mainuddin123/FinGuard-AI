
from src.tools.case_tools import (
    create_case,
    retrieve_case,
    record_human_decision,
)


def test_create_case_rejects_invalid_transaction_id():
    result = create_case.invoke({
        "transaction_id": 0,
        "risk_result": {
            "risk_score": 25,
            "risk_level": "MEDIUM",
            "signals": [],
        },
    })

    assert result["success"] is False


def test_create_case_rejects_invalid_risk_score():
    result = create_case.invoke({
        "transaction_id": 1,
        "risk_result": {
            "risk_score": 150,
            "risk_level": "HIGH",
            "signals": [],
        },
    })

    assert result["success"] is False


def test_create_case_rejects_invalid_risk_level():
    result = create_case.invoke({
        "transaction_id": 1,
        "risk_result": {
            "risk_score": 25,
            "risk_level": "UNKNOWN",
            "signals": [],
        },
    })

    assert result["success"] is False


def test_retrieve_case_rejects_invalid_case_id():
    result = retrieve_case.invoke({
        "case_id": 0,
    })

    assert result["success"] is False


def test_record_decision_rejects_invalid_case_id():
    result = record_human_decision.invoke({
        "case_id": 0,
        "decision": "APPROVED",
        "report": "Test report",
    })

    assert result["success"] is False


def test_record_decision_rejects_invalid_decision():
    result = record_human_decision.invoke({
        "case_id": 1,
        "decision": "UNKNOWN",
        "report": "Test report",
    })

    assert result["success"] is False
