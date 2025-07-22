import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import os

def collect_binance_data(symbol, days=180):
    """Collect historical 1-minute data from Binance"""
    
    base_url = "https://api.binance.com/api/v3/klines"
    
    # Calculate date range (6 months ago for training)
    end_date = datetime(2025, 7, 22)  # Today
    start_date = end_date - timedelta(days=days)
    
    start_ms = int(start_date.timestamp() * 1000)
    end_ms = int(end_date.timestamp() * 1000)
    
    all_data = []
    current_start = start_ms
    
    print(f"Collecting {symbol} data from {start_date} to {end_date}")
    
    while current_start < end_ms:
        params = {
            'symbol': symbol,
            'interval': '1m',
            'startTime': current_start,
            'endTime': min(current_start + (1000 * 60000), end_ms),
            'limit': 1000
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            batch_data = response.json()
            all_data.extend(batch_data)
            
            print(f"Downloaded {len(batch_data)} candles, total: {len(all_data)}")
            
            current_start += (1000 * 60000)
            time.sleep(0.1)  # Rate limit compliance
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)
            continue
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 
        'volume', 'close_time', 'quote_asset_volume',
        'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore'
    ])
    
    # Convert to proper types
    numeric_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col])
    
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    # Save to file
    filename = f"data/raw/{symbol.lower()}_1m_data.csv"
    df.to_csv(filename)
    print(f"Saved {len(df)} records to {filename}")
    
    return df

if __name__ == "__main__":
    # Collect data for our trading pairs
    symbols = ['ETHUSDT', 'SOLUSDT']
    
    for symbol in symbols:
        print(f"\n=== Collecting {symbol} ===")
        collect_binance_data(symbol, days=180)
        
    print("\n✅ Data collection completed!")
