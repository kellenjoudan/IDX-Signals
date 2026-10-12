import pandas as pd
import numpy as np
from week2 import load_prices

def run_sanity_check(filepath="week2/data/processed/prices.parquet"):
    print(f"--- Running Sanity Check on {filepath} ---\n")
    df = load_prices(filepath)

    # 1. Total Rows & Universe Summary
    total_tickers = df['ticker'].nunique()
    total_rows = len(df)
    min_date = df['date'].min().strftime('%Y-%m-%d')
    max_date = df['date'].max().strftime('%Y-%m-%d')

    print(f"Date Range: {min_date} to {max_date}")
    print(f"Total Unique Tickers: {total_tickers}")
    print(f"Total Price Rows: {total_rows}\n")

    # 2. Check for Tickers with Few Rows / Late IPOs
    print("=== 1. Ticker Row Count & History Check ===")
    ticker_counts = df.groupby('ticker').agg(
        first_date=('date', 'min'),
        last_date=('date', 'max'),
        row_count=('date', 'count')
    ).reset_index()

    # Find tickers with significantly fewer rows (e.g., less than 80% of max expected history)
    max_history = ticker_counts['row_count'].max()
    short_history = ticker_counts[ticker_counts['row_count'] < (max_history * 0.8)]

    if not short_history.empty:
        print(f"Found {len(short_history)} tickers with shorter history (possible recent listings/IPOs):")
        for _, row in short_history.iterrows():
            print(f"  - {row['ticker']}: {row['row_count']} rows (First: {row['first_date'].strftime('%Y-%m-%d')}, Last: {row['last_date'].strftime('%Y-%m-%d')})")
    else:
        print("All tickers have a full history range!")
    print()

    # 3. Check for Trading Gaps (Missing Days)
    print("=== 2. Trading Gap Detection (> 5 Consecutive Days) ===")
    df = df.sort_values(by=['ticker', 'date'])
    df['prev_date'] = df.groupby('ticker')['date'].shift(1)
    df['gap_days'] = (df['date'] - df['prev_date']).dt.days

    # Identify gaps > 5 calendar days (accounts for standard weekends + market holidays)
    large_gaps = df[df['gap_days'] > 5]

    if not large_gaps.empty:
        print(f"Found {len(large_gaps)} unexpected trading gaps (>5 calendar days):")
        for _, row in large_gaps.iterrows():
            start_gap = row['prev_date'].strftime('%Y-%m-%d')
            end_gap = row['date'].strftime('%Y-%m-%d')
            print(f"  - {row['ticker']}: Gap of {row['gap_days']} days between {start_gap} and {end_gap}")
    else:
        print("No unexpected gaps detected between trading days!")
    print()

    # 4. Check for Suspicious Price Spikes or Drops (> 35% single-day change)
    print("=== 3. Single-Day Price Jump Check (> 35% move) ===")
    df['prev_close'] = df.groupby('ticker')['close'].shift(1)
    df['daily_return'] = (df['close'] - df['prev_close']) / df['prev_close']

    # Flags jump > 35% or < -35% (beyond standard IDX auto-rejection limit bounds)
    spikes = df[df['daily_return'].abs() > 0.35]

    if not spikes.empty:
        print(f"Found {len(spikes)} potential price anomalies/unadjusted split errors:")
        for _, row in spikes.iterrows():
            ret_pct = row['daily_return'] * 100
            print(f"  - {row['ticker']} on {row['date'].strftime('%Y-%m-%d')}: {ret_pct:+.2f}% jump (Close: {row['close']:.2f})")
    else:
        print("No extreme unadjusted price jumps found!")

if __name__ == "__main__":
    run_sanity_check()
