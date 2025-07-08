import ccxt
import pandas as pd
from datetime import datetime, timedelta

def get_historical_data(symbol, interval='1h', period='7d'):
    """
    Fetch historical data using ccxt for crypto markets from Kraken.
    """
    period_days = int(period.replace('d', ''))
    
    # Initialize exchange (using Kraken as a free alternative to Binance)
    exchange = ccxt.kraken({
        'timeout': 30000,
        'enableRateLimit': True,
    })
    
    timeframe_map = {
        '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
        '1h': '1h', '4h': '4h', '1d': '1d', '1w': '1w'
    }
    timeframe = timeframe_map.get(interval, '1h')
    
    ccxt_symbol = symbol.replace('-', '/')
    
    try:
        # Check if the market symbol is available on the exchange
        exchange.load_markets()
        if ccxt_symbol not in exchange.markets:
            print(f"Symbol {ccxt_symbol} not available on Kraken. Please try another symbol or exchange.")
            return pd.DataFrame()

        now = datetime.utcnow()
        start_time = now - timedelta(days=period_days)
        since = exchange.parse8601(start_time.isoformat() + 'Z')
        
        print(f"Fetching {ccxt_symbol} data from Kraken...")
        ohlcv = exchange.fetch_ohlcv(ccxt_symbol, timeframe, since)
        
        if not ohlcv:
            print(f"No data returned for {ccxt_symbol} from Kraken.")
            return pd.DataFrame()
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = pd.to_numeric(df[col])
        
        print(f"Successfully fetched {len(df)} rows of data.")
        return df
        
    except Exception as e:
        print(f"An error occurred while fetching data from Kraken: {e}")
        return pd.DataFrame()

def get_current_price(symbol):
    """
    Get current price for a symbol from Kraken.
    """
    exchange = ccxt.kraken({'enableRateLimit': True})
    
    try:
        ccxt_symbol = symbol.replace('-', '/')
        ticker = exchange.fetch_ticker(ccxt_symbol)
        return ticker['last']
    except Exception as e:
        print(f"Error fetching current price from Kraken: {e}")
        return None

def get_market_info(symbol):
    """
    Get market information for a symbol from Kraken.
    """
    exchange = ccxt.kraken({'enableRateLimit': True})
    
    try:
        ccxt_symbol = symbol.replace('-', '/')
        ticker = exchange.fetch_ticker(ccxt_symbol)
        
        return {
            'symbol': symbol,
            'price': ticker['last'],
            'volume': ticker['baseVolume'],
            'change_24h': ticker.get('percentage'), # .get() for safety
            'high_24h': ticker['high'],
            'low_24h': ticker['low']
        }
    except Exception as e:
        print(f"Error fetching market info from Kraken: {e}")
        return None