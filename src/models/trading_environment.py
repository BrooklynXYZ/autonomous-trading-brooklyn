import gym
from gym import spaces
import numpy as np
import pandas as pd

class TradingEnvironment(gym.Env):
    """Simplified trading environment for RL training"""
    
    def __init__(self, data, initial_balance=10000):
        super().__init__()
        
        self.data = data
        self.initial_balance = initial_balance
        self.current_step = 0
        self.max_steps = len(data) - 1
        
        # Portfolio state
        self.balance = initial_balance
        self.position = 0.0  # Current position size
        self.portfolio_value = initial_balance
        
        # Trading metrics
        self.total_trades = 0
        self.winning_trades = 0
        
        # Action space: 0=Hold, 1=Buy10%, 2=Buy25%, 3=Sell10%, 4=Sell25%, 5=CloseAll
        self.action_space = spaces.Discrete(6)
        
        # Observation space: market features + portfolio state
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(46,), dtype=np.float32
        )
        
    def reset(self):
        """Reset environment to initial state"""
        
        self.current_step = 50  # Start after some data for indicators
        self.balance = self.initial_balance
        self.position = 0.0
        self.portfolio_value = self.initial_balance
        self.total_trades = 0
        self.winning_trades = 0
        
        return self._get_observation()
    
    def step(self, action):
        """Execute one trading step"""
        
        # Get current price (simplified)
        current_price = self._get_current_price()
        
        # Calculate portfolio value before action
        prev_portfolio_value = self._calculate_portfolio_value(current_price)
        
        # Execute action
        self._execute_action(action, current_price)
        
        # Calculate new portfolio value
        new_portfolio_value = self._calculate_portfolio_value(current_price)
        
        # Calculate reward
        reward = self._calculate_reward(prev_portfolio_value, new_portfolio_value)
        
        # Move to next step
        self.current_step += 1
        done = self.current_step >= self.max_steps
        
        # Get new observation
        observation = self._get_observation()
        
        info = {
            'portfolio_value': new_portfolio_value,
            'position': self.position,
            'current_price': current_price
        }
        
        return observation, reward, done, info
    
    def _get_observation(self):
        """Get current state observation"""
        
        # Use current data row as market features (first 44 dimensions)
        if hasattr(self.data, 'iloc'):
            market_features = self.data.iloc[self.current_step].values[:44]
        else:
            market_features = self.data[self.current_step][:44]
        
        # Add portfolio features
        portfolio_features = np.array([
            self.position / self.initial_balance,  # Normalized position
            self.portfolio_value / self.initial_balance - 1  # Portfolio return
        ])
        
        observation = np.concatenate([market_features, portfolio_features]).astype(np.float32)
        
        # Ensure correct dimensions
        if len(observation) < 46:
            observation = np.pad(observation, (0, 46 - len(observation)))
        elif len(observation) > 46:
            observation = observation[:46]
            
        return observation
    
    def _execute_action(self, action, current_price):
        """Execute trading action"""
        
        trade_executed = False
        
        if action == 1:  # Buy 10%
            trade_amount = (self.balance * 0.10) / current_price
            if self.balance >= trade_amount * current_price:
                self.position += trade_amount
                self.balance -= trade_amount * current_price
                trade_executed = True
                
        elif action == 2:  # Buy 25%
            trade_amount = (self.balance * 0.25) / current_price
            if self.balance >= trade_amount * current_price:
                self.position += trade_amount
                self.balance -= trade_amount * current_price
                trade_executed = True
                
        elif action == 3:  # Sell 10%
            trade_amount = abs(self.position) * 0.10
            if abs(self.position) >= trade_amount:
                self.position -= trade_amount
                self.balance += trade_amount * current_price
                trade_executed = True
                
        elif action == 4:  # Sell 25%
            trade_amount = abs(self.position) * 0.25
            if abs(self.position) >= trade_amount:
                self.position -= trade_amount
                self.balance += trade_amount * current_price
                trade_executed = True
                
        elif action == 5:  # Close all
            if abs(self.position) > 0:
                self.balance += self.position * current_price
                self.position = 0.0
                trade_executed = True
        
        if trade_executed:
            self.total_trades += 1
    
    def _calculate_portfolio_value(self, current_price):
        """Calculate total portfolio value"""
        return self.balance + (self.position * current_price)
    
    def _get_current_price(self):
        """Get current market price (simplified)"""
        
        # Simulate price based on step
        base_price = 2000  # Base price for simulation
        volatility = 0.02
        
        # Add some random walk
        price_change = np.random.normal(0, volatility)
        return base_price * (1 + price_change)
    
    def _calculate_reward(self, prev_value, new_value):
        """Calculate reward for the action"""
        
        # Primary reward: portfolio return
        portfolio_return = (new_value - prev_value) / prev_value if prev_value > 0 else 0
        
        # Risk penalty for large drawdowns
        current_drawdown = max(0, (self.initial_balance - new_value) / self.initial_balance)
        risk_penalty = -current_drawdown * 2
        
        # Encourage trading (small bonus)
        activity_bonus = 0.001 if self.total_trades > 0 else 0
        
        total_reward = portfolio_return * 100 + risk_penalty + activity_bonus
        
        return total_reward
