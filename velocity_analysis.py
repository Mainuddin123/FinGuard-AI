import pandas as pd
from pathlib import Path

DATA_PATH = Path(
    "data/raw/synthetic_mobile_money_transaction_dataset.csv"
)

df = pd.read_csv(DATA_PATH)

# Sort chronologically
df = df.sort_values("step").copy()

# Transaction counts per sender per step
sender_velocity = (
    df.groupby(["initiator", "step"])
    .size()
    .reset_index(name="transactions_per_step")
)

# Transaction counts per recipient per step
recipient_velocity = (
    df.groupby(["recipient", "step"])
    .size()
    .reset_index(name="transactions_per_step")
)

print("\n========== SENDER VELOCITY ==========")
print(sender_velocity["transactions_per_step"].describe())

print("\n========== RECIPIENT VELOCITY ==========")
print(recipient_velocity["transactions_per_step"].describe())

# Join velocity features to transaction records
df = df.merge(
    sender_velocity,
    on=["initiator", "step"],
    how="left"
)

print("\n========== VELOCITY BY FRAUD LABEL ==========")
print(
    df.groupby("isFraud")["transactions_per_step"]
    .describe()
)

print("\n========== HIGH VELOCITY TRANSACTIONS ==========")
print(
    df[df["transactions_per_step"] >= 5][
        ["step", "initiator", "amount",
         "transactions_per_step", "isFraud"]
    ].head(15)
)