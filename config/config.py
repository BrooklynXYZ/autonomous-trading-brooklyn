import os
from typing import Dict, Any
from pydantic import BaseSettings

class Config(BaseSettings):
    # Recall Network API Configuration
    RECALL_API_BASE_URL: str = "https://api.sandbox.competitions.recall.network"
    RECALL_API_TOKEN: str = os.getenv("RECALL_API_TOKEN", "")
    
    # Trading Configuration
    INITIAL_BALANCE: float = 10000.0
    MAX_PORTFOLIO_RISK: float = 0.15
    MAX_POSITION_SIZE: float = 0.30
    MAX_DAILY_TRADES: int = 50
    EMERGENCY_STOP_THRESHOLD: float = 0.25
    
    # Model Configuration
    MODEL_PATH: str = "data/models/best_model.pth"
    TRAINING_DATA_DAYS: int = 180
    VALIDATION_DATA_DAYS: int = 90
    
    # Risk Management
    STOP_LOSS_PERCENTAGE: float = 0.02  # 2%
    TAKE_PROFIT_PERCENTAGE: float = 0.035  # 3.5%
    TRAILING_STOP_PERCENTAGE: float = 0.008  # 0.8%
    MAX_HOLD_TIME_MINUTES: int = 20
    
    # RL Training Parameters
    LEARNING_RATE: float = 3e-4
    GAMMA: float = 0.99
    EPS_CLIP: float = 0.2
    K_EPOCHS: int = 4
    BATCH_SIZE: int = 64
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/trading.log"
    
    # Data Sources
    BINANCE_API_URL: str = "https://api.binance.com/api/v3"
    UPDATE_FREQUENCY: int = 60  # seconds
    
    class Config:
        env_file = ".env"

# Global config instance
config = Config() 