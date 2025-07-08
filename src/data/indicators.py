import pandas as pd
import numpy as np

def compute_sma(df, window=20):
    """Compute Simple Moving Average"""
    return df['Close'].rolling(window=window).mean()

def compute_rsi(df, window=14):
    """Compute Relative Strength Index"""
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(df, fast_period=12, slow_period=26, signal_period=9):
    """Compute MACD indicator"""
    ema_fast = df['Close'].ewm(span=fast_period).mean()
    ema_slow = df['Close'].ewm(span=slow_period).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal_period).mean()
    macd_histogram = macd - macd_signal
    return macd

def compute_bollinger_bands(df, period=20, std_dev=2):
    """Compute Bollinger Bands"""
    sma = df['Close'].rolling(window=period).mean()
    std = df['Close'].rolling(window=period).std()
    bb_upper = sma + (std * std_dev)
    bb_lower = sma - (std * std_dev)
    return pd.DataFrame({
        'bb_upper': bb_upper, 
        'bb_middle': sma, 
        'bb_lower': bb_lower
    }, index=df.index)

def compute_stochastic(df, k_period=14, d_period=3):
    """Compute Stochastic Oscillator"""
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()
    stoch_k = 100 * (df['Close'] - low_min) / (high_max - low_min)
    stoch_d = stoch_k.rolling(window=d_period).mean()
    return pd.DataFrame({'stoch_k': stoch_k, 'stoch_d': stoch_d}, index=df.index)

def compute_volume_indicators(df):
    """Compute volume-based indicators"""
    # Volume Moving Average
    volume_ma = df['Volume'].rolling(window=20).mean()
    # Volume Rate of Change
    volume_roc = df['Volume'].pct_change(periods=10)
    # Simple On-Balance Volume
    obv = (df['Volume'] * (df['Close'].diff().apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0))).cumsum()
    
    return pd.DataFrame({
        'volume_ma': volume_ma, 
        'volume_roc': volume_roc, 
        'obv': obv
    }, index=df.index)

def compute_atr(df, period=14):
    """Compute Average True Range"""
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = true_range.rolling(window=period).mean()
    return atr