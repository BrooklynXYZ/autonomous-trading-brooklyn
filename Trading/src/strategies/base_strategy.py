class BaseStrategy:
    def __init__(self, signal_generator, risk_analyzer, order_manager, portfolio):
        self.signal_generator = signal_generator
        self.risk_analyzer = risk_analyzer
        self.order_manager = order_manager
        self.portfolio = portfolio

    def run(self, features, symbol, stop_loss_pct):
        signal = self.signal_generator.generate_signal(features)
        balance = self.portfolio.get_balance('USDT')
        position_size = self.risk_analyzer.calculate_position_size(balance, stop_loss_pct)
        if signal in ['buy', 'sell']:
            self.order_manager.place_order(symbol, signal, position_size)
