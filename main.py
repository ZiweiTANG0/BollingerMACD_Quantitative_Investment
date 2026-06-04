"""
main.py
=======
Entry point for the Bollinger-MACD trading system.

Pipeline:
    data download -> signal generation -> backtest -> statistical validation
    -> visualisation.

The validation step (4) is the substantive addition: a backtest alone cannot
tell you whether a measured edge is real. Step 4 runs stationarity tests,
moving-block bootstrap confidence intervals, a Monte-Carlo random-timing null,
and a sub-period stability check, and reports whatever it finds.
"""

from strategy import download_data, BollingerMACDStrategy
from backtest import VectorizedBacktest
from visualize import plot_bollinger_macd, plot_simple_equity_curve
from validation import run_all

import json

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
TICKER = '000300.SS'                       # CSI 300 index (also the benchmark)
START, END = '2016-01-01', '2026-01-01'    # ten-year window

STRATEGY_PARAMS = dict(bb_window=20, bb_std=2.0, macd_fast=12, macd_slow=26,
                       macd_signal=9, volume_threshold=1.1)

# Backtest settings are defined ONCE and reused for both the real run and the
# Monte-Carlo null, so the two can never silently drift apart. commission,
# slippage and position_size fall back to the VectorizedBacktest defaults.
BACKTEST_KWARGS = dict(initial_capital=1_000_000)
RUN_PARAMS = dict(stop_loss=0.05, take_profit=0.12)
# NOTE: the Monte-Carlo null re-runs the engine with run()'s default stop_loss
# /take_profit (0.05 / 0.12). If you change RUN_PARAMS above, keep them equal to
# those defaults so the null stays comparable to the real strategy.

RUN_VALIDATION = True                      # set False to skip the (slow) step 4
N_BOOT = 2000                              # bootstrap replications
N_SIM = 500                                # Monte-Carlo random-timing simulations


def main():
    print("=" * 60)
    print("STARTING ALGORITHMIC TRADING SYSTEM")
    print("=" * 60)

    # 1. Download data
    data = download_data(TICKER, START, END)

    # 2. Generate signals
    strategy = BollingerMACDStrategy(**STRATEGY_PARAMS)
    signals_df = strategy.generate_signals(data)

    # 3. Run backtest
    engine = VectorizedBacktest(**BACKTEST_KWARGS)
    results = engine.run(data, signals_df['signal'], verbose=True, **RUN_PARAMS)
    engine.print_summary(results)

    # 4. Statistical validation
    if RUN_VALIDATION:
        report = run_all(
            results, data, signals_df['signal'], VectorizedBacktest,
            backtest_kwargs=BACKTEST_KWARGS, n_boot=N_BOOT, n_sim=N_SIM,
        )
        with open('validation_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print("\nValidation summary written to validation_report.json")

    # 5. Visualise
    print("\nGenerating visualizations...")
    plot_bollinger_macd(data, signals_df)
    plot_simple_equity_curve(results)


if __name__ == "__main__":
    main()
