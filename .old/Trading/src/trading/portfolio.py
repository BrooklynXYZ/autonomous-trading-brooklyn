class Portfolio:
    def __init__(self, exchange_client):
        self.exchange_client = exchange_client

    def get_balance(self, currency):
        balance = self.exchange_client.fetch_balance()
        return balance.get('total', {}).get(currency, 0)
