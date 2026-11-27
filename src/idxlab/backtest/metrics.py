import math

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

def sharpe(equity: pd.Series, risk_free_annual: float = 0.0, periods_per_year: int = 252) -> float:
    """Annualised Sharpe ratio from daily equity. Risk-free rate defaults to 0."""
    returns = equity.pct_change().dropna()
    excess = returns - risk_free_annual / periods_per_year
    std = excess.std(ddof=1)
    if std == 0 or math.isnan(std):
        return float("nan")
    return float(excess.mean() / std * math.sqrt(periods_per_year))


def annual_turnover(trades: pd.DataFrame, equity: pd.Series) -> float:
    """Traded value per year, as a multiple of average equity.

    One-way convention: (total bought + total sold) / 2 / average equity / years.
    """
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    traded = trades["value"].abs().sum()
    return float(traded / 2 / equity.mean() / years)