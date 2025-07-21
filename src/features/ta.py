# =============================================================================
# TECHNICAL ANALYSIS MODULE
# =============================================================================

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import pandas_ta as ta
from loguru import logger

class TechnicalAnalysis:
    """
    Technical analysis indicators for cryptocurrency trading
    Optimized for short-term (15m-1h) trading strategies
    """

    def __init__(self):
        logger.info("Technical analysis module initialized")

    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators for the given OHLCV data
        Returns DataFrame with all indicators added as columns
        """
        if len(df) < 50:
            logger.warning(f"Insufficient data for indicators: {len(df)} rows")
            return df

        logger.info("Calculating technical indicators")

        # Make a copy to avoid modifying original
        data = df.copy()

        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_cols):
            logger.error(f"Missing required columns. Have: {data.columns.tolist()}")
            return df

        try:
            # Moving Averages
            data = self._add_moving_averages(data)

            # Momentum Indicators
            data = self._add_momentum_indicators(data)

            # Volatility Indicators
            data = self._add_volatility_indicators(data)

            # Volume Indicators
            data = self._add_volume_indicators(data)

            # Support/Resistance
            data = self._add_support_resistance(data)

            # Price Action
            data = self._add_price_action_features(data)

            # Fill any NaN values with forward fill then backward fill
            data = data.fillna(method='ffill').fillna(method='bfill')

            logger.success(f"Calculated {len(data.columns) - len(df.columns)} new indicators")
            return data

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return df

    def _add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add various moving averages"""
        # Simple Moving Averages
        for period in [7, 14, 21, 50]:
            df[f'sma_{period}'] = ta.sma(df['close'], length=period)

        # Exponential Moving Averages
        for period in [7, 14, 21, 50]:
            df[f'ema_{period}'] = ta.ema(df['close'], length=period)

        # Hull Moving Average (responsive)
        df['hma_21'] = ta.hma(df['close'], length=21)

        # Volume Weighted Average Price
        df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])

        # Moving Average Convergence/Divergence
        macd_data = ta.macd(df['close'], fast=12, slow=26, signal=9)
        df['macd'] = macd_data['MACD_12_26_9']
        df['macd_signal'] = macd_data['MACDs_12_26_9']
        df['macd_histogram'] = macd_data['MACDh_12_26_9']

        return df

    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum-based indicators"""
        # Relative Strength Index
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['rsi_fast'] = ta.rsi(df['close'], length=7)  # More sensitive

        # Stochastic Oscillator
        stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3)
        df['stoch_k'] = stoch['STOCHk_14_3_3']
        df['stoch_d'] = stoch['STOCHd_14_3_3']

        # Williams %R
        df['williams_r'] = ta.willr(df['high'], df['low'], df['close'], length=14)

        # Commodity Channel Index
        df['cci'] = ta.cci(df['high'], df['low'], df['close'], length=20)

        # Rate of Change
        df['roc'] = ta.roc(df['close'], length=10)

        # Money Flow Index
        df['mfi'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=14)

        return df

    def _add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility-based indicators"""
        # Bollinger Bands
        bb = ta.bbands(df['close'], length=20, std=2)
        df['bb_upper'] = bb['BBU_20_2.0']
        df['bb_middle'] = bb['BBM_20_2.0']
        df['bb_lower'] = bb['BBL_20_2.0']
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # Average True Range
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        df['atr_percent'] = df['atr'] / df['close'] * 100

        # Keltner Channels
        kc = ta.kc(df['high'], df['low'], df['close'], length=20, scalar=2)
        df['kc_upper'] = kc['KCUe_20_2']
        df['kc_middle'] = kc['KCBe_20_2']
        df['kc_lower'] = kc['KCLe_20_2']

        # Donchian Channels
        dc = ta.donchian(df['high'], df['low'], lower_length=20, upper_length=20)
        df['dc_upper'] = dc['DCU_20_20']
        df['dc_lower'] = dc['DCL_20_20']
        df['dc_middle'] = dc['DCM_20_20']

        return df

    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based indicators"""
        # On-Balance Volume
        df['obv'] = ta.obv(df['close'], df['volume'])

        # Volume Moving Averages
        df['volume_sma_20'] = ta.sma(df['volume'], length=20)
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']

        # Accumulation/Distribution Line
        df['ad'] = ta.ad(df['high'], df['low'], df['close'], df['volume'])

        # Chaikin Money Flow
        df['cmf'] = ta.cmf(df['high'], df['low'], df['close'], df['volume'], length=20)

        # Volume Weighted Average Price deviation
        if 'vwap' in df.columns:
            df['vwap_deviation'] = (df['close'] - df['vwap']) / df['vwap'] * 100

        return df

    def _add_support_resistance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add support and resistance levels"""
        # Pivot points
        df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
        df['r1'] = 2 * df['pivot'] - df['low']
        df['s1'] = 2 * df['pivot'] - df['high']
        df['r2'] = df['pivot'] + (df['high'] - df['low'])
        df['s2'] = df['pivot'] - (df['high'] - df['low'])

        # Recent highs and lows
        df['high_20'] = df['high'].rolling(window=20).max()
        df['low_20'] = df['low'].rolling(window=20).min()

        return df

    def _add_price_action_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price action features"""
        # Candlestick patterns
        df['body_size'] = abs(df['close'] - df['open'])
        df['upper_shadow'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_shadow'] = df[['close', 'open']].min(axis=1) - df['low']
        df['total_range'] = df['high'] - df['low']

        # Relative sizes
        df['body_to_range'] = df['body_size'] / df['total_range']
        df['upper_shadow_to_range'] = df['upper_shadow'] / df['total_range']
        df['lower_shadow_to_range'] = df['lower_shadow'] / df['total_range']

        # Price changes
        df['price_change'] = df['close'].pct_change()
        df['price_change_abs'] = df['price_change'].abs()

        # Gap analysis
        df['gap'] = df['open'] - df['close'].shift(1)
        df['gap_percent'] = df['gap'] / df['close'].shift(1) * 100

        return df

    def get_signal_strength(self, df: pd.DataFrame, lookback: int = 10) -> Dict[str, float]:
        """
        Calculate overall signal strength from multiple indicators
        Returns scores from -1 (strong bearish) to +1 (strong bullish)
        """
        if len(df) < lookback:
            return {'overall': 0.0, 'trend': 0.0, 'momentum': 0.0, 'volume': 0.0}

        latest = df.tail(lookback)
        current = df.iloc[-1]

        signals = {}

        # Trend signals
        trend_signals = []
        if 'ema_7' in current and 'ema_21' in current:
            trend_signals.append(1 if current['ema_7'] > current['ema_21'] else -1)
        if 'sma_14' in current and 'sma_50' in current:
            trend_signals.append(1 if current['sma_14'] > current['sma_50'] else -1)
        if 'macd' in current and 'macd_signal' in current:
            trend_signals.append(1 if current['macd'] > current['macd_signal'] else -1)

        signals['trend'] = np.mean(trend_signals) if trend_signals else 0.0

        # Momentum signals
        momentum_signals = []
        if 'rsi' in current:
            if current['rsi'] > 70:
                momentum_signals.append(-0.5)  # Overbought
            elif current['rsi'] < 30:
                momentum_signals.append(0.5)   # Oversold
            else:
                momentum_signals.append((50 - current['rsi']) / 50)  # Normalized

        if 'stoch_k' in current:
            if current['stoch_k'] > 80:
                momentum_signals.append(-0.5)
            elif current['stoch_k'] < 20:
                momentum_signals.append(0.5)

        if 'cci' in current:
            momentum_signals.append(np.tanh(current['cci'] / 200))  # Normalize CCI

        signals['momentum'] = np.mean(momentum_signals) if momentum_signals else 0.0

        # Volume signals
        volume_signals = []
        if 'volume_ratio' in current:
            # High volume = stronger signal
            volume_strength = min(current['volume_ratio'], 3.0) / 3.0  # Cap at 3x normal
            volume_signals.append(volume_strength)

        if 'obv' in df and len(df) > 5:
            # OBV trend
            obv_trend = np.polyfit(range(5), df['obv'].tail(5), 1)[0]
            volume_signals.append(np.tanh(obv_trend / 1000000))  # Normalize

        signals['volume'] = np.mean(volume_signals) if volume_signals else 0.0

        # Overall signal (weighted combination)
        signals['overall'] = (
            0.4 * signals['trend'] +
            0.4 * signals['momentum'] +
            0.2 * signals['volume']
        )

        return signals

    def detect_patterns(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        Detect common trading patterns
        """
        if len(df) < 20:
            return {}

        current = df.iloc[-1]
        recent = df.tail(5)

        patterns = {}

        # Bollinger Band squeeze
        if 'bb_width' in df:
            bb_width_20 = df['bb_width'].tail(20).mean()
            patterns['bb_squeeze'] = current['bb_width'] < bb_width_20 * 0.7

        # RSI divergence (simplified)
        if 'rsi' in df and len(df) > 10:
            price_trend = df['close'].tail(10).iloc[-1] > df['close'].tail(10).iloc[0]
            rsi_trend = df['rsi'].tail(10).iloc[-1] > df['rsi'].tail(10).iloc[0]
            patterns['rsi_divergence'] = price_trend != rsi_trend

        # Volume spike
        if 'volume_ratio' in current:
            patterns['volume_spike'] = current['volume_ratio'] > 2.0

        # Price breakout
        if 'high_20' in current and 'low_20' in current:
            patterns['breakout_up'] = current['close'] > current['high_20'] * 0.99
            patterns['breakdown'] = current['close'] < current['low_20'] * 1.01

        return patterns

# Global technical analysis instance
technical_analyzer = TechnicalAnalysis()
