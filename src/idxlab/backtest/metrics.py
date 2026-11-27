import pandas as pd


def total_return(equity: pd.Series) -> float:
    """Total return over the whole period, e.g. 0.25 = +25%."""
    return float(equity.iloc[-1] / equity.iloc[0] - 1)


def cagr(equity: pd.Series) -> float:
    """Compound annual growth rate, using calendar days between first and last date."""
    days = (equity.index[-1] - equity.index[0]).days
    years = days / 365.25
    return float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1)


def max_drawdown(equity: pd.Series) -> float:
    """Worst peak-to-trough loss as a negative number, e.g. -0.10 = -10%."""
    running_peak = equity.cummax()
    return float((equity / running_peak - 1).min())