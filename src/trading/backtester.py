



########
import pandas as pd
import numpy as np
from tqdm import tqdm
from data.types import BacktestResult

class Backtester:
    def __init__(self, agent, data, capital=10000):
        self.agent = agent
        self.data = data
        self.initial_capital = capital
        self.cash = capital
        self.coin = 0
        self.history = []

    def run(self):
        for i in tqdm(range(len(self.data) - 1)):
            row = self.data.iloc[i]
            next_row = self.data.iloc[i + 1]
            state = self.agent.preprocess(row)
            action = self.agent.act(state)

            price = row['close']
            if action == 1 and self.cash > 0:  # BUY
                self.coin = self.cash / price
                self.cash = 0
            if action == 2 and self.coin > 0:  # SELL
                self.cash += self.coin * price
                self.coin = 0

            next_state = self.agent.preprocess(next_row)
            next_price = next_row['close']
            total_value = self.cash + self.coin * price
            future_value = self.cash + self.coin * next_price

            reward = (future_value - total_value) / total_value
            self.agent.remember(state, action, reward, next_state, False)
            self.agent.replay()

            self.history.append(future_value)

        return pd.DataFrame({
            'portfolio_value': self.history
        })
# Add this method to the existing CryptoBacktester class

async def run_enhanced_backtest(self, agent, symbol: str, 
                              start_date: str, end_date: str, 
                              timeframe: str = '1h') -> BacktestResult:
    """
    Enhanced backtest with simulated whale data
    """
    logger.info(f"Starting enhanced backtest with whale simulation: {symbol}")
    
    # Initialize whale tracker for the agent
    await agent.initialize_whale_tracker()
    
    try:
        # Run normal backtest but with enhanced market data
        data = self._prepare_backtest_data(symbol, start_date, end_date, timeframe)
        
        if len(data) < 100:
            logger.error(f"Insufficient data for backtesting: {len(data)} records")
            return self._create_empty_result()
        
        # Add simulated whale data to backtest data
        data = await self._add_whale_simulation(data, symbol)
        
        # Reset portfolio state
        self._reset_portfolio()
        
        # Run backtest with enhanced data
        for i in range(50, len(data)):
            current_data = data.iloc[:i+1].copy()
            current_row = data.iloc[i]
            
            try:
                # Get enhanced market data (now includes whale features)
                raw_data = await agent.get_enhanced_market_data(symbol)
                raw_data.update(current_row.to_dict())
                
                # Preprocess with whale features
                state = agent.preprocess(raw_data)
                current_price = current_row['close']
                
                # Generate trading signal
                action = agent.act(state)
                
                # Execute trade
                if action != 0:  # Not HOLD
                    self._execute_enhanced_trade(action, current_price, current_row['timestamp'], raw_data)
                
                # Calculate portfolio value and continue with rest of backtesting logic
                portfolio_value = self._calculate_portfolio_value({symbol: current_price})
                
                # Store history
                self.equity_curve.append(portfolio_value)
                self.timestamps.append(current_row['timestamp'])
                
                # Train agent
                if i % 5 == 0:
                    reward = self._calculate_enhanced_reward(portfolio_value, raw_data)
                    if hasattr(agent, 'last_state') and agent.last_state is not None:
                        agent.remember(agent.last_state, action, reward, state, False)
                        if i % 10 == 0:
                            agent.replay()
                    agent.last_state = state.copy()
                
                # Progress logging
                if i % 500 == 0:
                    logger.info(f"Enhanced Progress: {i}/{len(data)} | Portfolio: ${portfolio_value:,.2f}")
                    
            except Exception as e:
                logger.error(f"Error at enhanced step {i}: {e}")
                continue
        
        # Calculate final results
        result = self._calculate_backtest_results(start_date, end_date, symbol)
        logger.success(f"Enhanced backtest completed! Final return: {result.total_return:.2%}")
        
        return result
        
    finally:
        # Cleanup
        await agent.cleanup()

async def _add_whale_simulation(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """Add simulated whale data to backtest data"""
    import random
    import numpy as np
    
    # Simulate whale transactions based on market conditions
    data = data.copy()
    
    for i in range(len(data)):
        row = data.iloc[i]
        
        # Simulate whale activity based on price volatility
        volatility = abs(row.get('close', 0) - row.get('open', 0)) / row.get('open', 1)
        
        # Higher volatility = more whale activity
        whale_activity_factor = min(volatility * 10, 1)
        
        # Simulate whale flows
        base_flow = random.uniform(-5000000, 5000000)  # -5M to +5M USD
        whale_flow = base_flow * (1 + whale_activity_factor)
        
        # Add whale features to the data
        data.loc[i, 'whale_flow'] = whale_flow
        data.loc[i, 'whale_inflow'] = max(0, whale_flow) + random.uniform(0, 2000000)
        data.loc[i, 'whale_outflow'] = max(0, -whale_flow) + random.uniform(0, 2000000)
        data.loc[i, 'net_whale_flow'] = whale_flow
        data.loc[i, 'whale_tx_count'] = max(1, int(abs(whale_flow) / 500000))
        data.loc[i, 'avg_whale_tx_size'] = abs(whale_flow) / data.loc[i, 'whale_tx_count'] if data.loc[i, 'whale_tx_count'] > 0 else 0
        data.loc[i, 'largest_whale_tx'] = data.loc[i, 'avg_whale_tx_size'] * random.uniform(1.5, 3.0)
        data.loc[i, 'whale_exchange_ratio'] = random.uniform(0.3, 0.8)
        
        # Multi-chain flows
        for chain in ['eth', 'btc', 'sol', 'base', 'bsc', 'arb']:
            data.loc[i, f'{chain}_whale_flow'] = whale_flow * random.uniform(0.1, 0.3)
        
        # AI-derived scores
        data.loc[i, 'whale_accumulation_score'] = random.uniform(-1, 1)
        data.loc[i, 'whale_distribution_score'] = -data.loc[i, 'whale_accumulation_score']
        data.loc[i, 'whale_manipulation_risk'] = random.uniform(0, 1)
        
        # Additional whale metrics
        data.loc[i, 'whale_concentration'] = random.uniform(0, 1)
        data.loc[i, 'new_whale_addresses'] = random.randint(0, 20)
        data.loc[i, 'active_whale_addresses'] = random.randint(50, 500)
    
    return data

def _execute_enhanced_trade(self, action, price, timestamp, market_data):
    """Execute trade with whale data considerations"""
    # Consider whale manipulation risk in position sizing
    manipulation_risk = market_data.get('whale_manipulation_risk', 0)
    risk_adjustment = 1 - (manipulation_risk * 0.3)  # Reduce position size if high risk
    
    # Adjust position size based on whale accumulation
    accumulation_score = market_data.get('whale_accumulation_score', 0)
    if action == 1 and accumulation_score > 0.5:  # BUY and whales accumulating
        risk_adjustment *= 1.2  # Increase position size
    elif action == 2 and accumulation_score < -0.5:  # SELL and whales distributing  
        risk_adjustment *= 1.2  # Increase position size
    
    # Use the regular trade execution with adjusted size
    base_size = 0.01  # Base position size
    adjusted_size = base_size * risk_adjustment
    
    # Execute with adjusted size (simplified)
    if action == 1:  # BUY
        self.cash -= adjusted_size * price * 1.001  # Include small fee
    elif action == 2:  # SELL
        self.cash += adjusted_size * price * 0.999  # Include small fee

def _calculate_enhanced_reward(self, portfolio_value, market_data) -> float:
    """Calculate reward considering whale data"""
    if not self.portfolio_history:
        return 0.0
    
    # Base reward from portfolio change
    prev_value = self.portfolio_history[-1]['portfolio_value'] if self.portfolio_history else self.initial_capital
    base_reward = (portfolio_value - prev_value) / prev_value
    
    # Whale-based reward adjustments
    whale_score_bonus = 0
    
    # Bonus for trading with whale accumulation
    accumulation_score = market_data.get('whale_accumulation_score', 0)
    if accumulation_score > 0.3:  # Whales accumulating
        whale_score_bonus += 0.01
    elif accumulation_score < -0.3:  # Whales distributing
        whale_score_bonus -= 0.01
    
    # Penalty for high manipulation risk
    manipulation_risk = market_data.get('whale_manipulation_risk', 0)
    if manipulation_risk > 0.7:
        whale_score_bonus -= 0.02
    
    return base_reward + whale_score_bonus
