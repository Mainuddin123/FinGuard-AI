
import pytest

from src.database import db


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_finguard.db"
    monkeypatch.setattr(db, "DB_PATH", test_db_path)

    db.initialize_database()
    return test_db_path


@pytest.fixture
def sample_transaction():
    return {
        "step": 1,
        "transactionType": "TRANSFER",
        "amount": 5000.0,
        "initiator": "CUSTOMER_001",
        "oldBalInitiator": 10000.0,
        "newBalInitiator": 5000.0,
        "recipient": "CUSTOMER_002",
        "oldBalRecipient": 2000.0,
        "newBalRecipient": 7000.0,
    }


def test_database_initialization(test_db):
    assert test_db.exists()


def test_save_and_get_transaction(test_db, sample_transaction):
    transaction_id = db.save_transaction(sample_transaction)

    assert transaction_id > 0

    result = db.get_transaction(transaction_id)

    assert result is not None
    assert result["transaction_type"] == "TRANSFER"
    assert result["amount"] == 5000.0


def test_get_nonexistent_transaction(test_db):
    result = db.get_transaction(999999)

    assert result is None


def test_create_and_retrieve_investigation_case(
    test_db,
    sample_transaction,
):
    transaction_id = db.save_transaction(sample_transaction)

    case_id = db.create_investigation_case(
        transaction_id=transaction_id,
        risk_score=25,
        risk_level="MEDIUM",
        signals=[
            {
                "signal": "TRANSFER_TRANSACTION",
                "points": 25,
            }
        ],
    )

    assert case_id > 0

    case = db.get_investigation_case(case_id)

    assert case is not None
    assert case["transaction_id"] == transaction_id
    assert case["risk_score"] == 25
    assert case["risk_level"] == "MEDIUM"
    assert isinstance(case["signals"], list)


def test_get_nonexistent_case(test_db):
    result = db.get_investigation_case(999999)

    assert result is None
