import yfinance as yf

def get_historical_data(symbol, interval='1h', period='7d'):
    ticker = yf.Ticker(symbol)
    df = ticker.history(interval=interval, period=period)
    return df
