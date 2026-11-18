import pandas as pd
from pathlib import Path

DATA_PATH = Path(
    "data/raw/synthetic_mobile_money_transaction_dataset.csv"
)

df = pd.read_csv(DATA_PATH)

# Sender transaction statistics
sender_stats = df.groupby("initiator").agg(
    total_transactions=("isFraud", "count"),
    fraud_transactions=("isFraud", "sum"),
    total_amount=("amount", "sum")
)

sender_stats["fraud_rate"] = (
    sender_stats["fraud_transactions"]
    / sender_stats["total_transactions"]
)

# Recipient transaction statistics
recipient_stats = df.groupby("recipient").agg(
    total_transactions=("isFraud", "count"),
    fraud_transactions=("isFraud", "sum"),
    total_amount=("amount", "sum")
)

recipient_stats["fraud_rate"] = (
    recipient_stats["fraud_transactions"]
    / recipient_stats["total_transactions"]
)

print("\n========== SENDER ACCOUNT ANALYSIS ==========")
print(sender_stats.describe())

print("\nTop 10 senders by fraud transaction count:")
print(
    sender_stats.sort_values(
        "fraud_transactions",
        ascending=False
    ).head(10)
)

print("\n========== RECIPIENT ACCOUNT ANALYSIS ==========")
print(recipient_stats.describe())

print("\nTop 10 recipients by fraud transaction count:")
print(
    recipient_stats.sort_values(
        "fraud_transactions",
        ascending=False
    ).head(10)
)