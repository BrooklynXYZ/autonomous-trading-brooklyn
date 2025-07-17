# Autonomous Trading Agent

A modular, AI-powered trading bot designed to autonomously trade and compound profits, with support for backtesting, paper trading, and live deployment.

## Features

- AI-driven signal generation (supports custom ML models)
- Modular strategy and risk management
- Compounding wallet logic (e.g., every 12 hours or per trade)
- Backtesting with dummy or historical data
- Paper trading and live trading via exchange APIs (CCXT)
- Easy configuration and extension

## Project Structure

```
autonomous-trading-agent/
├── src/
│   ├── core/
│   ├── trading/
│   ├── ai/
│   ├── strategies/
│   ├── data/
│   └── utils/
├── config/
├── scripts/
├── tests/
└── requirements.txt
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd autonomous-trading-agent
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Configure your settings**
   - Edit config files in `config/` for trading parameters, API keys, and AI model settings

## Usage

### Backtesting with Dummy Money
```bash
python scripts/backtest.py
```
- Simulates 25 compounding trades with dummy money

### Run the Trading Bot (Live/Paper)
```bash
python scripts/run_bot.py
```

## Configuration

- `config/main.yaml`: Main settings (API keys, currencies, risk parameters)
- `config/trading.yaml`: Trading pairs, max drawdown, intervals
- `config/ai.yaml`: AI model type, features, and parameters

## Testing

- Unit and integration tests are located in `tests/`
- Run all tests:
  ```bash
  pytest
  ```

## Safety and Risk Management

⚠️ **Important**: Always test your strategies thoroughly with paper trading before deploying with real funds. This bot can result in significant financial losses if not properly configured.

- Start with small amounts
- Use proper stop-loss and take-profit settings
- Monitor the bot's performance regularly
- Understand the risks involved in automated trading

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

Please document any new strategies or modules thoroughly.

## Requirements

- Python 3.8+
- See `requirements.txt` for full dependency list
- Exchange API keys (for live trading)

## Roadmap

- [ ] Advanced AI model integration
- [ ] Multi-exchange support
- [ ] Enhanced backtesting capabilities
- [ ] Web dashboard for monitoring
- [ ] Mobile notifications

## License

MIT License - see LICENSE file for details

## Support

- Open an issue on GitHub for bug reports
- Start a discussion for feature requests or general questions
- Check the documentation in the `docs/` folder (if available)

## Disclaimer

This software is for educational and research purposes. Trading cryptocurrencies and other financial instruments involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results. Use at your own risk.

---

**Note**: This setup allows you to validate your compounding logic and wallet growth before using real money or integrating advanced AI trading logic. Adjust the backtest parameters to reflect your specific strategy and risk profile.