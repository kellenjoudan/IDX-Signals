import pandas as pd

df = pd.read_parquet("data/processed/prices.parquet")
tickers = ["BBCA", "BBRI", "BMRI", "ASII", "UNTR"]
sample = df[(df["date"] >= "2022-01-01") & (df["ticker"].isin(tickers))]
sample.to_parquet("data/sample/prices_sample.parquet", index=False)
print(sample.shape)
print(sample["ticker"].value_counts())