import pandas as pd

EXPECTED_COLUMNS = [
    "date", "ticker", "open", "high", "low", "close",
    "volume", "raw_close", "value_traded", "is_suspended",
]


def test_sample_matches_data_contract():
    df = pd.read_parquet("data/sample/prices_sample.parquet")
    assert list(df.columns) == EXPECTED_COLUMNS
    assert len(df) > 0
    assert df["ticker"].nunique() == 5