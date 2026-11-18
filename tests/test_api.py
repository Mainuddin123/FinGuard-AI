
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api import routes


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_start_investigation_transaction_not_found(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        routes,
        "get_transaction",
        lambda transaction_id: None,
    )

    response = client.post(
        "/api/v1/investigations",
        json={"transaction_id": 999999},
    )

    assert response.status_code == 404


def test_start_investigation_success(client, monkeypatch):

    monkeypatch.setattr(
        routes,
        "get_transaction",
        lambda transaction_id: {"id": transaction_id},
    )

    monkeypatch.setattr(
        routes,
        "run_investigation",
        lambda transaction_id, thread_id: {},
    )

    monkeypatch.setattr(
        routes,
        "get_investigation_status",
        lambda thread_id: {
            "values": {
                "transaction_id": 1,
                "risk_analysis": {"risk_score": 25},
                "case_id": 10,
            },
            "next": ["human_review"],
            "is_interrupted": True,
        },
    )

    response = client.post(
        "/api/v1/investigations",
        json={"transaction_id": 1},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING_HUMAN_REVIEW"
    assert response.json()["human_review_required"] is True
    assert response.json()["transaction_id"] == 1
    assert response.json()["case_id"] == 10


def test_get_investigation_success(client, monkeypatch):

    monkeypatch.setattr(
        routes,
        "get_investigation_status",
        lambda thread_id: {
            "values": {
                "transaction_id": 1,
                "risk_analysis": {"risk_score": 25},
                "case_id": 10,
            },
            "next": ["human_review"],
            "is_interrupted": True,
        },
    )

    response = client.get(
        "/api/v1/investigations/test-thread"
    )

    assert response.status_code == 200
    assert response.json()["transaction_id"] == 1
    assert response.json()["human_review_required"] is True


def test_get_investigation_not_found(client, monkeypatch):

    monkeypatch.setattr(
        routes,
        "get_investigation_status",
        lambda thread_id: {
            "values": {},
            "next": [],
            "is_interrupted": False,
        },
    )

    response = client.get(
        "/api/v1/investigations/unknown-thread"
    )

    assert response.status_code == 404


def test_submit_decision_when_not_waiting(
    client,
    monkeypatch,
):

    monkeypatch.setattr(
        routes,
        "get_investigation_status",
        lambda thread_id: {
            "values": {"transaction_id": 1},
            "next": [],
            "is_interrupted": False,
        },
    )

    response = client.post(
        "/api/v1/investigations/decision",
        json={
            "thread_id": "test-thread",
            "decision": "ESCALATED",
        },
    )

    assert response.status_code == 409


def test_submit_human_decision_success(
    client,
    monkeypatch,
):

    status_calls = iter([
        {
            "values": {
                "transaction_id": 1,
                "case_id": 10,
            },
            "next": ["human_review"],
            "is_interrupted": True,
        },
        {
            "values": {
                "transaction_id": 1,
                "case_id": 10,
                "human_decision": "ESCALATED",
                "report": "Investigation completed.",
            },
            "next": [],
            "is_interrupted": False,
        },
    ])

    monkeypatch.setattr(
        routes,
        "get_investigation_status",
        lambda thread_id: next(status_calls),
    )

    monkeypatch.setattr(
        routes,
        "resume_investigation",
        lambda thread_id, decision: {},
    )

    response = client.post(
        "/api/v1/investigations/decision",
        json={
            "thread_id": "test-thread",
            "decision": "ESCALATED",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"
    assert response.json()["transaction_id"] == 1
    assert response.json()["human_review_required"] is False
    assert response.json()["report"] == "Investigation completed."


def test_invalid_transaction_id(client):

    response = client.post(
        "/api/v1/investigations",
        json={"transaction_id": 0},
    )

    assert response.status_code == 422


def test_invalid_human_decision(client):

    response = client.post(
        "/api/v1/investigations/decision",
        json={
            "thread_id": "test-thread",
            "decision": "UNKNOWN",
        },
    )

    assert response.status_code == 422
