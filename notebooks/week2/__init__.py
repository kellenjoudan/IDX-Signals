import pandas as pd

def load_prices(filepath="data/processed/prices.parquet"):
    """
    Loads the cleaned LQ45 price data.
    """
    df = pd.read_parquet(filepath)
    # Ensure date is a datetime object
    df['date'] = pd.to_datetime(df['date'])
    return df
