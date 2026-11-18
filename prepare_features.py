import pandas as pd
import numpy as np
from pathlib import Path

INPUT_PATH = Path(
    "data/raw/synthetic_mobile_money_transaction_dataset.csv"
)

OUTPUT_PATH = Path(
    "data/processed/transactions_features.csv"
)

# Load dataset
df = pd.read_csv(INPUT_PATH)

# Preserve ground-truth target separately
target = df["isFraud"].copy()

# Feature engineering
features = df.drop(columns=["isFraud"]).copy()

# Sender balance changes
features["sender_balance_change"] = (
    features["oldBalInitiator"]
    - features["newBalInitiator"]
)

# Recipient balance changes
features["recipient_balance_change"] = (
    features["newBalRecipient"]
    - features["oldBalRecipient"]
)

# Expected balance changes
features["sender_balance_error"] = (
    features["newBalInitiator"]
    - (features["oldBalInitiator"] - features["amount"])
)

features["recipient_balance_error"] = (
    features["newBalRecipient"]
    - (features["oldBalRecipient"] + features["amount"])
)

# Balance indicators
features["negative_sender_balance"] = (
    features["newBalInitiator"] < 0
).astype(int)

features["zero_sender_balance"] = (
    features["newBalInitiator"] == 0
).astype(int)

features["zero_recipient_balance"] = (
    features["newBalRecipient"] == 0
).astype(int)

# Amount transformation
features["log_amount"] = np.log1p(features["amount"])

# Save engineered features and target
features["isFraud"] = target

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
features.to_csv(OUTPUT_PATH, index=False)

print("========== FEATURE ENGINEERING ==========")
print("Original shape:", df.shape)
print("Processed shape:", features.shape)
print("\nFeature columns:")
print(features.columns.tolist())

print("\nMissing values:")
print(features.isnull().sum().sum())

print("\nOutput saved to:", OUTPUT_PATH)