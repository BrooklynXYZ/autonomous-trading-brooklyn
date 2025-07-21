#!/usr/bin/env python3
# =============================================================================
# BACKTEST RUNNER SCRIPT
# =============================================================================

import os
import sys
import asyncio
from datetime import datetime, timedelta
import argparse
from loguru import logger

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.trading.backtester import CryptoBacktester
from src.agents.btc_eth_agent import BTCETHAgent
from src.utils.config_loader import config

def setup_logging():
    """Setup logging configuration"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # File logging
    os.makedirs("logs", exist_ok=True)
    logger.add(
        "logs/backtest_{time}.log",
        rotation="100 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG"
    )

def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description='Run crypto trading bot backtest')
    parser.add_argument('--symbol', default='BTC/USDT', help='Trading symbol')
    parser.add_argument('--start-date', default='2024-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2024-06-30', help='End date (YYYY-MM-DD)')
    parser.add_argument('--timeframe', default='1h', help='Timeframe (15m, 1h, 4h, 1d)')
    parser.add_argument('--capital', type=float, default=10000, help='Initial capital')
    parser.add_argument('--save-plots', action='store_true', help='Save result plots')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🚀 CRYPTO TRADING BOT BACKTEST")
    logger.info("=" * 60)
    logger.info(f"Symbol: {args.symbol}")
    logger.info(f"Period: {args.start_date} to {args.end_date}")
    logger.info(f"Timeframe: {args.timeframe}")
    logger.info(f"Initial Capital: ${args.capital:,}")
    logger.info("=" * 60)
    
    try:
        # Validate API keys
        api_status = config.validate_keys()
        logger.info("API Key Status:")
        for service, status in api_status.items():
            status_icon = "✅" if status else "❌"
            logger.info(f"  {service}: {status_icon}")
        
        if not any(api_status.values()):
            logger.warning("No API keys configured! Using simulated data only.")
        
        # Initialize components
        logger.info("Initializing backtester and agent...")
        backtester = CryptoBacktester(initial_capital=args.capital)
        agent = BTCETHAgent()
        
        # Run backtest
        logger.info("Starting backtest...")
        start_time = datetime.now()
        
        result = backtester.run_backtest(
            agent=agent,
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            timeframe=args.timeframe
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Display results
        logger.info("=" * 60)
        logger.info("📊 BACKTEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total Return: {result.total_return:.2%}")
        logger.info(f"Annualized Return: {result.annualized_return:.2%}")
        logger.info(f"Max Drawdown: {result.max_drawdown:.2%}")
        logger.info(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
        logger.info(f"Win Rate: {result.win_rate:.1%}")
        logger.info(f"Total Trades: {result.total_trades}")
        logger.info(f"Final Portfolio Value: ${result.final_capital:,.2f}")
        logger.info("=" * 60)
        logger.info(f"Backtest Duration: {duration}")
        
        # Plot results
        if args.save_plots:
            os.makedirs("results", exist_ok=True)
            plot_path = f"results/backtest_{args.symbol.replace('/', '_')}_{args.start_date}_{args.end_date}.png"
            backtester.plot_results(result, save_path=plot_path)
        else:
            backtester.plot_results(result)
        
        # Save detailed results
        if result.total_trades > 0:
            logger.info(f"Saving detailed results...")
            import pandas as pd
            
            trades_df = pd.DataFrame(result.trades)
            equity_df = pd.DataFrame({
                'timestamp': result.timestamps,
                'portfolio_value': result.equity_curve
            })
            
            os.makedirs("results", exist_ok=True)
            trades_df.to_csv(f"results/trades_{args.symbol.replace('/', '_')}_{args.start_date}.csv", index=False)
            equity_df.to_csv(f"results/equity_{args.symbol.replace('/', '_')}_{args.start_date}.csv", index=False)
            
            logger.success("Results saved to CSV files")
        
        # Performance assessment
        if result.total_return > 0.1:  # >10% return
            logger.success("🎉 PROFITABLE STRATEGY!")
        elif result.total_return > 0:
            logger.info("📈 Modest gains")
        else:
            logger.warning("📉 Strategy needs improvement")
            
        logger.success("Backtest completed successfully!")
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()



# #########


# import pandas as pd
# import matplotlib.pyplot as plt
# from src.agents.btc_eth_agent import BTCETHAgent
# from src.trading.backtester import Backtester

# # Load sample price data
# data = pd.read_csv('data/sample_backtest.csv', parse_dates=['timestamp'])

# # Pretend we have derived features
# data['rsi'] = 50 + np.random.rand(len(data)) * 10
# data['macd'] = np.random.rand(len(data)) * 2 - 1
# data['sma_fast'] = data['close'].rolling(5).mean().fillna(method='bfill')
# data['sma_slow'] = data['close'].rolling(20).mean().fillna(method='bfill')
# data['sentiment'] = np.random.rand(len(data)) * 2 - 1
# data['whale_flow'] = np.random.rand(len(data)) - 0.5

# # Build agent
# agent = BTCETHAgent()

# # Run backtest
# bt = Backtester(agent, data)
# results = bt.run()

# # Plot results
# plt.plot(results['portfolio_value'])
# plt.title("Portfolio Value Over Time")
# plt.xlabel("Steps")
# plt.ylabel("USD Value")
# plt.grid(True)
# plt.savefig("results/backtest_plot.png")
# plt.show()
# ########