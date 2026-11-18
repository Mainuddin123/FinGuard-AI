import pandas as pd
from pathlib import Path

DATA_PATH = Path(
    "data/raw/synthetic_mobile_money_transaction_dataset.csv"
)

df = pd.read_csv(DATA_PATH)

# Expected balance changes
df["sender_expected_balance"] = (
    df["oldBalInitiator"] - df["amount"]
)

df["recipient_expected_balance"] = (
    df["oldBalRecipient"] + df["amount"]
)

# Actual vs expected differences
df["sender_balance_error"] = (
    df["newBalInitiator"] - df["sender_expected_balance"]
)

df["recipient_balance_error"] = (
    df["newBalRecipient"] - df["recipient_expected_balance"]
)

# Balance inconsistency flags
df["sender_balance_mismatch"] = (
    df["sender_balance_error"].abs() > 0.01
)

df["recipient_balance_mismatch"] = (
    df["recipient_balance_error"].abs() > 0.01
)

print("\n========== BALANCE MISMATCH BY FRAUD LABEL ==========")

for column in [
    "sender_balance_mismatch",
    "recipient_balance_mismatch",
]:
    print(f"\n{column}")
    print(
        df.groupby("isFraud")[column]
        .agg(["count", "sum", "mean"])
    )

print("\n========== NEGATIVE SENDER BALANCE ==========")

df["negative_sender_balance"] = (
    df["newBalInitiator"] < 0
)

print(
    df.groupby("isFraud")["negative_sender_balance"]
    .agg(["sum", "mean"])
)

print("\n========== FRAUD VS LEGITIMATE BALANCE ERRORS ==========")

print(
    df.groupby("isFraud")[
        ["sender_balance_error", "recipient_balance_error"]
    ].mean()
)