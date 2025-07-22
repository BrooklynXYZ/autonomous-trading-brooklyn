import pandas as pd
import numpy as np
import ta
import os

def calculate_technical_indicators(df):
    """Calculate technical indicators for training"""
    
    print("Calculating technical indicators...")
    
    # Price-based indicators
    df['rsi_14'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['rsi_21'] = ta.momentum.RSIIndicator(df['close'], window=21).rsi()
    
    # Moving averages
    df['sma_7'] = ta.trend.SMAIndicator(df['close'], window=7).sma_indicator()
    df['sma_21'] = ta.trend.SMAIndicator(df['close'], window=21).sma_indicator()
    df['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
    df['ema_26'] = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
    
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_middle'] = bb.bollinger_mavg()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
    
    # MACD
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_histogram'] = macd.macd_diff()
    
    # Volume indicators
    df['volume_sma'] = ta.volume.VolumeSMAIndicator(df['close'], df['volume'], window=10).volume_sma()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # Momentum indicators
    df['momentum_5'] = df['close'].pct_change(5)
    df['momentum_15'] = df['close'].pct_change(15)
    df['momentum_30'] = df['close'].pct_change(30)
    
    # Volatility
    df['volatility'] = df['close'].rolling(window=20).std()
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    
    # Price position indicators
    df['price_position'] = (df['close'] - df['low'].rolling(20).min()) / (df['high'].rolling(20).max() - df['low'].rolling(20).min())
    
    return df

def prepare_training_data():
    """Prepare data for RL training"""
    
    symbols = ['ethusdt', 'solusdt']
    processed_data = {}
    
    for symbol in symbols:
        print(f"\n=== Processing {symbol.upper()} ===")
        
        # Load raw data
        filename = f"data/raw/{symbol}_1m_data.csv"
        if not os.path.exists(filename):
            print(f"Raw data file not found: {filename}")
            continue
            
        df = pd.read_csv(filename, index_col='timestamp', parse_dates=True)
        
        # Calculate features
        df = calculate_technical_indicators(df)
        
        # Remove NaN values
        df = df.dropna()
        
        print(f"Processed {len(df)} records with features")
        
        # Save processed data
        output_filename = f"data/processed/{symbol}_features.csv"
        df.to_csv(output_filename)
        print(f"Saved to {output_filename}")
        
        processed_data[symbol] = df
    
    return processed_data

if __name__ == "__main__":
    prepare_training_data()
    print("\n✅ Feature engineering completed!")
