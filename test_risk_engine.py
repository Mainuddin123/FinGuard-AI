import pytest

from src.risk.engine import analyze_transaction


# Reusable valid transaction
@pytest.fixture
def normal_transaction():
    return {
        "transactionType": "PAYMENT",
        "amount": 100.0,
        "oldBalInitiator": 500.0,
        "newBalInitiator": 400.0,
        "oldBalRecipient": 100.0,
        "newBalRecipient": 200.0,
    }


# 1. Normal transaction
def test_normal_transaction(normal_transaction):
    result = analyze_transaction(normal_transaction)

    assert result["risk_score"] == 0
    assert result["risk_level"] == "LOW"
    assert result["requires_review"] is False


# 2. Transfer transaction
def test_transfer_transaction(normal_transaction):
    normal_transaction["transactionType"] = "TRANSFER"

    result = analyze_transaction(normal_transaction)

    assert result["risk_score"] == 25
    assert result["risk_level"] == "MEDIUM"
    assert "TRANSFER_TRANSACTION" in [
        signal["signal"] for signal in result["signals"]
    ]


# 3. Negative sender balance
def test_negative_sender_balance(normal_transaction):
    normal_transaction["newBalInitiator"] = -50

    result = analyze_transaction(normal_transaction)

    assert "NEGATIVE_SENDER_BALANCE" in [
        signal["signal"] for signal in result["signals"]
    ]


# 4. Unexpected sender balance
def test_unexpected_sender_balance(normal_transaction):
    normal_transaction["newBalInitiator"] = 600

    result = analyze_transaction(normal_transaction)

    assert "UNEXPECTED_SENDER_BALANCE" in [
        signal["signal"] for signal in result["signals"]
    ]


# 5. Unexpected recipient balance
def test_unexpected_recipient_balance(normal_transaction):
    normal_transaction["newBalRecipient"] = 100

    result = analyze_transaction(normal_transaction)

    assert "UNEXPECTED_RECIPIENT_BALANCE" in [
        signal["signal"] for signal in result["signals"]
    ]


# 6. High-risk combination
def test_high_risk_transaction(normal_transaction):
    normal_transaction.update({
        "transactionType": "TRANSFER",
        "newBalInitiator": 600,
        "newBalRecipient": 100,
    })

    result = analyze_transaction(normal_transaction)

    assert result["risk_score"] == 55
    assert result["risk_level"] == "HIGH"
    assert result["requires_review"] is True


# 7. Missing required fields
def test_missing_fields(normal_transaction):
    del normal_transaction["amount"]

    with pytest.raises(ValueError, match="Missing transaction fields"):
        analyze_transaction(normal_transaction)


# 8. Invalid numeric value
def test_invalid_numeric_value(normal_transaction):
    normal_transaction["amount"] = "invalid"

    with pytest.raises(ValueError, match="contain a valid numeric value"):
        analyze_transaction(normal_transaction)


# 9. Negative transaction amount
def test_negative_amount(normal_transaction):
    normal_transaction["amount"] = -100

    with pytest.raises(ValueError, match="cannot be negative"):
        analyze_transaction(normal_transaction)


# 10. NaN value
def test_nan_value(normal_transaction):
    normal_transaction["amount"] = float("nan")

    with pytest.raises(ValueError, match="invalid numeric values"):
        analyze_transaction(normal_transaction)


# 11. Infinite value
def test_infinite_value(normal_transaction):
    normal_transaction["amount"] = float("inf")

    with pytest.raises(ValueError, match="invalid numeric values"):
        analyze_transaction(normal_transaction)


# 12. Ground-truth label must not affect scoring
def test_ground_truth_label_not_used(normal_transaction):
    normal_transaction["isFraud"] = 1

    result = analyze_transaction(normal_transaction)

    assert result["risk_score"] == 0
    assert result["risk_level"] == "LOW"


# 13. Balance mismatch alone should not increase risk
def test_balance_mismatch_not_automatically_flagged(normal_transaction):
    normal_transaction["newBalInitiator"] = 450
    normal_transaction["newBalRecipient"] = 150

    result = analyze_transaction(normal_transaction)

    assert result["risk_score"] == 0
    assert result["risk_level"] == "LOW"


# 14. Result must contain required output fields
def test_result_structure(normal_transaction):
    result = analyze_transaction(normal_transaction)

    expected_fields = {
        "risk_score",
        "risk_level",
        "signals",
        "requires_review",
        "decision",
        "disclaimer",
    }

    assert expected_fields.issubset(result.keys())


# 15. Risk score must remain within 0–100
def test_risk_score_range(normal_transaction):
    result = analyze_transaction(normal_transaction)

    assert 0 <= result["risk_score"] <= 100
