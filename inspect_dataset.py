import pandas as pd
from pathlib import Path

# Dataset path
DATA_PATH = Path(
    "data/raw/synthetic_mobile_money_transaction_dataset.csv"
)

# Load dataset
if not DATA_PATH.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

df = pd.read_csv(DATA_PATH)

# Basic information
print("\n========== DATASET OVERVIEW ==========")
print("Shape:", df.shape)
print("\nFirst 5 records:")
print(df.head())

# Columns and data types
print("\n========== COLUMN INFORMATION ==========")
print(df.columns.tolist())
print(df.dtypes)
df.info()

# Missing values
print("\n========== MISSING VALUES ==========")
print(df.isnull().sum())

# Duplicate records
print("\n========== DUPLICATES ==========")
print("Duplicate rows:", df.duplicated().sum())

# Unique values
print("\n========== UNIQUE VALUES ==========")
print(df.nunique())