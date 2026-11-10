import logging
import os
import pandas as pd
import yfinance as yf
from idxlab.config import LQ45_TICKERS, START_DATE, END_DATE

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def download_and_clean_lq45(start_date: str = START_DATE, end_date: str = END_DATE):
    yf_tickers = [f"{t}.JK" for t in LQ45_TICKERS]
    
    logging.info(f"Downloading historical data from {start_date} to {end_date}...")
    raw_data = yf.download(
        tickers=yf_tickers,
        start=start_date,
        end=end_date,
        interval="1d",
        group_by="ticker",
        auto_adjust=False,
        progress=False,
    )

    processed_dfs = []
    downloaded_tickers = set()

    for ticker in LQ45_TICKERS:
        yf_ticker = f"{ticker}.JK"

        # Check if ticker exists in downloaded columns
        if isinstance(raw_data.columns, pd.MultiIndex):
            if yf_ticker not in raw_data.columns.levels[0]:
                logging.warning(
                    f"[SKIP WARNING] Ticker '{ticker}' was not returned by yfinance. "
                    f"Confirm if IPO/listing occurred after {end_date} (e.g., AADI listed in late 2024)."
                )
                continue
            df = raw_data[yf_ticker].copy().dropna(how="all")
        else:
            df = raw_data.copy().dropna(how="all")

        if df.empty or "Close" not in df.columns or df["Close"].isna().all():
            logging.warning(
                f"[SKIP WARNING] Ticker '{ticker}' returned zero valid price rows between {start_date} and {end_date}. Skipping."
            )
            continue

        downloaded_tickers.add(ticker)

        # 1. Store unadjusted close and calculate volume value
        df["raw_close"] = df["Close"]
        df["value_traded"] = df["raw_close"] * df["Volume"]

        # 2. Back-calculate split/dividend adjustments for OHL
        adj_ratio = df["Adj Close"] / df["Close"]
        df["open"] = df["Open"] * adj_ratio
        df["high"] = df["High"] * adj_ratio
        df["low"] = df["Low"] * adj_ratio
        df["close"] = df["Adj Close"]

        # 3. Format to match DATA_CONTRACT.md
        df["volume"] = df["Volume"]
        df["ticker"] = ticker
        
        # Rule: Flag zero-volume rows as suspended
        df["is_suspended"] = df["volume"] == 0

        # Reset index to make Date a column
        df = df.reset_index()
        df = df.rename(columns={"Date": "date", "index": "date"})

        contract_cols = [
            "date", "ticker", "open", "high", "low", "close",
            "volume", "raw_close", "value_traded", "is_suspended"
        ]
        processed_dfs.append(df[contract_cols])

    missing_tickers = set(LQ45_TICKERS) - downloaded_tickers
    if missing_tickers:
        logging.warning(f"Missing tickers from universe: {sorted(list(missing_tickers))}")

    if not processed_dfs:
        raise ValueError("No ticker data was successfully downloaded.")

    final_df = pd.concat(processed_dfs, ignore_index=True)
    final_df["date"] = pd.to_datetime(final_df["date"])
    final_df = final_df.sort_values(by=["date", "ticker"]).reset_index(drop=True)

    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "prices.parquet")
    final_df.to_parquet(file_path, index=False)
    logging.info(f"Saved {len(final_df)} rows for {len(downloaded_tickers)} tickers to {file_path}")


if __name__ == "__main__":
    download_and_clean_lq45()