
import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path

from src.database.db import DB_PATH, initialize_database


# Project configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]

CSV_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "transactions_features.csv"
)

BATCH_SIZE = 50_000

COLUMNS = [
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

NUMERIC_COLUMNS = [
    "step",
    "amount",
    "oldBalInitiator",
    "newBalInitiator",
    "oldBalRecipient",
    "newBalRecipient",
]


def ingest_transactions():
    """Import transaction records into SQLite in batches."""

    # 1. Validate dataset
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {CSV_PATH}"
        )

    initialize_database()

    total_imported = 0

    # 2. Open database connection
    conn = sqlite3.connect(DB_PATH)

    try:
        # Enable foreign-key enforcement
        conn.execute("PRAGMA foreign_keys = ON")

        # 3. Prevent duplicate full-dataset ingestion
        existing = conn.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

        if existing > 0:
            print(
                f"Database already contains {existing:,} transactions."
            )
            print("Ingestion skipped to prevent duplicates.")
            return

        # 4. Start one atomic ingestion transaction
        conn.execute("BEGIN")

        # 5. Read dataset in batches
        for batch_number, chunk in enumerate(
            pd.read_csv(
                CSV_PATH,
                usecols=lambda column: column in COLUMNS,
                chunksize=BATCH_SIZE,
            ),
            start=1,
        ):

            # Validate required columns
            missing = set(COLUMNS) - set(chunk.columns)

            if missing:
                raise ValueError(
                    f"Dataset is missing columns: {sorted(missing)}"
                )

            # Validate missing values
            if chunk[COLUMNS].isnull().any().any():
                raise ValueError(
                    f"Missing transaction values in batch {batch_number}."
                )

            # Validate numeric values
            numeric_data = chunk[NUMERIC_COLUMNS].to_numpy(
                dtype=float
            )

            if not np.isfinite(numeric_data).all():
                raise ValueError(
                    f"Invalid numeric values in batch {batch_number}."
                )

            # Validate transaction amounts
            if (chunk["amount"] < 0).any():
                raise ValueError(
                    f"Negative transaction amount in batch {batch_number}."
                )

            # Convert records for SQLite insertion
            records = [
                (
                    int(row.step),
                    str(row.transactionType),
                    float(row.amount),
                    str(row.initiator),
                    float(row.oldBalInitiator),
                    float(row.newBalInitiator),
                    str(row.recipient),
                    float(row.oldBalRecipient),
                    float(row.newBalRecipient),
                )
                for row in chunk[COLUMNS].itertuples(index=False)
            ]

            if not records:
                continue

            # Batch insertion
            conn.executemany(
                """
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
                """,
                records,
            )

            total_imported += len(records)

            print(
                f"Batch {batch_number}: "
                f"{total_imported:,} transactions processed"
            )

        # 6. Reject empty datasets
        if total_imported == 0:
            raise ValueError(
                "Dataset contains no transaction records."
            )

        # 7. Commit only after every batch succeeds
        conn.commit()

        print("\nTransaction ingestion completed successfully.")
        print(f"Total imported: {total_imported:,}")
        print(f"Database location: {DB_PATH}")

    except Exception:
        conn.rollback()

        print(
            "\nIngestion failed. "
            "All changes from this ingestion were rolled back."
        )

        raise

    finally:
        conn.close()


if __name__ == "__main__":
    ingest_transactions()
