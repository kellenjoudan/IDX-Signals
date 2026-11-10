import pytest
import pandas as pd
from idxlab.data.validate import (
    check_zero_volume_days,
    check_trading_gaps,
    check_price_jumps,
)


@pytest.fixture
def synthetic_df():
    dates = pd.to_datetime(["2024-01-08", "2024-01-09", "2024-01-11", "2024-01-12"])
    
    df_a = pd.DataFrame({
        "date": dates,
        "ticker": "TKRA",
        "open": [100.0, 101.0, 102.0, 103.0],
        "high": [105.0, 105.0, 105.0, 105.0],
        "low": [99.0, 99.0, 99.0, 99.0],
        "close": [100.0, 101.0, 102.0, 103.0],
        "volume": [1000, 1500, 1200, 1100],
        "raw_close": [100.0, 101.0, 102.0, 103.0],
        "value_traded": [100000.0, 151500.0, 122400.0, 113300.0],
        "is_suspended": [False, False, False, False]
    })

    df_b = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-08", "2024-01-09", "2024-01-12"]),
        "ticker": "TKRB",
        "open": [200.0, 200.0, 300.0],
        "high": [205.0, 200.0, 310.0],
        "low": [195.0, 200.0, 295.0],
        "close": [200.0, 200.0, 300.0],
        "volume": [2000, 0, 2500],
        "raw_close": [200.0, 200.0, 300.0],
        "value_traded": [400000.0, 0.0, 750000.0],
        "is_suspended": [False, True, False]
    })

    return pd.concat([df_a, df_b], ignore_index=True)


def test_zero_volume_days_detection(synthetic_df):
    zero_rows, summary = check_zero_volume_days(synthetic_df)
    assert len(zero_rows) == 1
    assert zero_rows.iloc[0]["ticker"] == "TKRB"
    assert zero_rows.iloc[0]["date"] == pd.Timestamp("2024-01-09")


def test_single_ticker_gap_separation(synthetic_df):
    gap_df, active_dates = check_trading_gaps(synthetic_df)
    assert len(gap_df) == 1
    assert gap_df.iloc[0]["ticker"] == "TKRB"
    assert gap_df.iloc[0]["missing_date"] == "2024-01-11"


def test_price_jump_detection(synthetic_df):
    jumps = check_price_jumps(synthetic_df, threshold=0.35)
    assert len(jumps) == 1
    assert jumps.iloc[0]["ticker"] == "TKRB"
    assert jumps.iloc[0]["return_pct"] == 50.0