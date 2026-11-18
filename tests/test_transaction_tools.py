
from src.tools import transaction_tools


def test_investigate_transaction_rejects_invalid_id():
    result = transaction_tools.investigate_transaction.invoke({
        "transaction_id": 0
    })

    assert result["success"] is False


def test_investigate_transaction_not_found(monkeypatch):
    monkeypatch.setattr(
        transaction_tools,
        "get_transaction",
        lambda transaction_id: None,
    )

    result = transaction_tools.investigate_transaction.invoke({
        "transaction_id": 999999
    })

    assert result["success"] is False


def test_investigate_transaction_success(monkeypatch):
    sample_transaction = {
        "id": 1,
        "step": 1,
        "transaction_type": "TRANSFER",
        "amount": 5000.0,
        "initiator": "CUSTOMER_001",
        "old_balance_initiator": 10000.0,
        "new_balance_initiator": 5000.0,
        "recipient": "CUSTOMER_002",
        "old_balance_recipient": 2000.0,
        "new_balance_recipient": 7000.0,
    }

    monkeypatch.setattr(
        transaction_tools,
        "get_transaction",
        lambda transaction_id: sample_transaction,
    )

    result = transaction_tools.investigate_transaction.invoke({
        "transaction_id": 1
    })

    assert result["success"] is True
    assert result["transaction_id"] == 1
    assert result["transaction"]["transactionType"] == "TRANSFER"
    assert "risk_analysis" in result
    assert 0 <= result["risk_analysis"]["risk_score"] <= 100
