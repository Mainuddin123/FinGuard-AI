import pandas as pd
from pathlib import Path

DATA_PATH = Path(
    "data/raw/synthetic_mobile_money_transaction_dataset.csv"
)

df = pd.read_csv(DATA_PATH)

# Separate fraudulent and legitimate transactions
fraud = df[df["isFraud"] == 1]
legitimate = df[df["isFraud"] == 0]

print("\n========== FRAUD BY TRANSACTION TYPE ==========")
print(pd.crosstab(
    df["transactionType"],
    df["isFraud"],
    normalize="index"
) * 100)

print("\n========== SENDER BALANCE ANALYSIS ==========")
print(df.groupby("isFraud")[
    ["oldBalInitiator", "newBalInitiator"]
].mean())

print("\n========== RECIPIENT BALANCE ANALYSIS ==========")
print(df.groupby("isFraud")[
    ["oldBalRecipient", "newBalRecipient"]
].mean())

print("\n========== FRAUD TRANSACTION AMOUNT ==========")
print(fraud["amount"].describe())

print("\n========== LEGITIMATE TRANSACTION AMOUNT ==========")
print(legitimate["amount"].describe())

print("\n========== FRAUD TRANSFER SAMPLE ==========")
print(
    fraud[
        [
            "step",
            "transactionType",
            "amount",
            "oldBalInitiator",
            "newBalInitiator",
            "oldBalRecipient",
            "newBalRecipient",
        ]
    ].head(10).to_string(index=False)
)