import ccxt
from core.logger import get_logger

logger = get_logger(__name__)

class ExchangeClient:
    def __init__(self, api_key, api_secret, exchange_name='binance'):
        self.exchange = getattr(ccxt, exchange_name)({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

    def fetch_balance(self):
        return self.exchange.fetch_balance()

    def fetch_ticker(self, symbol):
        return self.exchange.fetch_ticker(symbol)

    def create_order(self, symbol, side, amount, price=None, order_type='market'):
        try:
            if order_type == 'market':
                return self.exchange.create_market_order(symbol, side, amount)
            else:
                return self.exchange.create_limit_order(symbol, side, amount, price)
        except Exception as e:
            logger.error(f"Order error: {e}")
            raise
