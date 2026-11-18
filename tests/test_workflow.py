
from unittest.mock import patch

import pytest

from src.workflow.graph import (
    run_investigation,
    get_investigation_status,
    resume_investigation,
)


def test_invalid_transaction_id():
    with pytest.raises(ValueError):
        run_investigation(
            transaction_id=0,
            thread_id="test-invalid-001",
        )


def test_empty_thread_id():
    with pytest.raises(ValueError):
        run_investigation(
            transaction_id=1,
            thread_id=" ",
        )


def test_invalid_human_decision():
    with pytest.raises(ValueError):
        resume_investigation(
            thread_id="test-thread-001",
            decision="INVALID",
        )


def test_empty_resume_thread_id():
    with pytest.raises(ValueError):
        resume_investigation(
            thread_id=" ",
            decision="APPROVED",
        )


def test_empty_status_thread_id():
    with pytest.raises(ValueError):
        get_investigation_status(" ")


@patch("src.workflow.graph.workflow.invoke")
def test_investigation_invokes_workflow(mock_invoke):
    mock_invoke.return_value = {"risk_analysis": {"risk_score": 25}}

    result = run_investigation(
        transaction_id=1,
        thread_id="pytest-workflow-001",
    )

    assert result["risk_analysis"]["risk_score"] == 25

    mock_invoke.assert_called_once()


@patch("src.workflow.graph.workflow.invoke")
def test_resume_invokes_workflow(mock_invoke):
    mock_invoke.return_value = {"human_decision": "ESCALATED"}

    result = resume_investigation(
        thread_id="pytest-resume-001",
        decision="ESCALATED",
    )

    assert result["human_decision"] == "ESCALATED"
    mock_invoke.assert_called_once()
