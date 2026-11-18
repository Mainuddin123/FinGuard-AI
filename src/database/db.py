
import sqlite3
import json

from pathlib import Path
from contextlib import contextmanager
from typing import Any


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "finguard.db"


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

@contextmanager
def get_connection():
    """Provide a managed SQLite database connection."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    # Enable foreign key enforcement for this connection.
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

def initialize_database():
    """Create FinGuard AI database tables."""

    with get_connection() as conn:

        # Transaction records
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                step INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                initiator TEXT NOT NULL,
                old_balance_initiator REAL NOT NULL,
                new_balance_initiator REAL NOT NULL,
                recipient TEXT NOT NULL,
                old_balance_recipient REAL NOT NULL,
                new_balance_recipient REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Investigation cases
        conn.execute("""
            CREATE TABLE IF NOT EXISTS investigation_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                signals TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING_REVIEW',
                human_decision TEXT,
                investigation_report TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                FOREIGN KEY (transaction_id)
                    REFERENCES transactions(id)
            )
        """)

        # Useful indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_transaction_initiator
            ON transactions(initiator)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_status
            ON investigation_cases(status)
        """)

    print("FinGuard AI database initialized successfully.")


# --------------------------------------------------
# TRANSACTION OPERATIONS
# --------------------------------------------------

def save_transaction(transaction: dict[str, Any]) -> int:
    """Save a transaction and return its database ID."""

    if not isinstance(transaction, dict):
        raise ValueError("Transaction must be a dictionary.")

    required_fields = [
        "step",
        "transactionType",
        "amount",
        "initiator",
        "oldBalInitiator",
        "newBalInitiator",
        "recipient",
        "oldBalRecipient",
        "newBalRecipient",
    ]

    missing = [
        field for field in required_fields
        if field not in transaction
    ]

    if missing:
        raise ValueError(f"Missing fields: {missing}")

    with get_connection() as conn:

        cursor = conn.execute("""
            INSERT INTO transactions (
                step,
                transaction_type,
                amount,
                initiator,
                old_balance_initiator,
                new_balance_initiator,
                recipient,
                old_balance_recipient,
                new_balance_recipient
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            transaction["step"],
            transaction["transactionType"],
            transaction["amount"],
            str(transaction["initiator"]),
            transaction["oldBalInitiator"],
            transaction["newBalInitiator"],
            str(transaction["recipient"]),
            transaction["oldBalRecipient"],
            transaction["newBalRecipient"],
        ))

        return cursor.lastrowid


def get_transaction(transaction_id: int):
    """Retrieve a transaction by its database ID."""

    with get_connection() as conn:

        row = conn.execute("""
            SELECT *
            FROM transactions
            WHERE id = ?
        """, (transaction_id,)).fetchone()

        return dict(row) if row else None


# --------------------------------------------------
# INVESTIGATION CASE OPERATIONS
# --------------------------------------------------

def create_investigation_case(
    transaction_id: int,
    risk_result: dict[str, Any] | None = None,
    *,
    risk_score: int | None = None,
    risk_level: str | None = None,
    signals: list | None = None,
) -> int:
    """
    Create an investigation case.

    Supports two formats:

    1. risk_result={
        "risk_score": 25,
        "risk_level": "MEDIUM",
        "signals": [...]
    }

    2. risk_score=25,
       risk_level="MEDIUM",
       signals=[...]
    """

    # Validate transaction ID
    if (
        isinstance(transaction_id, bool)
        or not isinstance(transaction_id, int)
        or transaction_id <= 0
    ):
        raise ValueError(
            "Transaction ID must be a positive integer."
        )

    # Support both input formats
    if risk_result is not None:

        if any(
            value is not None
            for value in (risk_score, risk_level, signals)
        ):
            raise ValueError(
                "Use either risk_result or individual risk fields."
            )

        if not isinstance(risk_result, dict):
            raise ValueError(
                "risk_result must be a dictionary."
            )

        risk_score = risk_result.get("risk_score")
        risk_level = risk_result.get("risk_level")
        signals = risk_result.get("signals")

    # Validate risk score
    if (
        isinstance(risk_score, bool)
        or not isinstance(risk_score, int)
        or not 0 <= risk_score <= 100
    ):
        raise ValueError(
            "Risk score must be an integer between 0 and 100."
        )

    # Validate risk level
    if (
        not isinstance(risk_level, str)
        or risk_level.upper() not in {"LOW", "MEDIUM", "HIGH"}
    ):
        raise ValueError("Invalid risk level.")

    # Validate signals
    if not isinstance(signals, list):
        raise ValueError("Signals must be a list.")

    with get_connection() as conn:

        cursor = conn.execute("""
            INSERT INTO investigation_cases (
                transaction_id,
                risk_score,
                risk_level,
                signals,
                status
            )
            VALUES (?, ?, ?, ?, 'PENDING_REVIEW')
        """, (
            transaction_id,
            risk_score,
            risk_level.upper(),
            json.dumps(signals),
        ))

        return cursor.lastrowid


def get_investigation_case(case_id: int):
    """Retrieve an investigation case by its ID."""

    with get_connection() as conn:

        row = conn.execute("""
            SELECT *
            FROM investigation_cases
            WHERE id = ?
        """, (case_id,)).fetchone()

        if not row:
            return None

        result = dict(row)

        result["signals"] = json.loads(
            result["signals"]
        )

        return result


# --------------------------------------------------
# HUMAN REVIEW OPERATIONS
# --------------------------------------------------

def update_case_status(
    case_id: int,
    status: str,
    human_decision: str,
    report: str | None = None,
):
    """Record a human review decision."""

    allowed_statuses = {
        "APPROVED",
        "REJECTED",
        "ESCALATED",
    }

    if (
        isinstance(case_id, bool)
        or not isinstance(case_id, int)
        or case_id <= 0
    ):
        raise ValueError(
            "Case ID must be a positive integer."
        )

    if status not in allowed_statuses:
        raise ValueError("Invalid case status.")

    if human_decision not in allowed_statuses:
        raise ValueError("Invalid human decision.")

    if status != human_decision:
        raise ValueError(
            "Case status must match the human decision."
        )

    if report is not None and not isinstance(report, str):
        raise ValueError(
            "Investigation report must be a string."
        )

    with get_connection() as conn:

        cursor = conn.execute("""
            UPDATE investigation_cases
            SET
                status = ?,
                human_decision = ?,
                investigation_report = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            status,
            human_decision,
            report,
            case_id,
        ))

        if cursor.rowcount == 0:
            raise ValueError(
                f"Case {case_id} not found."
            )


# --------------------------------------------------
# DIRECT EXECUTION
# --------------------------------------------------

if __name__ == "__main__":
    initialize_database()
