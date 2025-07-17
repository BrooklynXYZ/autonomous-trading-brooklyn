import yaml
from pydantic import BaseModel, ValidationError
from typing import List

class TradingConfig(BaseModel):
    exchange: str
    trading_pairs: List[str]  # Define trading_pairs as a list of strings
    risk_per_trade: float
    stop_loss_atr_multiplier: float
    take_profit_atr_multiplier: float
    model_type: str

def load_config(filepath: str):
    with open(filepath, 'r') as file:
        config_data = yaml.safe_load(file)
    try:
        return TradingConfig(**config_data)
    except ValidationError as e:
        print(f"Error validating config file: {e}")
        raise
