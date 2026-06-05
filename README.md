# Quantitative Trading Framework: Bollinger–MACD Strategy with Statistical Validation

> **Author:** Ziwei Tang
> **Updated:** June 2026
> **Language:** Python 3.10+
> **Origin:** Extends a strategy first prototyped at a 2019 Python Quantitative Trading Camp (QTC, Shenzhen), rebuilt here as a full research workflow.

## Overview

A modular, vectorized backtesting framework for a hybrid Bollinger-Bands + MACD
trading strategy, built end-to-end in Python: signal generation, a custom
backtesting engine with realistic frictions, performance reporting, and — the
focus of this version — a **statistical validation suite** that tests whether
the strategy's measured performance is real or within the range of noise.

The headline finding is reported honestly below: **once sampling uncertainty
and realistic costs are accounted for, the strategy shows no statistically
robust edge.** Establishing that rigorously, rather than reporting a flattering
return figure, is the purpose of the project.

## What the system does

- **Hybrid signal logic.** Bollinger Bands for mean-reversion, MACD for
  trend/momentum, with a volume filter for confirmation. Long-or-flat only
  (no shorting); one position at a time.
- **Backtesting engine with real frictions.** Transaction costs and slippage,
  capital and position-size constraints, stop-loss / take-profit rules, and a
  day-by-day execution loop designed to avoid look-ahead bias.
- **Standard performance metrics.** CAGR, annualised volatility, Sharpe,
  Sortino, maximum drawdown, win rate, and excess return vs. a buy-and-hold
  CSI 300 (`000300.SS`) benchmark.
- **Statistical validation suite** (`validation.py`): stationarity testing,
  bootstrap confidence intervals, a Monte-Carlo random-timing null, and a
  sub-period stability check.

## Project structure

```
Bollinger-MACD-Strategy
┣ main.py            # Orchestrates: data → signals → backtest → validation → plots
┣ strategy.py        # Data download, indicator calculation, signal logic
┣ backtest.py        # Trade execution, P&L, performance metrics
┣ validation.py      # Statistical validation (stationarity, bootstrap, MC null, stability)
┣ visualize.py       # Equity-curve and indicator charts
┣ requirements.txt   # Dependencies
┗ README.md          # This file
```

## Strategy logic

```
Entry (Buy):  Close > Upper Bollinger Band      (breakout)
              AND MACD > Signal Line            (bullish momentum)
              AND Volume > Volume SMA × 1.1     (volume confirmation)

Exit (Sell):  Close < Middle Bollinger Band     (loss of trend) OR
              MACD < Signal Line                (momentum divergence) OR
              Stop-loss (−5%) or Take-profit (+12%) hit
```

## Headline backtest results (CSI 300, 2016–2026)

| Metric | Strategy | Benchmark (buy & hold) |
|---|---|---|
| Total return (10y) | +4.37% | −9.72% |
| Annualised Sharpe | 0.18 | — |
| Max drawdown | −11.45% | — |
| Win rate | 47.95% | — |


## Statistical validation — honest findings

The strategy was subjected to four standard robustness checks (`validation.py`).

**1. Stationarity (Augmented Dickey–Fuller).** As expected, the price level is
non-stationary (ADF = −1.94, p = 0.32) while returns are stationary
(ADF = −33.25, p < 0.001) — confirming that modelling should be done on returns,
not prices.

**2. Bootstrap confidence intervals (moving-block, L = 11, B = 2000).**
- Annualised Sharpe: **0.18, 95% CI [−1.09, +1.08]** — the interval comfortably
  includes zero.
- Mean daily active return (strategy − benchmark): +6.96e-05, 95% CI
  [−4.14e-04, +5.57e-04], **p = 0.842** — not significant.

The point estimate is positive, but the uncertainty around it is an order of
magnitude larger. The apparent edge is statistically indistinguishable from zero.

**3. Monte-Carlo random-timing null (500 simulations, matched to 17 round-trip
trades).** Against random strategies that trade as often and hold as long, the
real strategy's Sharpe (0.18) beats 93.2% of them; the random-timing
distribution averages a Sharpe of −0.49 (90% range [−1.23, +0.25]). The
empirical p-value is **0.068** — just outside the conventional 5% threshold.
Read honestly: the signal timing is *suggestive* rather than significant. It
does not clear the bar at which one would claim a real edge.

**4. Sub-period stability (four equal windows).** Per-window annualised Sharpe:
**[−1.29, −0.33, +1.36, −0.33]**. The whole-sample result is driven almost
entirely by a single window; the other three are negative. There is no stable,
repeatable edge across time.

## Conclusion

The four checks form a coherent — and, for the strategy, unflattering — picture.
Whole-sample, the strategy is *marginally* better than random timing (it beats
93% of random strategies, but at p = 0.068, short of significance). Yet its
Sharpe ratio is statistically indistinguishable from zero (95% CI
[−1.09, +1.08]), and the sub-period analysis explains the tension: essentially
all of the apparent performance comes from one of four time windows, with the
rest negative. With only ~17 round-trip trades over a decade, the sample is too
small to support a firm claim of edge in any case.

I treat this as the project's most useful result. A simple rule-based signal of
this kind, once realistic frictions, sampling uncertainty and sample size are
accounted for, has no demonstrable, stable edge — and being able to establish
that rigorously is worth more than any single return figure. It is also a large
part of why I want formal training in stochastic processes and statistical
inference.

## Quick start

```bash
# 1. Clone the repository
git clone https://github.com/ZiweiTANG0/BollingerMACD_Quantitative_Investment.git
cd BollingerMACD_Quantitative_Investment

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the full pipeline (backtest + statistical validation)
python main.py
```

Validation is enabled by default. To skip the (slower) Monte-Carlo step, set
`RUN_VALIDATION = False` in `main.py`, or reduce `N_SIM`.
