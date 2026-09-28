# Project Spec — IDX Signals

This is our agreed scope. Changes to anything below go through an issue + PR so we don't quietly drift.

## Goal
Rank LQ45 stocks and produce daily BUY/HOLD/SELL signals, tested honestly with walk-forward
validation and realistic IDX costs. 

## Universe
- Full universe: LQ45 constituents (list to be finalized in data contract, Week 4)
- Week 1–2 test set (for quick iteration only): BBCA, BBRI, UNTR, ASII, BMRI

## Prediction Target
- Binary classification: will this stock's return over the next 5 trading days be
  higher than the median LQ45 stock's return? (1 = yes, 0 = no)
- We deliberately do NOT predict tomorrow's up/down because it is too noisy, accuracy ignores magnitude of moves.

## Trading Rules
- **Long-only.** SELL means "exit position," never short selling.
- Positions sized in lots of 100 shares.
- Equal-weight positions, max 5–10 concurrent positions.
- **Entry:** score in top K and above a minimum threshold, not already held, passes
  liquidity filter, not suspended, free slot + enough cash.
- **Exit (first rule to trigger wins):** stop-loss → trailing stop → time exit
  (5–10 trading days) → signal exit (rank falls well outside entry threshold).
  Take-profit target is optional and will be tested, not assumed.
- Signals computed after close on day t; trades execute at day t+1's open.

## Costs Included
Brokerage fees, tax on sale, slippage: all set in one config file, applied in
every backtest. 

## Validation Methodology
- Walk-forward only: train on the past, test on the period right after, slide forward.
- Never randomly shuffle data into train/test
- Final holdout period is locked away and evaluated exactly once.

## Out of Scope (v1)
- Short selling
- Intraday trading
- Options/derivatives
- Real-money trading
- Non-LQ45 stocks

## Success Criteria
- Model beats rule-based baselines (MA crossover, RSI, momentum) after costs.
- Model beats IHSG and equal-weight LQ45 benchmarks after costs.
- If neither holds, we say so

## Decision Log
| Date | Decision | Reason |
|------|----------|--------|