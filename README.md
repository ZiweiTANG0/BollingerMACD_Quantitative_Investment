# Quantitative Trading Strategy: From Academic Competition to Production-Grade Implementation

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Author:** Ziwei Tang  
**Original Project:** 2018 Quantitative Investment Training Camp  
**Replication:** May 2026  

---

## Table of Contents

- [Project Overview](#-project-overview)
- [Background Story](#-background-story)
- [Strategy Methodology](#-strategy-methodology)
- [Key Improvements (2018 → 2026)](#-key-improvements-2018--2026)
- [Results & Performance](#-results--performance)
- [Installation & Usage](#-installation--usage)
- [Technical Architecture](#-technical-architecture)
- [Robustness Analysis](#-robustness-analysis)
- [Limitations & Future Work](#-limitations--future-work)
- [Connection to Academic Goals](#-connection-to-academic-goals)
- [References](#-references)

---

## 🎯 Project Overview

This project represents the **evolution of a momentum-based trading strategy** over an 8-year period:
- **2018**: Initial development during undergraduate quantitative investment training
- **2026**: Complete rewrite with industrial best practices and rigorous statistical validation

**Core Strategy:** Bollinger Bands + MACD momentum system for Chinese A-share market (HS300 Index)

**Key Question:** Can a simple technical strategy maintain statistical significance when subjected to proper validation methodologies?

**Answer:** Yes, but with important caveats (see [Robustness Analysis](#-robustness-analysis))

---

## 📚 Background Story

### The Origin (2018)

As an undergraduate majoring in French Literature at Shanghai International Studies University, I participated in a **Quantitative Training Camp** organized by Tsinghua University and China Institution of Innovation. 

Despite my non-quantitative background, our team developed a systematic trading strategy that:
- ✅ Generated 18.5% annual return in backtests (vs. HS300: 12.3%)
- ✅ Won Group Third Place Award 
- ✅ Was featured in an [institutional WeChat article](https://mp.weixin.qq.com/s/M0ABKMYyb9DpPiwkcFJkLg) (8,000+ views)

**Original Article:** (https://mp.weixin.qq.com/s/M0ABKMYyb9DpPiwkcFJkLg)

### The Problem

While the strategy showed promising results, it suffered from typical beginner mistakes:
- No statistical hypothesis testing (is alpha real or luck?)
- Single backtest period (potential overfitting)
- Ignored transaction costs (unrealistic P&L)
- Basic risk management (fixed 5% stop-loss)
- Script-based code (not production-ready)

### The Motivation (2026)

After 5 years working in:
- M&A valuation (L'Oréal, Deloitte)
- Private equity analysis (Invus)
- AI financial model validation (CFA Institute)

I recognized the need to **revisit this foundational project with quantitative rigor**. This replication serves two purposes:

1. **Technical:** Apply industrial best practices learned from professional experience
2. **Academic:** Demonstrate readiness for advanced studies in financial mathematics

---

## Strategy Methodology

### Core Logic

**Market Hypothesis:** Momentum exists in Chinese A-share market due to:
1. Retail investor herding behavior
2. Information diffusion delays
3. Behavioral biases (anchoring, confirmation bias)

### Signal Generation

#### Entry Signals (Long Position)

```python
BUY when ALL conditions met:
1. Price > Bollinger Upper Band (20-day, 2σ)
   → Breakout confirmation
   
2. MACD Line > Signal Line (MACD > MACD_signal)
   → Momentum acceleration (Golden Cross)
   
3. Volume > 20-day Moving Average × 1.2
   → Volume confirmation (reduce false breakouts)
   
4. No existing position

**#### Sell Signals (Long Position)**

SELL when ANY condition met:
1. Price < Bollinger Middle Band
   → Momentum weakening
   
2. MACD Line < Signal Line (Death Cross)
   → Trend reversal
   
3. Stop Loss: Price < Entry × (1 - stop_loss_pct)
   → Default: 5% stop loss
   
4. Take Profit: Price > Entry × (1 + take_profit_pct)
   → Default: 15% take profit

**### Risk Management**
position_size = (portfolio_value × risk_per_trade) / ATR(14)

where:
  risk_per_trade = Dynamic, based on recent market volatility
    - Low vol regime (σ < 15%): risk_per_trade = 2%
    - Medium vol (15% ≤ σ < 25%): risk_per_trade = 1.5%
    - High vol (σ ≥ 25%): risk_per_trade = 1%
  
  ATR(14) = Average True Range over 14 days (volatility proxy)
Rationale: Risk parity approach - maintain constant risk exposure across different market regimes

