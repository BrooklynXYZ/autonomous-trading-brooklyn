import torch
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import pandas as pd

from models.rl_model import PPONetwork
from data.market_data import MarketDataProvider
from data.feature_engineer import FeatureEngineer
from .portfolio_manager import PortfolioManager
from .risk_manager import RiskManager
from .recall_client import RecallClient
from config.config import config
from config.tokens import TRADING_PAIRS

logger = logging.getLogger(__name__)

class StrategyEngine:
    """Main trading strategy engine combining RL model with traditional risk management"""
    
    def __init__(self, recall_client: RecallClient):
        self.recall_client = recall_client
        self.portfolio_manager = PortfolioManager(recall_client)
        self.risk_manager = RiskManager()
        self.market_data = MarketDataProvider()
        self.feature_engineer = FeatureEngineer()
        
        # Load trained model
        self.model = self._load_model()
        self.model.eval()
        
        # Trading state
        self.active_positions: Dict[str, Dict] = {}
        self.last_trade_time: Dict[str, datetime] = {}
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0.0
        }
        
    def _load_model(self) -> PPONetwork:
        """Load trained PPO model"""
        
        try:
            model = PPONetwork(state_dim=46, action_dim=6)
            
            if config.MODEL_PATH and torch.cuda.is_available():
                model.load_state_dict(torch.load(config.MODEL_PATH))
            else:
                model.load_state_dict(torch.load(config.MODEL_PATH, map_location='cpu'))
                
            logger.info("RL model loaded successfully")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            # Return initialized model if loading fails
            return PPONetwork(state_dim=46, action_dim=6)
    
    async def execute_trading_cycle(self) -> bool:
        """Execute one complete trading cycle"""
        
        try:
            # Update portfolio state
            await self.portfolio_manager.update_portfolio_state()
            
            # Update market data
            await self.market_data.update_market_data()
            
            # Process each trading pair
            for pair in TRADING_PAIRS:
                await self._process_trading_pair(pair)
            
            # Log performance
            self._log_performance()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            return False
    
    async def _process_trading_pair(self, pair: Dict) -> None:
        """Process trading decisions for a specific pair"""
        
        pair_name = pair["name"]
        base_token = pair["base"]
        quote_token = pair["quote"]
        
        try:
            # Get current market state
            market_state = await self._get_market_state(pair)
            
            if market_state is None:
                logger.warning(f"No market data available for {pair_name}")
                return
            
            # Get current positions
            base_position = self.portfolio_manager.get_position_size(base_token["address"])
            quote_position = self.portfolio_manager.get_position_size(quote_token["address"])
            
            # Create state vector for RL model
            state_vector = self._create_state_vector(market_state, base_position, quote_position)
            
            # Get action from RL model
            action = self._get_model_action(state_vector)
            
            # Validate action with risk manager
            is_valid, validation_message = self.risk_manager.validate_trade(
                action,
                self.portfolio_manager.portfolio_value,
                self.portfolio_manager.initial_balance,
                {base_token["address"]: base_position, quote_token["address"]: quote_position}
            )
            
            if not is_valid:
                logger.info(f"Trade blocked by risk manager: {validation_message}")
                return
            
            # Execute trade if action is not hold
            if action != 0:
                await self._execute_trade_action(pair, action, market_state)
                
        except Exception as e:
            logger.error(f"Error processing trading pair {pair_name}: {e}")
    
    def _get_model_action(self, state_vector: np.ndarray) -> int:
        """Get action from RL model"""
        
        try:
            state_tensor = torch.FloatTensor(state_vector).unsqueeze(0)
            
            with torch.no_grad():
                # For this simplified version, we'll focus on base token actions
                # Model returns probabilities for both tokens, we'll use base token probs
                base_probs, _, _ = self.model(state_tensor)
                
                # Sample action from probability distribution
                action_dist = torch.distributions.Categorical(base_probs)
                action = action_dist.sample().item()
                
            return action
            
        except Exception as e:
            logger.error(f"Error getting model action: {e}")
            return 0  # Default to hold
    
    async def _execute_trade_action(self, pair: Dict, action: int, market_state: Dict) -> None:
        """Execute the trading action"""
        
        base_token = pair["base"]
        quote_token = pair["quote"]
        pair_name = pair["name"]
        
        # Get current positions
        base_position = self.portfolio_manager.get_position_size(base_token["address"])
        quote_position = self.portfolio_manager.get_position_size(quote_token["address"])
        
        # Calculate trade amounts
        base_price = market_state.get("price", 0)
        
        if base_price == 0:
            logger.error("Invalid price data for trade execution")
            return
        
        try:
            if action == 1:  # Buy 10% base token
                trade_amount = self.portfolio_manager.calculate_position_size_for_trade(1, base_position, base_price)
                await self._execute_buy_trade(base_token, quote_token, trade_amount, "RL Model: Buy 10% signal")
                
            elif action == 2:  # Buy 25% base token
                trade_amount = self.portfolio_manager.calculate_position_size_for_trade(2, base_position, base_price)
                await self._execute_buy_trade(base_token, quote_token, trade_amount, "RL Model: Buy 25% signal")
                
            elif action == 3:  # Sell 10% base token
                trade_amount = self.portfolio_manager.calculate_position_size_for_trade(3, base_position, base_price)
                await self._execute_sell_trade(base_token, quote_token, trade_amount, "RL Model: Sell 10% signal")
                
            elif action == 4:  # Sell 25% base token
                trade_amount = self.portfolio_manager.calculate_position_size_for_trade(4, base_position, base_price)
                await self._execute_sell_trade(base_token, quote_token, trade_amount, "RL Model: Sell 25% signal")
                
            elif action == 5:  # Close all positions
                if base_position > 0:
                    await self._execute_sell_trade(base_token, quote_token, base_position, "RL Model: Close all positions")
                    
        except Exception as e:
            logger.error(f"Error executing trade action: {e}")
    
    async def _execute_buy_trade(self, base_token: Dict, quote_token: Dict, amount: float, reason: str) -> None:
        """Execute buy trade (quote token -> base token)"""
        
        if amount <= 0:
            return
        
        # Calculate quote token amount needed
        quote_amount = amount * self.market_data.get_current_price(base_token["symbol"])
        
        # Check if we have enough quote tokens
        available_quote = self.portfolio_manager.get_available_balance_for_token(quote_token["address"])
        
        if available_quote < quote_amount:
            logger.warning(f"Insufficient {quote_token['symbol']} balance for buy trade")
            return
        
        # Execute trade via Recall API
        result = self.recall_client.execute_trade(
            from_token=quote_token["address"],
            to_token=base_token["address"],
            amount=str(quote_amount),
            reason=reason,
            from_chain=quote_token["chain"],
            to_chain=base_token["chain"],
            from_specific_chain=quote_token["specificChain"],
            to_specific_chain=base_token["specificChain"]
        )
        
        if result.get("success"):
            logger.info(f"Buy trade executed: {quote_amount} {quote_token['symbol']} -> {base_token['symbol']}")
            self.performance_metrics["total_trades"] += 1
        else:
            logger.error(f"Buy trade failed: {result.get('error')}")
    
    async def _execute_sell_trade(self, base_token: Dict, quote_token: Dict, amount: float, reason: str) -> None:
        """Execute sell trade (base token -> quote token)"""
        
        if amount <= 0:
            return
        
        # Check if we have enough base tokens
        available_base = self.portfolio_manager.get_available_balance_for_token(base_token["address"])
        
        if available_base < amount:
            logger.warning(f"Insufficient {base_token['symbol']} balance for sell trade")
            return
        
        # Execute trade via Recall API
        result = self.recall_client.execute_trade(
            from_token=base_token["address"],
            to_token=quote_token["address"],
            amount=str(amount),
            reason=reason,
            from_chain=base_token["chain"], 
            to_chain=quote_token["chain"],
            from_specific_chain=base_token["specificChain"],
            to_specific_chain=quote_token["specificChain"]
        )
        
        if result.get("success"):
            logger.info(f"Sell trade executed: {amount} {base_token['symbol']} -> {quote_token['symbol']}")
            self.performance_metrics["total_trades"] += 1
        else:
            logger.error(f"Sell trade failed: {result.get('error')}")
    
    async def _get_market_state(self, pair: Dict) -> Optional[Dict]:
        """Get current market state for a trading pair"""
        
        base_symbol = pair["base"]["symbol"]
        
        # This would typically get data from Binance or other market data provider
        # For now, we'll use portfolio data as proxy
        try:
            portfolio_data = self.recall_client.get_portfolio()
            
            if portfolio_data.get("success"):
                tokens = portfolio_data.get("tokens", [])
                for token in tokens:
                    if token.get("symbol") == base_symbol:
                        return {
                            "symbol": base_symbol,
                            "price": token.get("price", 0),
                            "timestamp": datetime.now()
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting market state: {e}")
            return None
    
    def _create_state_vector(self, market_state: Dict, base_position: float, quote_position: float) -> np.ndarray:
        """Create state vector for RL model"""
        
        # For this simplified version, create a basic state vector
        # In production, this would include technical indicators, market data, etc.
        
        portfolio_value = self.portfolio_manager.portfolio_value
        initial_balance = self.portfolio_manager.initial_balance
        
        state = np.array([
            # Price and market data (placeholder - would be real technical indicators)
            market_state.get("price", 0) / 1000,  # Normalized price
            0.5,  # Placeholder for RSI
            0.0,  # Placeholder for MACD
            1.0,  # Placeholder for volume ratio
            
            # Position information
            base_position / initial_balance if initial_balance > 0 else 0,
            quote_position / initial_balance if initial_balance > 0 else 0,
            
            # Portfolio metrics
            portfolio_value / initial_balance if initial_balance > 0 else 1,
            (portfolio_value - initial_balance) / initial_balance if initial_balance > 0 else 0,
            
            # Risk metrics
            max(0, (initial_balance - portfolio_value) / initial_balance) if initial_balance > 0 else 0,
            
            # Add padding to reach 46 dimensions as expected by model
            *[0.0] * 37  # Placeholder features
        ], dtype=np.float32)
        
        return state
    
    def _log_performance(self) -> None:
        """Log current performance metrics"""
        
        metrics = self.portfolio_manager.get_portfolio_metrics()
        
        logger.info(f"Portfolio Performance:")
        logger.info(f"  Total Value: ${metrics.get('total_value', 0):.2f}")
        logger.info(f"  Total Return: {metrics.get('total_return', 0):.2%}")
        logger.info(f"  Total Trades: {self.performance_metrics['total_trades']}")
        logger.info(f"  P&L: ${metrics.get('profit_loss', 0):.2f}")
