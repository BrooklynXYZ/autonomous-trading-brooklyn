class RiskAnalyzer:
    def __init__(self, risk_per_trade=0.01):
        self.risk_per_trade = risk_per_trade

    def calculate_position_size(self, balance, stop_loss_pct):
        return balance * self.risk_per_trade / stop_loss_pct
