## Quantitative Trading Framework: Bollinger-MACD Strategy

> **Author:** Ziwei Tang  
> **Date:** May 2026  
> **Language:** Python 3.10+  

## Overview

Welcome to the **Bollinger-MACD Trading Framework**. This project implements a robust, modularized algorithmic trading system designed to capture market alpha using a hybrid approach of trend-following and mean-reversion. 

Built from scratch with Python, this framework features a **vectorized backtesting engine, dynamic state-machine signal generation, and comprehensive performance visualization**, demonstrating a complete quantitative research workflow. 

##  Key Features

- **Hybrid Signal Generation:** Combines Bollinger Bands (volatility/mean-reversion), MACD (momentum), and Volume Moving Averages (confirmation) to generate high-probability trade setups.
- **Robust Backtesting Engine:** A custom-built, vectorized backtester that accounts for real-world trading constraints including initial capital, commission fees, and slippage.
- **Strict Risk Management:** Hard-coded logic for trailing Stop-Loss and Take-Profit limits to preserve capital.
- **Performance Analytics:** Calculates institutional-grade metrics including CAGR, Maximum Drawdown, Sharpe Ratio, Sortino Ratio, and Calmar Ratio.
- **Modular Architecture:** Clean software design separating data ingestion, strategy logic, trade execution, and visualization.

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

## Strategic Logic 

The strategy strictly ensures that the portfolio can only hold one directional position at a time (Flat or Long, no short).

Entry Signal (Buy):
Close Price > Upper Bollinger Band (Breakout)
MACD > Signal Line (Bullish Momentum)
Volume > Volume SMA * Threshold (Volume Confirmation)
Exit Signal (Sell):
Close Price < Middle Bollinger Band (Loss of Trend) OR
MACD < Signal Line (Momentum Divergence)
Hard Stop-Loss (e.g., -5%) or Take-Profit (e.g., +12%) hit.

## Quick Start

1. Clone de repository
git clone https://github.com/ZiweiTANG0/BollingerMACD_Quantitative_Investment.git

cd BollingerMACD_Quantitative_Investment

2. Install dependencies 
pip install -r requirements.txt

3. Execute Backtest
python main.py
