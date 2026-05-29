# Import data 
from strategy import download_data, BollingerMACDStrategy
from backtest import VectorizedBacktest
from visualize import plot_bollinger_macd, plot_simple_equity_curve

def main():
    print("="*60)
    print("STARTING ALGORITHMIC TRADING SYSTEM")
    print("="*60)

    # 1. download data
    data = download_data('000300.SS', '2016-01-01', '2026-01-01')

    # 2. generate signals 
    strategy = BollingerMACDStrategy(
        bb_window=20, bb_std=2.0, macd_fast=12, macd_slow=26, macd_signal=9, volume_threshold=1.1
    )
    signals_df = strategy.generate_signals(data)

    # 3. run backtest 
    engine = VectorizedBacktest(initial_capital=1000000)
    results = engine.run(data, signals_df['signal'], stop_loss=0.05, take_profit=0.12, verbose=True)
    engine.print_summary(results)

    # 4. visualize
    print("Generating visualizations...")
    plot_bollinger_macd(data, signals_df)
    plot_simple_equity_curve(results)

if __name__ == "__main__":
    main()
