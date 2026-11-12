import pandas as pd
import pytest

from idxlab.backtest.buy_and_hold import buy_and_hold
from idxlab.backtest.metrics import cagr, max_drawdown, total_return


def _equity(values):
    idx = pd.date_range("2024-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=idx, dtype=float)


def test_total_return_and_drawdown():
    equity = _equity([100, 110, 99])
    assert total_return(equity) == pytest.approx(-0.01)
    assert max_drawdown(equity) == pytest.approx(-0.10)


def test_cagr_doubling_each_year():
    equity = pd.Series([1.0, 4.0], index=pd.to_datetime(["2020-01-01", "2022-01-01"]))
    assert cagr(equity) == pytest.approx(1.0, abs=0.01)  # 4x in 2 years = +100%/yr


def test_buy_and_hold_equal_weight():
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    prices = pd.DataFrame(
        {
            "date": list(dates) * 2,
            "ticker": ["A", "A", "B", "B"],
            "close": [100, 200, 100, 100],  # A doubles, B flat
        }
    )
    equity = buy_and_hold(prices)
    assert equity.iloc[0] == pytest.approx(1.0)
    assert equity.iloc[-1] == pytest.approx(1.5)  # half the money doubled