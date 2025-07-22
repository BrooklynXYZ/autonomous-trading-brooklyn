import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime
import requests

from config.config import config

logger = logging.getLogger(__name__)

class MarketDataProvider:
    """Provides market data from external sources"""
    
    def __init__(self):
        self.binance_base_url = config.BINANCE_API_URL
        self.current_prices: Dict[str, float] = {}
        self.last_update: datetime = datetime.now()
        
    async def update_market_data(self) -> bool:
        """Update market data from Binance API"""
        
        try:
            # Get current prices for our tokens
            symbols = ["ETHUSDT", "SOLUSDT"]  # Map to our trading pairs
            
            prices = {}
            for symbol in symbols:
                price = await self._get_binance_price(symbol)
                if price:
                    # Map to our token symbols
                    if symbol == "ETHUSDT":
                        prices["WETH"] = price
                    elif symbol == "SOLUSDT": 
                        prices["SOL"] = price
            
            self.current_prices.update(prices)
            self.last_update = datetime.now()
            
            logger.info(f"Market data updated: {prices}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update market data: {e}")
            return False
    
    async def _get_binance_price(self, symbol: str) -> Optional[float]:
        """Get current price from Binance"""
        
        try:
            response = requests.get(
                f"{self.binance_base_url}/ticker/price",
                params={"symbol": symbol},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return float(data["price"])
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        return self.current_prices.get(symbol, 0.0)
    
    def get_last_update(self) -> datetime:
        """Get timestamp of last market data update"""
        return self.last_update
