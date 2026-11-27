from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

from idxlab.backtest.costs import LOT_SIZE, CostModel


@dataclass
class Position:
    ticker: str
    entry_date: pd.Timestamp
    entry_price: float  # price paid per share, after slippage
    lots: int
    days_held: int = 0  # trading days since entry; the entry day itself is 0
    highest_price: float = 0.0  # highest close since entry

    @property
    def shares(self) -> int:
        return self.lots * LOT_SIZE


class Portfolio:
    """Cash plus open positions. Every trade goes through buy() or sell()."""

    def __init__(self, cash: float, costs: CostModel):
        self.cash = float(cash)
        self.costs = costs
        self.positions: dict[str, Position] = {}
        self.trades: list[dict] = []

    def buy(self, date, ticker: str, price: float, lots: int) -> None:
        if lots <= 0:
            return
        if ticker in self.positions:
            raise ValueError(f"already holding {ticker}")
        exec_price = self.costs.buy_price(price)
        value = lots * LOT_SIZE * exec_price
        fee = self.costs.buy_cost(value)
        if value + fee > self.cash + 1e-6:
            raise ValueError(f"not enough cash to buy {lots} lots of {ticker}")
        self.cash -= value + fee
        self.positions[ticker] = Position(
            ticker=ticker,
            entry_date=pd.Timestamp(date),
            entry_price=exec_price,
            lots=lots,
            highest_price=exec_price,
        )
        self.trades.append(
            {"date": pd.Timestamp(date), "ticker": ticker, "side": "BUY",
             "lots": lots, "price": exec_price, "value": value, "cost": fee}
        )

    def sell(self, date, ticker: str, price: float) -> None:
        pos = self.positions.pop(ticker)
        exec_price = self.costs.sell_price(price)
        value = pos.shares * exec_price
        cost = self.costs.sell_cost(value)
        self.cash += value - cost
        self.trades.append(
            {"date": pd.Timestamp(date), "ticker": ticker, "side": "SELL",
             "lots": pos.lots, "price": exec_price, "value": value, "cost": cost}
        )

    def end_of_day(self, date, closes: Mapping[str, float]) -> None:
        """Update days held and highest close for every open position."""
        for ticker, pos in self.positions.items():
            if pd.Timestamp(date) > pos.entry_date:
                pos.days_held += 1
            pos.highest_price = max(pos.highest_price, float(closes[ticker]))

    def market_value(self, closes: Mapping[str, float]) -> float:
        return sum(p.shares * float(closes[t]) for t, p in self.positions.items())

    def equity(self, closes: Mapping[str, float]) -> float:
        return self.cash + self.market_value(closes)

    def trades_frame(self) -> pd.DataFrame:
        cols = ["date", "ticker", "side", "lots", "price", "value", "cost"]
        return pd.DataFrame(self.trades, columns=cols)