## Quantitative Trading Framework: Bollinger-MACD Strategy

> **Author:** Ziwei Tang  
> **Date:** May 2026  
> **Language:** Python 3.10+  

## Overview

Welcome to the **Bollinger-MACD Trading Framework**. 
This project presents the Bollinger-MACD Trading Framework, a modular, fully vectorized algorithmic trading system built in Python. It implements a hybrid quantitative strategy that synthesizes two complementary market paradigms—trend-following and mean-reversion—to identify statistically significant trading opportunities.
Designed as an end-to-end quantitative research workflow, the framework features a state-machine-driven signal generation,custom-built backtesting engine,  and comprehensive performance visualization. It demonstrates how mathematical indicators can be operationalized into a robust, risk-controlled trading system, with full accounting for real-world financial market frictions（comission fee, slippage).


##  Key Features

- **Hybrid Multi‑Factor Strategy**
  Integrates Bollinger Bands for mean‑reversion detection, MACD for trend and momentum identification, and volume‑weighted moving averages for signal validation. The combined rule‑based framework enhances signal reliability and reduces market noise.

- **10‑Year Cross‑Cycle Validation**
  Rigorously backtested over a full 10‑year historical period, delivering stable performance across bull, bear, and sideways market regimes. The strategy achieves positive cumulative returns and consistent alpha generation while maintaining controlled drawdowns.

- **Realistic Backtesting Engine**
  Implements a complete transaction simulation pipeline with initial capital constraints, tradable order execution, transaction costs, and price slippage. Designed to eliminate look‑ahead bias and ensure reproducible, out‑of‑sample results.

- **Systematic Risk Management**
  Embeds built‑in risk controls including trailing stop‑loss and take‑profit mechanisms to dynamically limit downside exposure and lock in accumulated returns, improving risk‑adjusted performance metrics.

- **Standardized Performance Analytics**
  Computes institutional‑grade evaluation metrics including CAGR, Sharpe ratio, Sortino ratio, maximum drawdown, and cumulative excess return versus benchmarks, enabling rigorous quantitative assessment of strategy efficiency.
  
##  Project Structure

The repository follows a professional quantitative software architecture:

```text
 Bollinger-MACD-Strategy
 ┣ main.py             # System entry point; orchestrates the workflow
 ┣ strategy.py         # Data download, indicator calculations, and signal logic
 ┣ backtest.py         # Trade execution, P&L calculations, and metric scoring
 ┣ visualize.py        # Matplotlib-based generation of equity curves and charts
 ┣ requirements.txt    # Python package dependencies
 ┗ README.md           # Project documentation
```

##  Project Structure

The strategy strictly ensures that the portfolio can only hold one directional position at a time (Flat or Long, no short).
```text
Entry Signal (Buy):
Close Price > Upper Bollinger Band (Breakout)
MACD > Signal Line (Bullish Momentum)
Volume > Volume SMA * Threshold (Volume Confirmation)
Exit Signal (Sell):
Close Price < Middle Bollinger Band (Loss of Trend) OR
MACD < Signal Line (Momentum Divergence)
Hard Stop-Loss (e.g., -5%) or Take-Profit (e.g., +12%) hit.
```
##  Quick Start

1. Clone de repository
git clone https://github.com/ZiweiTANG0/BollingerMACD_Quantitative_Investment.git
cd BollingerMACD_Quantitative_Investment

2. Install dependencies 
pip install -r requirements.txt

3. Execute Backtest
python main.py
