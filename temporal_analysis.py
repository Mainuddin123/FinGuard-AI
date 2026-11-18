import pandas as pd
from pathlib import Path

DATA_PATH = Path(
    "data/raw/synthetic_mobile_money_transaction_dataset.csv"
)

df = pd.read_csv(DATA_PATH)

# Divide the dataset into 12 chronological groups
df["time_group"] = pd.qcut(
    df["step"],
    q=12,
    duplicates="drop"
)

# Fraud distribution across time groups
temporal_stats = (
    df.groupby("time_group", observed=True)
    .agg(
        total_transactions=("isFraud", "count"),
        fraud_transactions=("isFraud", "sum"),
        average_amount=("amount", "mean")
    )
)

temporal_stats["fraud_rate_percent"] = (
    temporal_stats["fraud_transactions"]
    / temporal_stats["total_transactions"]
    * 100
)

print("\n========== FRAUD RATE OVER TIME ==========")
print(temporal_stats.to_string())

# Fraud distribution by individual step
step_stats = (
    df.groupby("step")
    .agg(
        total_transactions=("isFraud", "count"),
        fraud_transactions=("isFraud", "sum")
    )
)

step_stats["fraud_rate_percent"] = (
    step_stats["fraud_transactions"]
    / step_stats["total_transactions"]
    * 100
)

print("\n========== HIGHEST FRAUD-RATE STEPS ==========")
print(
    step_stats.sort_values(
        "fraud_rate_percent",
        ascending=False
    ).head(10)
)

print("\n========== LOWEST FRAUD-RATE STEPS ==========")
print(
    step_stats.sort_values(
        "fraud_rate_percent",
        ascending=True
    ).head(10)
)