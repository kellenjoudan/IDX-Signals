import pandas as pd
import pytest

from idxlab.backtest.costs import NO_COSTS, CostModel
from idxlab.backtest.engine import (
    prepare_prices,
    run_buy_and_hold,
    run_index_buy_and_hold,
)


def _prices(rows):
    return pd.DataFrame(rows, columns=["date", "ticker", "open", "close", "volume"]).assign(
        date=lambda d: pd.to_datetime(d["date"])
    )


def _two_tickers():
    dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
    a_close = [100, 110, 121, 121]
    rows = []
    for d, c in zip(dates, a_close):
        rows.append((d, "A", 100, c, 1000))
        rows.append((d, "B", 200, 200, 1000))
    return _prices(rows)


def test_prepare_drops_short_history_and_closed_days():
    df = _two_tickers()
    late = _prices([("2024-01-03", "C", 50, 50, 1000), ("2024-01-04", "C", 50, 50, 1000)])
    closed = _prices([("2024-01-05", "A", 100, 121, 0), ("2024-01-05", "B", 200, 200, 0),
                      ("2024-01-05", "C", 50, 50, 0)])
    data = prepare_prices(pd.concat([df, late, closed]))
    assert data.dropped_tickers == ["C"]
    assert len(data.close) == 4  # the all-zero-volume day is gone


def test_buy_and_hold_no_costs_known_answer():
    data = prepare_prices(_two_tickers())
    res = run_buy_and_hold(data, initial_capital=2_000_000, costs=NO_COSTS)
    # buys at the open of the SECOND date: A 100 lots, B 50 lots
    assert res.entry_date == pd.Timestamp("2024-01-02")
    assert res.equity.iloc[0] == pytest.approx(2_000_000)  # day 0 is all cash
    assert res.equity.iloc[1] == pytest.approx(2_100_000)  # A 1,000,000 -> 1,100,000
    assert res.equity.iloc[2] == pytest.approx(2_210_000)
    assert len(res.trades) == 2


def test_lot_rounding_leaves_cash():
    data = prepare_prices(_two_tickers())
    # 1,050,000 split in two = 525,000 each: A buys 52 lots (520,000), B buys 26 lots (520,000)
    res = run_buy_and_hold(data, initial_capital=1_050_000, costs=NO_COSTS)
    bought = res.trades.set_index("ticker")["lots"]
    assert bought["A"] == 52 and bought["B"] == 26
    # leftover cash = 10,000, so day-0 equity is the full amount and day-1 includes the cash
    assert res.equity.iloc[1] == pytest.approx(10_000 + 520_000 * 1.1 + 520_000)


def test_costs_reduce_final_equity():
    data = prepare_prices(_two_tickers())
    free = run_buy_and_hold(data, 2_000_000, NO_COSTS).equity.iloc[-1]
    paid = run_buy_and_hold(data, 2_000_000, CostModel()).equity.iloc[-1]
    assert paid < free


def test_liquidate_at_end_charges_sell_costs():
    data = prepare_prices(_two_tickers())
    held = run_buy_and_hold(data, 2_000_000, CostModel()).equity.iloc[-1]
    sold = run_buy_and_hold(data, 2_000_000, CostModel(), liquidate_at_end=True)
    assert sold.equity.iloc[-1] < held
    assert (sold.trades["side"] == "SELL").sum() == 2


def test_index_buy_and_hold_no_costs():
    idx = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
        "open": [100.0, 100.0, 110.0],
        "close": [100.0, 110.0, 121.0],
    })
    dates = pd.DatetimeIndex(idx["date"])
    res = run_index_buy_and_hold(idx, dates, "2024-01-02", 1_000_000, NO_COSTS)
    assert res.equity.iloc[0] == pytest.approx(1_000_000)
    assert res.equity.iloc[-1] == pytest.approx(1_210_000)