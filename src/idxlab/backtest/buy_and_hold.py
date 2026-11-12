import pandas as pd


def buy_and_hold(prices: pd.DataFrame, initial_capital: float = 1.0) -> pd.Series:
    """Equal-weight buy-and-hold equity curve.

    Rules:
    - Input is a long table with columns: date, ticker, close (adjusted close).
    - Capital is split equally across all tickers on the first date.
    - Nothing is traded afterwards (no rebalancing).
    - No costs, no lot rounding (those arrive in Week 4).
    - Only dates where every ticker has a price are used.

    Returns a Series indexed by date, starting at initial_capital.
    """
    wide = prices.pivot(index="date", columns="ticker", values="close").sort_index()
    wide = wide.dropna()
    growth = wide / wide.iloc[0]          # each stock's value relative to day 1
    equity = initial_capital * growth.mean(axis=1)  # equal weight = average growth
    equity.name = "equity"
    return equity