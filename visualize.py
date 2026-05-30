import matplotlib.pyplot as plt

def plot_bollinger_macd(data, signals):
    fig, (ax1, ax2) = plt.subplots(2, figsize=(14, 10), sharex=True)
    ax1.plot(data.index, data['close'], label='Close Price', color='blue')
    ax1.plot(data.index, signals['bb_upper'], label='Upper Band', color='red', linestyle='--')
    ax1.plot(data.index, signals['bb_lower'], label='Lower Band', color='green', linestyle='--')

    ax1.plot(data[signals['signal'] == 1].index, data['close'][signals['signal'] == 1], '^', markersize=10, color='g', label='Buy Signal')
    ax1.plot(data[signals['signal'] == -1].index, data['close'][signals['signal'] == -1], 'v', markersize=10, color='r', label='Sell Signal')

    ax1.set_title('Bollinger Bands and Buy/Sell Signals', fontsize=15)
    ax1.legend()
    ax1.grid()

    ax2.plot(data.index, signals['macd'], label='MACD', color='blue')
    ax2.plot(data.index, signals['macd_signal'], label='Signal Line', color='orange')
    ax2.axhline(0, color='black', linestyle='--', lw=1)
    ax2.set_title('MACD', fontsize=15)
    ax2.legend()

    plt.xlabel('Date')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def plot_simple_equity_curve(results):
    data = results['data']
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(data.index, data['total'], label='Strategy', linewidth=2)
    initial = data['total'].iloc[0]
    benchmark = data['benchmark_cum'] * initial
    ax.plot(data.index, benchmark, label='Benchmark', linewidth=2, alpha=0.7)
    ax.set_title('Equity Curve', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
