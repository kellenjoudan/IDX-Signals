# IDX Signals
An end-to-end machine learning project that ranks Indonesian (IDX) LQ45 stocks and
produces daily BUY / HOLD / SELL signals, with honest, cost-aware backtesting.
Built by two undergraduate students for learning and portfolio purposes.

> ⚠️ **Disclaimer:** This project is for learning and portfolio purposes only.
> Nothing here is financial advice.

## Status
🚧 Week 3 of 16 — data pipeline and first backtest. See [docs/journal.md](docs/journal.md) for
weekly progress and [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md) for scope decisions.

## Table of Contents
- [Why this project](#why-this-project)
- [What it does](#what-it-does)
- [Tech stack](#tech-stack)
- [How to run](#how-to-run)
- [Results](#results)
- [Known limitations](#known-limitations)

## Why this project
We're two undergrad students practicing real data engineering, ML, and Git
teamwork on something we care about: the Indonesian stock market. Full details
in [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md).

## What it does
_Coming soon as each phase is built — see the roadmap in docs/PROJECT_SPEC.md._

## Tech stack
Python 3.11 · pandas / numpy · pyarrow (Parquet) · yfinance · scikit-learn ·
XGBoost · SHAP · matplotlib · Streamlit · pytest · ruff · GitHub Actions

## How to run
_Setup instructions will be filled in as each piece becomes runnable._

## Results
All numbers so far are verification runs, not benchmarks. Real benchmarks with costs come in Week 4.

| Run | Period | Total return | CAGR | Max drawdown | Notes |
|---|---|---|---|---|---|
| Equal-weight buy-and-hold, 5 tickers (BBCA, BBRI, BMRI, ASII, UNTR) | 2022-01-03 to 2023-12-29 | 45.8% | 20.9% | -15.5% (2022-07-07) | No costs, dividend-adjusted prices, checked against a hand calculation for BBCA |

## Known limitations
- **Hindsight bias in the universe:** the ticker list is the current LQ45 (October 2026),
  applied to 2019-2023 data. Some stocks joined the index partly because of recent performance.
- **Adjusted prices:** returns include dividends. IHSG is a price index, so comparisons
  with it favor the stocks.
- **Short sample so far:** the verification run covers 5 large stocks over 2 years.
