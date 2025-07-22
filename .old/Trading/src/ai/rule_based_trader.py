import pandas as pd
import numpy as np

class RuleBasedTrader:
    def __init__(self):
        self.rules = []
        self.setup_rules()
    
    def setup_rules(self):
        """Define trading rules"""
        self.rules = [
            self.golden_cross_rule,
            self.rsi_divergence_rule,
            self.bollinger_squeeze_rule,
            self.volume_breakout_rule,
            self.macd_crossover_rule
        ]
    
    def golden_cross_rule(self, df):
        """Golden Cross: SMA50 crosses above SMA200"""
        if len(df) < 200:
            return {'signal': 'hold', 'confidence': 0}
        
        try:
            sma_50 = df['Close'].rolling(50).mean()
            sma_200 = df['Close'].rolling(200).mean()
            
            current_cross = sma_50.iloc[-1] > sma_200.iloc[-1]
            prev_cross = sma_50.iloc[-2] > sma_200.iloc[-2]
            
            if current_cross and not prev_cross:
                return {'signal': 'buy', 'confidence': 0.8}
            elif not current_cross and prev_cross:
                return {'signal': 'sell', 'confidence': 0.8}
        except:
            pass
        
        return {'signal': 'hold', 'confidence': 0.5}
    
    def rsi_divergence_rule(self, df):
        """RSI Divergence Rule"""
        if len(df) < 14 or 'rsi' not in df.columns:
            return {'signal': 'hold', 'confidence': 0}
        
        try:
            rsi = df['rsi'].iloc[-1]
            
            if rsi < 30:
                return {'signal': 'buy', 'confidence': 0.7}
            elif rsi > 70:
                return {'signal': 'sell', 'confidence': 0.7}
        except:
            pass
        
        return {'signal': 'hold', 'confidence': 0.3}
    
    def bollinger_squeeze_rule(self, df):
        """Bollinger Band Squeeze"""
        if len(df) < 20:
            return {'signal': 'hold', 'confidence': 0}
        
        try:
            # Calculate Bollinger Bands
            sma_20 = df['Close'].rolling(20).mean()
            std_20 = df['Close'].rolling(20).std()
            bb_upper = sma_20 + (std_20 * 2)
            bb_lower = sma_20 - (std_20 * 2)
            
            current_price = df['Close'].iloc[-1]
            
            if current_price > bb_upper.iloc[-1]:
                return {'signal': 'sell', 'confidence': 0.6}
            elif current_price < bb_lower.iloc[-1]:
                return {'signal': 'buy', 'confidence': 0.6}
        except:
            pass
        
        return {'signal': 'hold', 'confidence': 0.4}
    
    def volume_breakout_rule(self, df):
        """Volume Breakout Rule"""
        if len(df) < 20:
            return {'signal': 'hold', 'confidence': 0}
        
        try:
            volume_ma = df['Volume'].rolling(20).mean()
            current_volume = df['Volume'].iloc[-1]
            price_change = df['Close'].pct_change().iloc[-1]
            
            if current_volume > volume_ma.iloc[-1] * 1.5:
                if price_change > 0.02:
                    return {'signal': 'buy', 'confidence': 0.7}
                elif price_change < -0.02:
                    return {'signal': 'sell', 'confidence': 0.7}
        except:
            pass
        
        return {'signal': 'hold', 'confidence': 0.3}
    
    def macd_crossover_rule(self, df):
        """MACD Crossover Rule"""
        if len(df) < 26 or 'macd' not in df.columns:
            return {'signal': 'hold', 'confidence': 0}
        
        try:
            macd = df['macd'].iloc[-1]
            macd_prev = df['macd'].iloc[-2]
            
            if macd > 0 and macd_prev <= 0:
                return {'signal': 'buy', 'confidence': 0.6}
            elif macd < 0 and macd_prev >= 0:
                return {'signal': 'sell', 'confidence': 0.6}
        except:
            pass
        
        return {'signal': 'hold', 'confidence': 0.4}
    
    def get_combined_signal(self, df):
        """Combine all rule signals"""
        signals = []
        
        for rule in self.rules:
            try:
                result = rule(df)
                signals.append(result)
            except Exception as e:
                print(f"Error in rule {rule.__name__}: {e}")
                continue
        
        if not signals:
            return 'hold'
        
        # Weighted voting
        buy_weight = sum(s['confidence'] for s in signals if s['signal'] == 'buy')
        sell_weight = sum(s['confidence'] for s in signals if s['signal'] == 'sell')
        hold_weight = sum(s['confidence'] for s in signals if s['signal'] == 'hold')
        
        if buy_weight > sell_weight and buy_weight > hold_weight:
            return 'buy'
        elif sell_weight > buy_weight and sell_weight > hold_weight:
            return 'sell'
        else:
            return 'hold'