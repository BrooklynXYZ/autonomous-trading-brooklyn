import logging
from typing import Dict, Tuple, List
from datetime import datetime, timedelta

from config.config import config

logger = logging.getLogger(__name__)

class RiskManager:
    """Manages trading risk and validates trade decisions"""
    
    def __init__(self):
        self.max_portfolio_risk = config.MAX_PORTFOLIO_RISK
        self.max_position_size = config.MAX_POSITION_SIZE  
        self.max_daily_trades = config.MAX_DAILY_TRADES
        self.emergency_stop_threshold = config.EMERGENCY_STOP_THRESHOLD
        
        # Daily tracking
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        # Trade tracking
        self.recent_trades: List[Dict] = []
        self.consecutive_losses = 0
        
    def validate_trade(
        self, 
        action: int,
        portfolio_value: float,
        initial_balance: float, 
        positions: Dict[str, float]
    ) -> Tuple[bool, str]:
        """
        Validate if a trade action should be allowed
        
        Args:
            action: Trading action (0=hold, 1-2=buy, 3-5=sell)
            portfolio_value: Current portfolio value
            initial_balance: Initial balance
            positions: Current positions dict
            
        Returns:
            Tuple of (is_valid, reason)
        """
        
        # Reset daily counters if new day
        self._reset_daily_counters_if_needed()
        
        # Check emergency stop
        if self._check_emergency_stop(portfolio_value, initial_balance):
            return False, "Emergency stop triggered - portfolio loss exceeds threshold"
        
        # Check daily trade limit
        if self.daily_trades >= self.max_daily_trades:
            return False, "Daily trade limit exceeded"
        
        # Check if action is hold (always allowed)
        if action == 0:
            return True, "Hold action approved"
        
        # Check portfolio drawdown
        current_drawdown = max(0, (initial_balance - portfolio_value) / initial_balance) if initial_balance > 0 else 0
        
        if current_drawdown > self.max_portfolio_risk:
            # Only allow closing positions during high drawdown
            if action not in [5]:  # Action 5 = close all
                return False, f"Portfolio drawdown ({current_drawdown:.1%}) exceeds limit - only position closing allowed"
        
        # Check position size limits for buy actions
        if action in [1, 2]:  # Buy actions
            total_position_value = sum(abs(pos) for pos in positions.values())
            position_ratio = total_position_value / portfolio_value if portfolio_value > 0 else 0
            
            additional_exposure = 0.10 if action == 1 else 0.25
            
            if position_ratio + additional_exposure > self.max_position_size:
                return False, f"Position size would exceed limit ({self.max_position_size:.1%})"
        
        # Check consecutive losses
        if self.consecutive_losses >= 3:
            # Reduce position sizing after consecutive losses
            if action in [2]:  # Large buy action
                return False, "Large position sizing blocked after consecutive losses"
        
        # All checks passed
        return True, "Trade approved"
    
    def record_trade_result(self, pnl: float, trade_info: Dict = None) -> None:
        """Record the result of a trade for risk tracking"""
        
        self.daily_trades += 1
        self.daily_pnl += pnl
        
        # Track recent trades
        trade_record = {
            "timestamp": datetime.now(),
            "pnl": pnl,
            "info": trade_info or {}
        }
        
        self.recent_trades.append(trade_record)
        
        # Keep only last 50 trades
        if len(self.recent_trades) > 50:
            self.recent_trades = self.recent_trades[-50:]
        
        # Update consecutive loss counter
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        logger.info(f"Trade recorded - PnL: ${pnl:.2f}, Consecutive losses: {self.consecutive_losses}")
    
    def get_position_size_multiplier(self) -> float:
        """Get position size multiplier based on recent performance"""
        
        if self.consecutive_losses >= 3:
            return 0.5  # Reduce position size after losses
        elif self.consecutive_losses >= 2:
            return 0.75
        else:
            return 1.0  # Normal position sizing
    
    def _check_emergency_stop(self, portfolio_value: float, initial_balance: float) -> bool:
        """Check if emergency stop should be triggered"""
        
        if initial_balance == 0:
            return False
            
        total_loss_ratio = (initial_balance - portfolio_value) / initial_balance
        
        return total_loss_ratio > self.emergency_stop_threshold
    
    def _reset_daily_counters_if_needed(self) -> None:
        """Reset daily counters if it's a new day"""
        
        current_date = datetime.now().date()
        
        if current_date > self.last_reset_date:
            self.daily_trades = 0
            self.daily_pnl = 0.0
            self.last_reset_date = current_date
            logger.info("Daily risk counters reset for new trading day")
    
    def get_risk_metrics(self) -> Dict[str, float]:
        """Get current risk metrics"""
        
        recent_pnl = sum(trade["pnl"] for trade in self.recent_trades[-10:])  # Last 10 trades
        
        return {
            "daily_trades": self.daily_trades,
            "daily_pnl": self.daily_pnl,
            "consecutive_losses": self.consecutive_losses,
            "recent_pnl": recent_pnl,
            "position_size_multiplier": self.get_position_size_multiplier()
        }
