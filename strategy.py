import pandas as pd
import talib as ta
import yfinance as yf

def download_data(ticker: str = '000300.SS', start: str = '2016-01-01', end: str = '2026-01-01') -> pd.DataFrame:
    print(f"Downloading {ticker}...")
    data = yf.download(ticker, start=start, end=end, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data.columns = [col.lower() for col in data.columns]
    print(f"✓ {len(data)} rows")
    return data

class BollingerMACDStrategy:
    def __init__(self, bb_window=20, bb_std=2.0, macd_fast=12, macd_slow=26, macd_signal=9, volume_window=20, volume_threshold=1.0):
        self.bb_window = bb_window
        self.bb_std = bb_std
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.volume_window = volume_window
        self.volume_threshold = volume_threshold
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = ta.BBANDS(df['close'], timeperiod=self.bb_window, nbdevup=self.bb_std, nbdevdn=self.bb_std, matype=0)
        df['macd'], df['macd_signal'], _ = ta.MACD(df['close'], fastperiod=self.macd_fast, slowperiod=self.macd_slow, signalperiod=self.macd_signal)
        df['volume_ma'] = ta.SMA(df['volume'], timeperiod=self.volume_window)
        return df
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_indicators(data)
        df['signal'] = 0
        df['position_state'] = 0
        position = 0
        
        for i in range(1, len(df)):
            if position == 0:
                entry_condition = ((df['close'].iloc[i] > df['bb_upper'].iloc[i]) &
                                   (df['macd'].iloc[i] > df['macd_signal'].iloc[i]) &
                                   (df['volume'].iloc[i] > df['volume_ma'].iloc[i] * self.volume_threshold))
                if entry_condition:
                    df.loc[df.index[i], 'signal'] = 1
                    position = 1
            elif position == 1:
                exit_condition = ((df['close'].iloc[i] < df['bb_middle'].iloc[i]) |
                                  (df['macd'].iloc[i] < df['macd_signal'].iloc[i]))
                if exit_condition:
                    df.loc[df.index[i], 'signal'] = -1
                    position = 0
            df.loc[df.index[i], 'position_state'] = position
        return df
