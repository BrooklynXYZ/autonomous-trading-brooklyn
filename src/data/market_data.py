import yfinance as yf

def get_historical_data(symbol, interval='1h', period='7d'):
    # yfinance expects symbols with a dash, e.g., "BTC-USDT" instead of "BTC/USDT"
    yf_symbol = symbol.replace('/', '-')
    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(interval=interval, period=period)
    return df
