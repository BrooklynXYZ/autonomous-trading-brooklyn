# =============================================================================
# MAIN CONFIGURATION FILE
# =============================================================================

import os
from typing import Dict, List
from dataclasses import dataclass
import yaml

@dataclass
class TradingConfig:
    # Trading pairs
    symbols: List[str]

    # Timeframes for analysis
    timeframes: List[str]

    # Risk management
    max_position_size: float
    stop_loss: float
    take_profit: float
    daily_loss_limit: float

    # Model configuration
    state_size: int
    action_size: int
    hidden_dims: List[int]
    learning_rate: float
    batch_size: int
    memory_size: int

    # Backtesting
    initial_capital: float
    commission: float
    start_date: str
    end_date: str

class Config:
    def __init__(self):
        # Load environment variables
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.coingecko_key = os.getenv('COINGECKO_API_KEY')
        self.coinapi_key = os.getenv('COINAPI_KEY')
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.whale_alert_key = os.getenv('WHALE_ALERT_API_KEY')
        self.recall_api_key = os.getenv('RECALL_API_KEY')
        self.recall_api_url = os.getenv('RECALL_API_URL')

        # Trading configuration
        self.trading = TradingConfig(
            symbols=['BTC/USDT', 'ETH/USDT'],
            timeframes=['15m', '1h'],  # Short-term focus
            max_position_size=0.1,
            stop_loss=0.02,  # 2% stop loss for short-term
            take_profit=0.06,  # 6% take profit for short-term
            daily_loss_limit=0.15,

            # M-DQN architecture
            state_size=60,  # 50 price features + 10 sentiment/whale features
            action_size=3,  # Buy, Sell, Hold
            hidden_dims=[256, 128, 64],
            learning_rate=0.001,
            batch_size=32,
            memory_size=10000,

            # Backtesting
            initial_capital=10000,
            commission=0.001,
            start_date='2023-01-01',
            end_date='2024-12-31'
        )

        # API endpoints
        self.endpoints = {
            'alpha_vantage': 'https://www.alphavantage.co/query',
            'coingecko': 'https://api.coingecko.com/api/v3',
            'coinapi': 'https://rest.coinapi.io/v1',
            'whale_alert': 'https://api.whale-alert.io/v1',
            'twitter': 'https://api.twitter.com/2'
        }

    def validate_keys(self) -> Dict[str, bool]:
        """Validate that required API keys are present"""
        return {
            'alpha_vantage': bool(self.alpha_vantage_key),
            'twitter': bool(self.twitter_bearer_token),
            'whale_alert': bool(self.whale_alert_key),
            'recall': bool(self.recall_api_key)
        }

# Global config instance
config = Config()
