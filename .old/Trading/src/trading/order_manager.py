class OrderManager:
    def __init__(self, exchange_client):
        self.exchange_client = exchange_client

    def place_order(self, symbol, side, amount, price=None, order_type='market'):
        return self.exchange_client.create_order(symbol, side, amount, price, order_type)
