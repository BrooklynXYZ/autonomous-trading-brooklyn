import yaml
from pydantic import BaseModel, ValidationError

class TradingConfig(BaseModel):
    api_key: str
    api_secret: str
    base_currency: str
    quote_currency: str
    risk_per_trade: float

def load_config(path: str) -> TradingConfig:
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    try:
        return TradingConfig(**data)
    except ValidationError as e:
        print("Config validation error:", e)
        raise
