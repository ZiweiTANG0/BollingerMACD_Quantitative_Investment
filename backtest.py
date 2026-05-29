import pandas as pd
import numpy as np
from typing import Dict
import warnings
warnings.filterwarnings('ignore')


class VectorizedBacktest:
    """
    Simple and robust backtesting engine
    """
    # Initialize Backtest    
    def __init__(
        self,
        initial_capital: float = 1000000,
        commission: float = 0.00025,
        slippage: float = 0.003,
        position_size: float = 0.8
    ):
        
        self.initial_capital = float(initial_capital)
        self.commission = commission
        self.slippage = slippage
        self.position_size = position_size
    # Run backtest     
    def run(
        self,
        data: pd.DataFrame,
        signals: pd.Series,
        stop_loss: float = 0.05,
        take_profit: float = 0.12,
        verbose: bool = True
    ) -> Dict:
        """
        Args:
            data: OHLCV DataFrame
            signals: Trading signals (1=buy, -1=sell, 0=hold)
            stop_loss: Stop loss percentage
            take_profit: Take profit percentage
            verbose: Print trade details
            
        Returns:
            Dictionary with backtest results
        """
        if verbose:
            print("\n" + "="*60)
            print("BACKTEST EXECUTION")
            print("="*60)
        
        # Prepare data
        df = data.copy()
        
        # Handle signals input
        if isinstance(signals, pd.DataFrame):
            signals = signals['signal']
        
        # Align signals with data
        df['signal'] = 0
        common_index = df.index.intersection(signals.index)
        df.loc[common_index, 'signal'] = signals.loc[common_index].values
        
        if verbose:
            buy_count = (df['signal'] == 1).sum()
            sell_count = (df['signal'] == -1).sum()
            print(f"\nSignals loaded: {buy_count} BUY, {sell_count} SELL")
        
        # Initialize tracking variables
        position = 0  # 0=no position, 1=holding
        cash = self.initial_capital
        shares = 0
        entry_price = 0.0
        trade_count = 0
        
        # Track portfolio value over time
        portfolio_values = []
        trade_log = []
        
        # Main backtest loop
        for date, row in df.iterrows():
            price = row['close']
            signal = row['signal']
            
            # Check stop loss / take profit if holding
            if position == 1 and entry_price > 0:
                pnl_pct = (price - entry_price) / entry_price
                
                if pnl_pct <= -stop_loss:
                    signal = -1  # Force sell
                    if verbose:
                        print(f"  [STOP LOSS] @ {date.date()}: {pnl_pct*100:.2f}%")
                
                elif pnl_pct >= take_profit:
                    signal = -1  # Force sell
                    if verbose:
                        print(f"  [TAKE PROFIT] @ {date.date()}: {pnl_pct*100:.2f}%")
            
            # Execute BUY
            if signal == 1 and position == 0:
                buy_price = price * (1 + self.slippage)
                buy_amount = cash * self.position_size
                shares = int(buy_amount / buy_price)
                
                if shares > 0:
                    cost = shares * buy_price * (1 + self.commission)
                    
                    if cost <= cash:
                        cash -= cost
                        position = 1
                        entry_price = buy_price
                        trade_count += 1
                        
                        trade_log.append({
                            'date': date,
                            'action': 'BUY',
                            'price': buy_price,
                            'shares': shares,
                            'value': cost
                        })
                        
                        if verbose:
                            print(f"\n  BUY  @ {date.date()}")
                            print(f"       Price: ¥{buy_price:.2f} × {shares} shares")
                            print(f"       Cost: ¥{cost:,.0f}")
                            print(f"       Cash remaining: ¥{cash:,.0f}")
            
            # Execute SELL
            elif signal == -1 and position == 1:
                sell_price = price * (1 - self.slippage)
                proceeds = shares * sell_price * (1 - self.commission)
                
                # Calculate P&L
                total_cost = shares * entry_price * (1 + self.commission)
                pnl = proceeds - total_cost
                pnl_pct = pnl / total_cost * 100
                
                cash += proceeds
                
                trade_log.append({
                    'date': date,
                    'action': 'SELL',
                    'price': sell_price,
                    'shares': shares,
                    'value': proceeds,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct
                })
                
                if verbose:
                    print(f"\n  SELL @ {date.date()}")
                    print(f"       Price: ¥{sell_price:.2f} × {shares} shares")
                    print(f"       Proceeds: ¥{proceeds:,.0f}")
                    print(f"       P&L: ¥{pnl:,.0f} ({pnl_pct:+.2f}%)")
                    print(f"       Cash: ¥{cash:,.0f}")
                
                position = 0
                shares = 0
                entry_price = 0.0
            
            # Record portfolio value
            holdings_value = shares * price if position == 1 else 0
            total_value = cash + holdings_value
            
            portfolio_values.append({
                'date': date,
                'cash': cash,
                'holdings': holdings_value,
                'total': total_value,
                'position': position
            })
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"Backtest completed: {trade_count} trades executed")
            print(f"{'='*60}\n")
        
        # Build results DataFrame
        results_df = pd.DataFrame(portfolio_values).set_index('date')
        
        # Calculate returns
        results_df['returns'] = results_df['total'].pct_change()
        results_df['cum_returns'] = (1 + results_df['returns']).cumprod()
        
        # Benchmark returns
        results_df['benchmark'] = df['close']
        results_df['benchmark_returns'] = results_df['benchmark'].pct_change()
        results_df['benchmark_cum'] = (1 + results_df['benchmark_returns']).cumprod()
        
        # Calculate metrics
        metrics = self._calculate_metrics(results_df)
        
        return {
            'data': results_df,
            'metrics': metrics,
            'trades': trade_log,
            'final_value': results_df['total'].iloc[-1],
            'trade_count': trade_count
        }
    
    def _calculate_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate performance metrics"""
        
        # Basic returns
        total_return = (df['total'].iloc[-1] / self.initial_capital - 1) * 100
        
        # Annualized metrics
        n_days = len(df)
        n_years = n_days / 252
        cagr = ((df['total'].iloc[-1] / self.initial_capital) ** (1/n_years) - 1) * 100 if n_years > 0 else 0
        
        # Volatility
        annual_vol = df['returns'].std() * np.sqrt(252) * 100 if len(df) > 1 else 0
        
        # Sharpe Ratio
        if df['returns'].std() > 0:
            sharpe = (df['returns'].mean() / df['returns'].std()) * np.sqrt(252)
        else:
            sharpe = 0
        
        # Sortino Ratio
        downside_returns = df['returns'][df['returns'] < 0]
        if len(downside_returns) > 0:
            downside_std = downside_returns.std() * np.sqrt(252)
            sortino = (df['returns'].mean() * 252 / downside_std) if downside_std > 0 else 0
        else:
            sortino = 0
        
        # Maximum Drawdown
        cumulative = df['total']
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        # Calmar Ratio
        calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Win Rate
        positive_days = (df['returns'] > 0).sum()
        negative_days = (df['returns'] < 0).sum()
        win_rate = (positive_days / (positive_days + negative_days) * 100) if (positive_days + negative_days) > 0 else 0
        
        # Benchmark metrics
        benchmark_return = (df['benchmark_cum'].iloc[-1] - 1) * 100
        benchmark_cagr = ((df['benchmark_cum'].iloc[-1]) ** (1/n_years) - 1) * 100 if n_years > 0 else 0
        
        return {
            'Total Return (%)': round(total_return, 2),
            'CAGR (%)': round(cagr, 2),
            'Annual Volatility (%)': round(annual_vol, 2),
            'Sharpe Ratio': round(sharpe, 2),
            'Sortino Ratio': round(sortino, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Calmar Ratio': round(calmar, 2),
            'Win Rate (%)': round(win_rate, 2),
            'Benchmark Return (%)': round(benchmark_return, 2),
            'Benchmark CAGR (%)': round(benchmark_cagr, 2),
            'Excess Return (%)': round(cagr - benchmark_cagr, 2)
        }
    
    def print_summary(self, results: Dict):
        """Print formatted backtest summary"""
        
        print("\n" + "="*60)
        print("BACKTEST SUMMARY")
        print("="*60)
        
        print(f"\nCapital:")
        print(f"  Initial: ¥{self.initial_capital:,.0f}")
        print(f"  Final:   ¥{results['final_value']:,.0f}")
        print(f"  Profit:  ¥{results['final_value'] - self.initial_capital:,.0f}")
        
        print(f"\nTrading:")
        print(f"  Total Trades: {results['trade_count']}")
        
        if len(results['trades']) > 0:
            buy_trades = [t for t in results['trades'] if t['action'] == 'BUY']
            sell_trades = [t for t in results['trades'] if t['action'] == 'SELL']
            
            if len(sell_trades) > 0:
                winning_trades = [t for t in sell_trades if t['pnl'] > 0]
                print(f"  Winning Trades: {len(winning_trades)} / {len(sell_trades)}")
                
                if len(winning_trades) > 0:
                    avg_win = np.mean([t['pnl'] for t in winning_trades])
                    print(f"  Average Win: ¥{avg_win:,.0f}")
                
                losing_trades = [t for t in sell_trades if t['pnl'] <= 0]
                if len(losing_trades) > 0:
                    avg_loss = np.mean([t['pnl'] for t in losing_trades])
                    print(f"  Average Loss: ¥{avg_loss:,.0f}")
        
        print("\n" + "-"*60)
        print("PERFORMANCE METRICS")
        print("-"*60)
        
        for key, value in results['metrics'].items():
            print(f"{key:.<45} {value}")
        
        print("\n" + "="*60)


# Simple test
if __name__ == "__main__":
    print("VectorizedBacktest class loaded successfully!")
    print("Use in Cell for testing.")
