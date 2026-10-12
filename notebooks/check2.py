from week2 import load_prices
import sys
import os

# Append the relative path to the week2 folder
sys.path.append(os.path.abspath("week2"))

# 1. Load the data using your reusable function
df = load_prices("week2/data/processed/prices.parquet")

# 2. Group by ticker to scan for row counts and date ranges
sanity_check = df.groupby('ticker').agg(
    first_date=('date', 'min'),
    last_date=('date', 'max'),
    total_days=('date', 'count')
).sort_values('total_days')

print("--- Tickers with the fewest rows (Recent listings or missing data) ---")
print(sanity_check.head(10))

# 3. Check for unexpected missing tickers (dropped because they were empty)
from week2.config import LQ45_TICKERS
missing_tickers = set(LQ45_TICKERS) - set(df['ticker'].unique())
print(f"\nMissing tickers entirely: {missing_tickers}")