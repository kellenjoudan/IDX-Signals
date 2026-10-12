import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 1. Define tickers with IDX suffix
tickers = ["BBCA.JK", "BBRI.JK", "BMRI.JK", "ASII.JK", "UNTR.JK"]

print("Downloading historical data...")
# Download ~5 years of daily OHLCV
data = yf.download(
    tickers=tickers,
    start="2019-01-01",
    end="2024-01-01",
    interval="1d",
    group_by="ticker",
    auto_adjust=False  # We want both unadjusted 'Close' and 'Adj Close'
)

# Display download summary
print("\nDownloaded columns for BBCA:")
print(data["BBCA.JK"].head())

# 2. Extract Close prices for a quick sanity plot
close_prices = pd.DataFrame({ticker.replace(".JK", ""): data[ticker]["Close"] for ticker in tickers})

# Plot
plt.figure(figsize=(12, 6))
for col in close_prices.columns:
    plt.plot(close_prices.index, close_prices[col], label=col)

plt.title("LQ45 Sample (Raw Close Prices: 2019 - 2024)")
plt.xlabel("Date")
plt.ylabel("Price (IDR)")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()