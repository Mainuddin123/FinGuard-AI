import pandas as pd
from pathlib import Path

DATA_PATH = Path(
    "data/raw/synthetic_mobile_money_transaction_dataset.csv"
)

df = pd.read_csv(DATA_PATH)

print("\n========== AMOUNT BY TRANSACTION TYPE ==========")

print(
    df.groupby("transactionType")["amount"]
    .describe()
)

print("\n========== FRAUD VS LEGITIMATE TRANSFER AMOUNTS ==========")

transfers = df[df["transactionType"] == "TRANSFER"]

print(
    transfers.groupby("isFraud")["amount"]
    .describe()
)

print("\n========== AMOUNT PERCENTILES BY FRAUD LABEL ==========")

percentiles = [0.25, 0.50, 0.75, 0.90, 0.95, 0.99]

print(
    transfers.groupby("isFraud")["amount"]
    .quantile(percentiles)
    .unstack()
)

print("\n========== FRAUD RATE BY AMOUNT RANGE ==========")

transfers = transfers.copy()

transfers["amount_range"] = pd.qcut(
    transfers["amount"],
    q=10,
    duplicates="drop"
)

print(
    transfers.groupby("amount_range", observed=True)
    ["isFraud"]
    .agg(["count", "sum", "mean"])
)