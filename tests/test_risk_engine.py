
import pytest

from src.risk.engine import analyze_transaction


def valid_transaction():
    return {
        "step": 1,
        "transactionType": "PAYMENT",
        "amount": 100.0,
        "initiator": "CUST001",
        "oldBalInitiator": 500.0,
        "newBalInitiator": 400.0,
        "recipient": "CUST002",
        "oldBalRecipient": 200.0,
        "newBalRecipient": 300.0,
    }


def test_normal_transaction():
    result = analyze_transaction(valid_transaction())

    assert result["risk_score"] == 0
    assert result["risk_level"] == "LOW"
    assert result["requires_review"] is False


def test_transfer_transaction():
    transaction = valid_transaction()
    transaction["transactionType"] = "TRANSFER"

    result = analyze_transaction(transaction)

    assert result["risk_score"] == 25
    assert result["risk_level"] == "MEDIUM"
    assert result["requires_review"] is True


def test_negative_sender_balance():
    transaction = valid_transaction()
    transaction["newBalInitiator"] = -50.0

    result = analyze_transaction(transaction)

    assert result["risk_score"] == 15
    assert result["risk_level"] == "LOW"


def test_negative_amount_rejected():
    transaction = valid_transaction()
    transaction["amount"] = -100.0

    with pytest.raises(ValueError):
        analyze_transaction(transaction)


def test_missing_required_field():
    transaction = valid_transaction()
    del transaction["amount"]

    with pytest.raises(ValueError):
        analyze_transaction(transaction)


def test_invalid_transaction_input():
    with pytest.raises((ValueError, TypeError)):
        analyze_transaction(None)


def test_invalid_numeric_value():
    transaction = valid_transaction()
    transaction["amount"] = "invalid"

    with pytest.raises(
        ValueError,
        match="contain a valid numeric value",
    ):
        analyze_transaction(transaction)


def test_risk_score_within_valid_range():
    result = analyze_transaction(valid_transaction())

    assert 0 <= result["risk_score"] <= 100
