import numpy as np
from src.ai.ensemble_model import EnsembleTradingModel
from src.ai.rule_based_trader import RuleBasedTrader
from src.ai.multi_timeframe_analyzer import MultiTimeframeAnalyzer

class SignalGenerator:
    def __init__(self, model=None, symbol="BTC-USDT"):
        self.model = model or EnsembleTradingModel()
        self.rule_trader = RuleBasedTrader()
        self.mtf_analyzer = MultiTimeframeAnalyzer(symbol)
        self.hybrid_mode = True
    
    def generate_signal(self, features, df=None):
        """Generate trading signal using hybrid approach"""
        if not self.hybrid_mode:
            return self._generate_ml_signal(features)
        
        # Get signals from different approaches
        ml_signal = self._generate_ml_signal(features)
        rule_signal = self.rule_trader.get_combined_signal(df) if df is not None else 'hold'
        
        # For backtesting, we'll skip MTF analysis to avoid API limits
        # mtf_signal = self.mtf_analyzer.get_signals_all_timeframes()
        mtf_signal = 'hold'
        
        # Combine signals with weights
        signal_weights = {
            'ml': 0.5,
            'rules': 0.5,
            'mtf': 0.0  # Disabled for backtesting
        }
        
        signals = {'ml': ml_signal, 'rules': rule_signal, 'mtf': mtf_signal}
        
        # Voting mechanism
        buy_votes = sum(signal_weights[k] for k, v in signals.items() if v == 'buy')
        sell_votes = sum(signal_weights[k] for k, v in signals.items() if v == 'sell')
        
        if buy_votes > sell_votes and buy_votes > 0.3:
            return 'buy'
        elif sell_votes > buy_votes and sell_votes > 0.3:
            return 'sell'
        else:
            return 'hold'
    
    def _generate_ml_signal(self, features):
        """Generate ML-based signal"""
        try:
            if hasattr(self.model, 'predict_proba') and self.model.is_trained:
                probabilities = self.model.predict_proba(features)
                confidence = np.max(probabilities, axis=1)[0]
                prediction = np.argmax(probabilities, axis=1)[0]
                
                if confidence > 0.6:
                    return 'buy' if prediction == 1 else 'sell'
                else:
                    return 'hold'
            elif hasattr(self.model, 'predict') and self.model.is_trained:
                prediction = self.model.predict(features)[0]
                return 'buy' if prediction == 1 else 'sell'
            else:
                return 'hold'
        except Exception as e:
            print(f"Error in ML signal generation: {e}")
            return 'hold'