# filepath: src/ai/multi_timeframe_analyzer.py
import pandas as pd
from src.data.market_data import get_historical_data
from src.data.indicators import compute_sma, compute_rsi, compute_macd

class MultiTimeframeAnalyzer:
    def __init__(self, symbol):
        self.symbol = symbol
        self.timeframes = ['1h', '4h', '1d']
    
    def get_signals_all_timeframes(self):
        """Get trading signals from multiple timeframes"""
        signals = {}
        
        for tf in self.timeframes:
            try:
                df = get_historical_data(self.symbol, interval=tf, period='30d')
                if df.empty:
                    continue
                
                # Compute indicators for each timeframe
                df['sma_20'] = compute_sma(df, window=20)
                df['sma_50'] = compute_sma(df, window=50)
                df['rsi'] = compute_rsi(df)
                df['macd'] = compute_macd(df)
                
                # Generate timeframe-specific signals
                signal = self._generate_timeframe_signal(df)
                signals[tf] = signal
            except Exception as e:
                print(f"Error processing {tf}: {e}")
                continue
                
        return self._combine_signals(signals)
    
    def _generate_timeframe_signal(self, df):
        """Generate signal for a specific timeframe"""
        latest = df.iloc[-1]
        
        # Trend following signals
        trend_signal = 1 if latest['sma_20'] > latest['sma_50'] else -1
        
        # Momentum signals
        momentum_signal = 1 if latest['rsi'] < 30 else (-1 if latest['rsi'] > 70 else 0)
        
        # MACD signals
        macd_signal = 1 if latest['macd'] > 0 else -1
        
        return {
            'trend': trend_signal,
            'momentum': momentum_signal,
            'macd': macd_signal,
            'strength': abs(trend_signal) + abs(momentum_signal) + abs(macd_signal)
        }
    
    def _combine_signals(self, signals):
        """Combine signals from all timeframes"""
        if not signals:
            return 'hold'
            
        weights = {'1h': 0.3, '4h': 0.4, '1d': 0.3}
        
        combined_score = 0
        for tf, weight in weights.items():
            if tf in signals:
                tf_score = (signals[tf]['trend'] + signals[tf]['momentum'] + signals[tf]['macd']) / 3
                combined_score += tf_score * weight
            
        return 'buy' if combined_score > 0.2 else ('sell' if combined_score < -0.2 else 'hold')