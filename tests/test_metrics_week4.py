import pandas as pd
import pytest

from idxlab.backtest.metrics import annual_turnover, sharpe


def test_sharpe_of_constant_growth_is_nan_and_of_noisy_is_positive():
    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    flat = pd.Series([100.0] * 5, index=idx)
    assert pd.isna(sharpe(flat))
    noisy = pd.Series([100.0, 101.0, 100.5, 102.0, 103.0], index=idx)
    assert sharpe(noisy) > 0


def test_annual_turnover_known_answer():
    idx = pd.to_datetime(["2024-01-01", "2025-01-01"])
    equity = pd.Series([100.0, 100.0], index=idx)
    trades = pd.DataFrame({"value": [100.0]})  # bought 100 once, never sold
    years = (idx[-1] - idx[0]).days / 365.25
    assert annual_turnover(trades, equity) == pytest.approx(0.5 / years)