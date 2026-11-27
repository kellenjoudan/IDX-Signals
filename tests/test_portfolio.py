import pandas as pd
import pytest

from idxlab.backtest.costs import NO_COSTS, CostModel
from idxlab.backtest.portfolio import Portfolio


def test_buy_then_sell_cash_flow():
    c = CostModel(buy_fee=0.001, sell_fee=0.001, sell_tax=0.002, slippage=0)
    pf = Portfolio(1_000_000, c)
    pf.buy("2024-01-02", "AAA", 1000, lots=3)
    # 300 shares * 1,000 = 300,000 plus 0.1% fee = 300
    assert pf.cash == pytest.approx(699_700)
    pf.sell("2024-01-10", "AAA", 1100)
    # 300 * 1,100 = 330,000 minus (0.1% + 0.2%) = 990
    assert pf.cash == pytest.approx(1_028_710)
    assert pf.positions == {}
    assert list(pf.trades_frame()["side"]) == ["BUY", "SELL"]


def test_cannot_buy_without_cash():
    pf = Portfolio(100_000, NO_COSTS)
    with pytest.raises(ValueError):
        pf.buy("2024-01-02", "AAA", 1000, lots=2)


def test_days_held_and_highest_price():
    pf = Portfolio(1_000_000, NO_COSTS)
    pf.buy("2024-01-02", "AAA", 1000, lots=1)
    pf.end_of_day("2024-01-02", {"AAA": 1000})  # entry day
    assert pf.positions["AAA"].days_held == 0
    pf.end_of_day("2024-01-03", {"AAA": 1200})
    pf.end_of_day("2024-01-04", {"AAA": 1100})
    pos = pf.positions["AAA"]
    assert pos.days_held == 2
    assert pos.highest_price == 1200


def test_equity_is_cash_plus_market_value():
    pf = Portfolio(1_000_000, NO_COSTS)
    pf.buy(pd.Timestamp("2024-01-02"), "AAA", 1000, lots=2)
    assert pf.equity({"AAA": 1500}) == pytest.approx(1_000_000 + 2 * 100 * 500)