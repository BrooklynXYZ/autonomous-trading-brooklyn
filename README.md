# Recall Network AI Trading Agent

An AI-powered trading agent for Recall Network's trading competitions using Reinforcement Learning (PPO) combined with traditional risk management.

## Features

- 🤖 **PPO Reinforcement Learning Model** for intelligent trading decisions
- 🛡️ **Advanced Risk Management** with multiple safety layers  
- 📊 **Real-time Portfolio Management** via Recall Network API
- 🔄 **Automated Trading Cycles** with configurable frequency
- 📈 **Multi-pair Trading** focusing on ETH/USDC and SOL/USDC
- 🚨 **Emergency Stop Mechanisms** for loss protection
- 📝 **Comprehensive Logging** and performance tracking

## Quick Start

### 1. Clone and Setup
```
git clone 
cd recall-ai-trader
pip install -r requirements.txt
```

### 2. Configuration
```
cp .env.example .env
# Edit .env with your Recall Network API token
```

### 3. Run the Trading Bot
```
python src/main.py
```

### 4. Docker Deployment
```
docker build -t recall-ai-trader .
docker run -d --env-file .env recall-ai-trader
```

## Trading Strategy

The bot uses a hybrid approach combining:

- **Reinforcement Learning (PPO)**: Learns optimal trading patterns from market data
- **Risk Management**: Traditional stop-losses, position sizing, and drawdown protection  
- **Portfolio Optimization**: Dynamic position sizing based on performance and volatility

## Performance Targets

- **Conservative**: 8-15% daily returns with <12% max drawdown
- **Optimistic**: 20-35% daily returns with proper risk management
- **Risk-First**: Maximum 15% portfolio drawdown with emergency stops

## API Integration

Integrates with Recall Network APIs:
- `/api/trade/execute` - Execute trades
- `/api/agent/portfolio` - Monitor portfolio value
- `/api/agent/balances` - Track token balances  
- `/api/agent/trades` - Review trade history

## Configuration

Key parameters in `config/config.py`:
- `MAX_PORTFOLIO_RISK`: Maximum allowed portfolio drawdown (default: 15%)
- `MAX_POSITION_SIZE`: Maximum position size per trade (default: 30%)
- `MAX_DAILY_TRADES`: Daily trade limit (default: 50)
- `UPDATE_FREQUENCY`: Trading cycle frequency in seconds (default: 60)

## Monitoring

The bot provides comprehensive logging including:
- Trade execution details
- Portfolio performance metrics
- Risk management decisions
- Model predictions and confidence scores

## Safety Features

- **Emergency Stops**: Automatic shutdown at 25% portfolio loss
- **Position Limits**: Maximum 30% allocation per position
- **Daily Limits**: Maximum 50 trades per day
- **Consecutive Loss Protection**: Reduced position sizing after losses
- **Real-time Risk Monitoring**: Continuous portfolio risk assessment

## Development

### Running Tests
```
pytest tests/
```

### Training the Model
```
python scripts/train_model.py
```

### Running Backtests  
```
python scripts/run_backtest.py
```

## Support

For issues and questions:
1. Check the logs in `logs/` directory
2. Review configuration in `config/config.py`
3. Ensure API token is correctly set in `.env`

## Disclaimer

This trading bot is for educational and competition purposes. Past performance does not guarantee future results. Use at your own risk. 