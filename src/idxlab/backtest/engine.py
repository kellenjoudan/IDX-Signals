from dataclasses import dataclass, field

import pandas as pd

from idxlab.backtest.costs import DEFAULT_COSTS, CostModel, max_affordable_lots
from idxlab.backtest.portfolio import Portfolio

@dataclass
class PreparedData:
    open: pd.DataFrame
    close: pd.DataFrame
    volume: pd.DataFrame
    dropped_tickers: list = field(default_factory=list)
    dropped_dates: int = 0


@dataclass
class BacktestResult:
    equity: pd.Series
    trades: pd.DataFrame
    entry_date: pd.Timestamp


def prepare_prices(prices: pd.DataFrame, tickers=None) -> PreparedData:
    """Turn the long price table into wide open/close/volume tables.

    - Optionally keep only the given tickers.
    - Drop tickers without a price on both the first and last date of the window
      (recent listings), and report them.
    - Drop dates where nobody traded (market closures).
    - Drop dates where any remaining ticker has no row, and count them.
    """
    df = prices if tickers is None else prices[prices["ticker"].isin(tickers)]
    start, end = df["date"].min(), df["date"].max()
    span = df.groupby("ticker")["date"].agg(["min", "max"])
    full = span[(span["min"] == start) & (span["max"] == end)].index
    dropped = sorted(set(df["ticker"].unique()) - set(full))
    df = df[df["ticker"].isin(full)]

    day_volume = df.groupby("date")["volume"].sum()
    open_days = day_volume[day_volume > 0].index
    df = df[df["date"].isin(open_days)]

    wide = {
        col: df.pivot(index="date", columns="ticker", values=col).sort_index()
        for col in ("open", "close", "volume")
    }
    before = len(wide["close"])
    keep = wide["close"].dropna().index.intersection(wide["open"].dropna().index)
    keep = keep.intersection(wide["volume"].dropna().index)
    wide = {k: v.loc[keep] for k, v in wide.items()}
    return PreparedData(
        open=wide["open"], close=wide["close"], volume=wide["volume"],
        dropped_tickers=dropped, dropped_dates=before - len(keep),
    )


def _entry_index(volume: pd.DataFrame) -> int:
    """First day after day 0 on which every ticker actually traded."""
    for i in range(1, len(volume)):
        if (volume.iloc[i] > 0).all():
            return i
    raise ValueError("no date where all tickers traded")


def run_buy_and_hold(
    data: PreparedData,
    initial_capital: float = 1_000_000_000,
    costs: CostModel = DEFAULT_COSTS,
    liquidate_at_end: bool = False,
) -> BacktestResult:
    """Equal-weight buy-and-hold with costs and whole lots.

    Rules:
    - The decision is made after day 0's close; buying happens at the OPEN of the
      first later day on which every ticker traded.
    - Cash is split equally across tickers; each share is rounded down to whole lots
      and leftover cash stays as cash.
    - Prices are adjusted prices, so lot counts differ slightly from real life.
    - Equity is marked at the close. With liquidate_at_end, everything is sold at the
      last close and sell costs are charged, so the last point shows cash after exit.
    """
    dates = data.close.index
    entry = _entry_index(data.volume)
    tickers = list(data.close.columns)
    pf = Portfolio(initial_capital, costs)
    equity = {}

    for i, date in enumerate(dates):
        if i == entry:
            alloc = pf.cash / len(tickers)
            for t in tickers:
                price = float(data.open.iloc[i][t])
                pf.buy(date, t, price, max_affordable_lots(alloc, price, costs))
        closes = data.close.iloc[i]
        pf.end_of_day(date, closes)
        if i == len(dates) - 1 and liquidate_at_end:
            for t in list(pf.positions):
                pf.sell(date, t, float(closes[t]))
        equity[date] = pf.equity(closes)

    return BacktestResult(
        equity=pd.Series(equity, name="equity"),
        trades=pf.trades_frame(),
        entry_date=dates[entry],
    )


def run_index_buy_and_hold(
    index: pd.DataFrame,
    dates: pd.DatetimeIndex,
    entry_date,
    initial_capital: float = 1_000_000_000,
    costs: CostModel = DEFAULT_COSTS,
    liquidate_at_end: bool = False,
) -> BacktestResult:
    """Buy-and-hold an index as if it were a fund (fractional units, no lots).

    `index` needs columns: date, open, close. Dates are aligned to `dates`
    (forward-filled where the index has no row), and the buy happens at the open
    of `entry_date`, the same day the stock benchmark buys.
    """
    idx = index.set_index("date").sort_index().reindex(dates).ffill().dropna()
    entry_date = pd.Timestamp(entry_date)
    exec_price = costs.buy_price(float(idx.loc[entry_date, "open"]))
    invested = initial_capital / (1 + costs.buy_fee)
    units = invested / exec_price
    buy_fee = invested * costs.buy_fee

    equity = {}
    for date, row in idx.iterrows():
        equity[date] = initial_capital if date < entry_date else units * float(row["close"])
    equity = pd.Series(equity, name="equity")

    trades = [{"date": entry_date, "ticker": "IHSG", "side": "BUY", "lots": None,
               "price": exec_price, "value": invested, "cost": buy_fee}]
    if liquidate_at_end:
        value = units * costs.sell_price(float(idx["close"].iloc[-1]))
        cost = costs.sell_cost(value)
        equity.iloc[-1] = value - cost
        trades.append({"date": idx.index[-1], "ticker": "IHSG", "side": "SELL", "lots": None,
                       "price": costs.sell_price(float(idx["close"].iloc[-1])),
                       "value": value, "cost": cost})
    return BacktestResult(equity=equity, trades=pd.DataFrame(trades), entry_date=entry_date)