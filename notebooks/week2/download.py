import yfinance as yf
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import os
from config import LQ45_TICKERS

def download_and_clean_lq45():
    # Append .JK for Yahoo Finance API
    yf_tickers = [f"{t}.JK" for t in LQ45_TICKERS]
    
    print("Downloading historical data...")
    # auto_adjust=False ensures we get both 'Close' (raw) and 'Adj Close'
    raw_data = yf.download(
        tickers=yf_tickers,
        start="2019-01-01",
        end="2024-01-01",
        interval="1d",
        group_by="ticker",
        auto_adjust=False
    )
    
    processed_dfs = []
    
    for ticker in LQ45_TICKERS:
        yf_ticker = f"{ticker}.JK"
        df = raw_data[yf_ticker].copy()
        
        # Drop entirely empty rows (weekends/holidays)
        df = df.dropna(how="all").copy()
        if df.empty:
            continue
            
        # 1. Store unadjusted close and calculate volume value
        df['raw_close'] = df['Close']
        df['value_traded'] = df['raw_close'] * df['Volume']
        
        # 2. Back-calculate split/dividend adjustments for OHL
        # yfinance provides Adj Close, so we find the ratio and apply it to Open, High, Low
        adj_ratio = df['Adj Close'] / df['Close']
        df['open'] = df['Open'] * adj_ratio
        df['high'] = df['High'] * adj_ratio
        df['low'] = df['Low'] * adj_ratio
        df['close'] = df['Adj Close']
        
        # 3. Format to match DATA_CONTRACT.md
        df['volume'] = df['Volume']
        df['ticker'] = ticker
        df['is_suspended'] = False # Default placeholder; you will refine this in Week 3
        
        # Reset index to make Date a column, rename to lowercase
        df = df.reset_index()
        df = df.rename(columns={"Date": "date"})
        
        # Select and order only the contracted columns
        contract_cols = [
            "date", "ticker", "open", "high", "low", "close", 
            "volume", "raw_close", "value_traded", "is_suspended"
        ]
        processed_dfs.append(df[contract_cols])

    # Combine all stocks into one long-format table
    final_df = pd.concat(processed_dfs, ignore_index=True)
    
    # Sort chronologically, then by ticker
    final_df = final_df.sort_values(by=["date", "ticker"]).reset_index(drop=True)
    
    # Save as Parquet
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    final_df.to_parquet(f"{output_dir}/prices.parquet", index=False)
    print(f"Saved {len(final_df)} rows to {output_dir}/prices.parquet")

if __name__ == "__main__":
    download_and_clean_lq45()
