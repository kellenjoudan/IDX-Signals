"""Data Validation Module for IDX Lab.

Merges previous check.py and check2.py checks into a unified validator script.
Run via: python -m idxlab.data.validate
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from idxlab.config import LQ45_TICKERS

DATA_PATH = Path("data/processed/prices.parquet")
REPORT_PATH = Path("docs/results/data_quality.md")


def load_prices(filepath: Path = DATA_PATH) -> pd.DataFrame:
    """Load cleaned Parquet price dataset."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}. Run `python -m idxlab.data.download` first.")
    df = pd.read_parquet(filepath)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values(by=["ticker", "date"]).reset_index(drop=True)


def check_missing_universe(df: pd.DataFrame, expected_tickers: list) -> list:
    """Find universe tickers missing entirely from the dataset."""
    if not expected_tickers:
        return []
    present_tickers = set(df["ticker"].unique())
    return sorted(list(set(expected_tickers) - present_tickers))


def check_short_histories(df: pd.DataFrame, threshold_ratio: float = 0.8) -> pd.DataFrame:
    """Find tickers with row count significantly lower than max universe history."""
    counts = df.groupby("ticker").agg(
        first_date=("date", "min"),
        last_date=("date", "max"),
        row_count=("date", "count")
    ).reset_index()
    
    max_rows = counts["row_count"].max()
    short_df = counts[counts["row_count"] < (max_rows * threshold_ratio)].copy()
    return short_df.sort_values("row_count")


def check_zero_volume_days(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Find zero-volume days per ticker and update is_suspended state."""
    df["is_suspended"] = df["volume"] == 0
    zero_vol_rows = df[df["volume"] == 0][["date", "ticker", "close", "raw_close", "volume"]].copy()
    
    summary = zero_vol_rows.groupby("ticker").agg(
        zero_vol_count=("date", "count"),
        dates=("date", lambda x: [d.strftime("%Y-%m-%d") for d in x])
    ).reset_index().sort_values("zero_vol_count", ascending=False)
    
    return zero_vol_rows, summary


def check_trading_gaps(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
    """Separate single-ticker missing data gaps from market-wide exchange closures."""
    market_active_dates = set(df["date"].unique())
    single_ticker_gaps = []

    for ticker, group in df.groupby("ticker"):
        group_dates = set(group["date"])
        first_date = group["date"].min()
        last_date = group["date"].max()

        expected_dates = {d for d in market_active_dates if first_date <= d <= last_date}
        missing_dates = expected_dates - group_dates

        for m_date in sorted(missing_dates):
            single_ticker_gaps.append({
                "ticker": ticker,
                "missing_date": m_date.strftime("%Y-%m-%d")
            })

    gap_df = pd.DataFrame(single_ticker_gaps)
    return gap_df, sorted([d.strftime("%Y-%m-%d") for d in market_active_dates])


def check_price_jumps(df: pd.DataFrame, threshold: float = 0.35) -> pd.DataFrame:
    """Identify single-day price moves exceeding +/- 35%."""
    df = df.copy()
    df["prev_close"] = df.groupby("ticker")["close"].shift(1)
    df["daily_return"] = (df["close"] - df["prev_close"]) / df["prev_close"]

    jumps = df[df["daily_return"].abs() > threshold].copy()
    jumps["return_pct"] = (jumps["daily_return"] * 100).round(2)
    jumps["date_str"] = jumps["date"].dt.strftime("%Y-%m-%d")

    cols = ["date_str", "ticker", "prev_close", "close", "return_pct", "volume"]
    return jumps[cols].rename(columns={"date_str": "date"}).sort_values("return_pct", ascending=False)


def generate_markdown_report(
    df: pd.DataFrame,
    missing_universe: list,
    short_hist: pd.DataFrame,
    zero_vol_summary: pd.DataFrame,
    single_gaps: pd.DataFrame,
    price_jumps: pd.DataFrame,
    output_path: Path = REPORT_PATH,
):
    """Write data quality report to markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write("# Data Quality Report\n\n")
        f.write(f"**Generated Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Records:** {len(df):,} | **Unique Tickers:** {df['ticker'].nunique()} | ")
        f.write(f"**Date Range:** {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}\n\n")

        f.write("## 1. Missing Universe Tickers\n")
        if missing_universe:
            f.write(f"The following {len(missing_universe)} ticker(s) were missing entirely from download:\n")
            for t in missing_universe:
                f.write(f"- `{t}` (Listed after download `END_DATE`, e.g., AADI)\n")
        else:
            f.write("All target universe tickers are present.\n")
        f.write("\n")

        f.write("## 2. Short History Tickers (<80% max rows)\n")
        if not short_hist.empty:
            f.write(short_hist.to_markdown(index=False) + "\n")
        else:
            f.write("No short history tickers detected.\n")
        f.write("\n")

        f.write("## 3. Zero-Volume Days & Suspensions\n")
        f.write("*`is_suspended` Rule: `is_suspended = True` when daily volume == 0.*\n\n")
        if not zero_vol_summary.empty:
            f.write(f"Total tickers affected: {len(zero_vol_summary)}\n\n")
            f.write(zero_vol_summary.to_markdown(index=False) + "\n")
        else:
            f.write("Zero zero-volume days detected.\n")
        f.write("\n")

        f.write("## 4. Single-Ticker Trading Gaps\n")
        f.write("*(Market-wide exchange closures like Lebaran are excluded)*\n\n")
        if not single_gaps.empty:
            f.write(f"Found {len(single_gaps)} single-ticker gap day(s):\n\n")
            f.write(single_gaps.to_markdown(index=False) + "\n")
        else:
            f.write("No single-ticker trading gaps found.\n")
        f.write("\n")

        f.write("## 5. Single-Day Price Jumps (>35% move)\n")
        if not price_jumps.empty:
            f.write(f"Found {len(price_jumps)} price jump anomaly candidate(s):\n\n")
            f.write(price_jumps.to_markdown(index=False) + "\n")
        else:
            f.write("No extreme single-day price jumps detected.\n")
        f.write("\n")


def run_validation():
    print("--- Running Data Validation Engine ---")
    df = load_prices()

    missing_universe = check_missing_universe(df, LQ45_TICKERS)
    short_hist = check_short_histories(df)
    _, zero_vol_summary = check_zero_volume_days(df)
    single_gaps, _ = check_trading_gaps(df)
    price_jumps = check_price_jumps(df)

    generate_markdown_report(
        df, missing_universe, short_hist, zero_vol_summary, single_gaps, price_jumps
    )

    print(f"Validation complete! Report written to {REPORT_PATH}")


if __name__ == "__main__":
    run_validation()