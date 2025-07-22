import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import numpy as np

from .recall_client import RecallClient
from config.tokens import TOKENS, TRADING_PAIRS
from config.config import config

logger = logging.getLogger(__name__)

class PortfolioManager:
    """Manages portfolio state and position sizing"""
    
    def __init__(self, recall_client: RecallClient):
        self.recall_client = recall_client
        self.positions: Dict[str, float] = {}
        self.balances: Dict[str, float] = {}
        self.portfolio_value: float = 0.0
        self.initial_balance: float = config.INITIAL_BALANCE
        self.last_update: datetime = datetime.now()
        
    async def update_portfolio_state(self) -> bool:
        """Update portfolio state from Recall Network"""
        
        try:
            # Get current portfolio
            portfolio_response = self.recall_client.get_portfolio()
            
            if not portfolio_response.get("success"):
                logger.error("Failed to fetch portfolio data")
                return False
            
            # Update portfolio value
            self.portfolio_value = portfolio_response.get("totalValue", 0.0)
            
            # Update token balances
            self.balances.clear()
            tokens = portfolio_response.get("tokens", [])
            
            for token_info in tokens:
                token_address = token_info.get("token")
                amount = token_info.get("amount", 0.0)
                symbol = token_info.get("symbol")
                
                if token_address:
                    self.balances[token_address] = amount
                    
            self.last_update = datetime.now()
            logger.info(f"Portfolio updated - Total value: ${self.portfolio_value:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating portfolio state: {e}")
            return False
    
    def get_position_size(self, token_address: str) -> float:
        """Get current position size for a token"""
        return self.balances.get(token_address, 0.0)
    
    def get_position_value(self, token_address: str) -> float:
        """Get current position value in USD for a token"""
        
        # Get current portfolio to find token value
        portfolio_response = self.recall_client.get_portfolio()
        
        if portfolio_response.get("success"):
            tokens = portfolio_response.get("tokens", [])
            for token_info in tokens:
                if token_info.get("token") == token_address:
                    return token_info.get("value", 0.0)
        
        return 0.0
    
    def calculate_position_size_for_trade(
        self, 
        action: int, 
        current_position: float,
        token_price: float
    ) -> float:
        """Calculate position size based on action and current state"""
        
        available_balance = self.portfolio_value
        
        if action == 1:  # Buy 10%
            trade_value = available_balance * 0.10
            return trade_value / token_price
            
        elif action == 2:  # Buy 25%  
            trade_value = available_balance * 0.25
            return trade_value / token_price
            
        elif action == 3:  # Sell 10%
            return abs(current_position) * 0.10
            
        elif action == 4:  # Sell 25%
            return abs(current_position) * 0.25
            
        elif action == 5:  # Close all
            return abs(current_position)
            
        return 0.0
    
    def get_available_balance_for_token(self, token_address: str) -> float:
        """Get available balance for a specific token"""
        return self.balances.get(token_address, 0.0)
    
    def get_portfolio_metrics(self) -> Dict[str, float]:
        """Calculate portfolio performance metrics"""
        
        if self.initial_balance == 0:
            return {}
            
        total_return = (self.portfolio_value - self.initial_balance) / self.initial_balance
        
        return {
            "total_value": self.portfolio_value,
            "initial_balance": self.initial_balance,
            "total_return": total_return,
            "profit_loss": self.portfolio_value - self.initial_balance,
            "last_update": self.last_update.isoformat()
        }
