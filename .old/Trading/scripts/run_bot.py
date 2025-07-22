from core.config import load_config
from trading.exchange_client import ExchangeClient
from trading.order_manager import OrderManager
from trading.portfolio import Portfolio
from ai.signal_generator import SignalGenerator
from ai.risk_analyzer import RiskAnalyzer
from ai.model import TradingModel
from strategies.base_strategy import BaseStrategy
from data.market_data import get_historical_data
from data.indicators import compute_sma, compute_rsi
from data.sentiment import SentimentAnalyzer

def main():
    config = load_config('config/main.yaml')
    exchange_client = ExchangeClient(config.api_key, config.api_secret)
    order_manager = OrderManager(exchange_client)
    portfolio = Portfolio(exchange_client)
    model = TradingModel()
    signal_generator = SignalGenerator(model)
    risk_analyzer = RiskAnalyzer(config.risk_per_trade)
    strategy = BaseStrategy(signal_generator, risk_analyzer, order_manager, portfolio)
    
    # Example: fetch data and run strategy
    df = get_historical_data(f"{config.base_currency}{config.quote_currency}")
    df['sma'] = compute_sma(df)
    df['rsi'] = compute_rsi(df)
    sentiment_analyzer = SentimentAnalyzer()
    sentiment, score = sentiment_analyzer.analyze("Bitcoin is bullish today!")
    features = [df['sma'].iloc[-1], df['rsi'].iloc[-1], score]
    strategy.run(features, f"{config.base_currency}/{config.quote_currency}", stop_loss_pct=0.02)

if __name__ == "__main__":
    main()
