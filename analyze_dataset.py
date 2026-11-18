import pandas as pd
from pathlib import Path

DATA_PATH = Path(
    "data/raw/synthetic_mobile_money_transaction_dataset.csv"
)

df = pd.read_csv(DATA_PATH)

print("\n========== FRAUD DISTRIBUTION ==========")
print(df["isFraud"].value_counts())
print("\nFraud percentage:")
print(df["isFraud"].value_counts(normalize=True) * 100)

print("\n========== TRANSACTION TYPES ==========")
print(df["transactionType"].value_counts())

print("\n========== FRAUD BY TRANSACTION TYPE ==========")
print(
    df.groupby("transactionType")["isFraud"]
    .agg(["count", "sum", "mean"])
    .sort_values("mean", ascending=False)
)

print("\n========== AMOUNT STATISTICS ==========")
print(df["amount"].describe())

print("\n========== FRAUD AMOUNT STATISTICS ==========")
print(
    df.groupby("isFraud")["amount"]
    .describe()
)

print("\n========== TRANSACTION STEP ==========")
print(df["step"].describe())