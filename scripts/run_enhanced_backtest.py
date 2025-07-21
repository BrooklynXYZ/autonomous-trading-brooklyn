#!/usr/bin/env python3
import sys
import os

# Add src/ to Python's module path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import asyncio
from datetime import datetime
import argparse
from loguru import logger
from trading.backtester import CryptoBacktester
from agents.btc_eth_agent import BTCETHAgent
from data.whale_feed import get_multi_chain_whale_data


def setup_logging():
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    os.makedirs("logs", exist_ok=True)
    logger.add(
        "logs/enhanced_backtest_{time}.log",
        rotation="100 MB",
        retention="7 days",
        level="DEBUG"
    )

async def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description='Run enhanced crypto trading bot backtest with whale tracking')
    parser.add_argument('--symbol', default='BTC/USDT', help='Trading symbol')
    parser.add_argument('--start-date', default='2024-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2024-06-30', help='End date (YYYY-MM-DD)')
    parser.add_argument('--timeframe', default='1h', help='Timeframe (15m, 1h, 4h, 1d)')
    parser.add_argument('--capital', type=float, default=10000, help='Initial capital')
    parser.add_argument('--test-whale', action='store_true', help='Test whale data fetching')
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("🐋 ENHANCED CRYPTO TRADING BOT WITH AI WHALE TRACKING")
    logger.info("=" * 80)
    logger.info(f"Symbol: {args.symbol}")
    logger.info(f"Period: {args.start_date} to {args.end_date}")
    logger.info(f"Timeframe: {args.timeframe}")
    logger.info(f"Initial Capital: ${args.capital:,}")
    logger.info("=" * 80)
    
    # Test whale data fetching if requested
    if args.test_whale:
        logger.info("🧪 Testing whale data fetching...")
        try:
            whale_alerts = await get_multi_chain_whale_data()
            logger.info(f"✅ Successfully fetched {len(whale_alerts)} whale alerts")
            
            for alert in whale_alerts[:5]:  # Show top 5
                tx = alert.transaction
                logger.info(f"  🐋 {tx.chain.value}: ${tx.value_usd:,.2f} - {tx.transaction_type.value}")
                logger.info(f"     AI Analysis: {alert.ai_reasoning[:100]}...")
                
        except Exception as e:
            logger.error(f"❌ Whale data test failed: {e}")
            logger.info("📝 Using simulated whale data for backtest")
    
    try:
        # Validate environment
        required_keys = ['ETHERSCAN_API_KEY', 'OPENAI_API_KEY']
        missing_keys = [key for key in required_keys if not os.getenv(key)]
        
        if missing_keys:
            logger.warning(f"⚠️  Missing API keys: {missing_keys}")
            logger.info("📝 Proceeding with simulated data...")
        else:
            logger.info("✅ All required API keys found")
        
        # Initialize components
        logger.info("🚀 Initializing enhanced backtester and agent...")
        backtester = CryptoBacktester(initial_capital=args.capital)
        agent = BTCETHAgent()
        
        # Run enhanced backtest
        logger.info("📊 Starting enhanced backtest with whale tracking...")
        start_time = datetime.now()
        
        result = await backtester.run_enhanced_backtest(
            agent=agent,
            symbol=args.symbol,
            start_date=args.start_date,
            end_date=args.end_date,
            timeframe=args.timeframe
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Display results
        logger.info("=" * 80)
        logger.info("📈 ENHANCED BACKTEST RESULTS WITH WHALE TRACKING")
        logger.info("=" * 80)
        logger.info(f"💰 Total Return: {result.total_return:.2%}")
        logger.info(f"📅 Annualized Return: {result.annualized_return:.2%}")
        logger.info(f"📉 Max Drawdown: {result.max_drawdown:.2%}")
        logger.info(f"⚡ Sharpe Ratio: {result.sharpe_ratio:.2f}")
        logger.info(f"🎯 Win Rate: {result.win_rate:.1%}")
        logger.info(f"🔢 Total Trades: {result.total_trades}")
        logger.info(f"💵 Final Portfolio Value: ${result.final_capital:,.2f}")
        logger.info(f"⏱️  Backtest Duration: {duration}")
        logger.info("=" * 80)
        
        # Save results
        os.makedirs("results", exist_ok=True)
        
        # Plot results
        backtester.plot_results(result)
        
        # Save detailed data
        if result.total_trades > 0:
            import pandas as pd
            
            trades_df = pd.DataFrame(result.trades)
            equity_df = pd.DataFrame({
                'timestamp': result.timestamps,
                'portfolio_value': result.equity_curve
            })
            
            symbol_clean = args.symbol.replace('/', '_')
            trades_df.to_csv(f"results/enhanced_trades_{symbol_clean}_{args.start_date}.csv", index=False)
            equity_df.to_csv(f"results/enhanced_equity_{symbol_clean}_{args.start_date}.csv", index=False)
            
            logger.success("💾 Enhanced results saved to CSV files")
        
        # Performance assessment with whale considerations
        if result.total_return > 0.15:  # >15% return
            logger.success("🎉 HIGHLY PROFITABLE WHALE-ENHANCED STRATEGY!")
        elif result.total_return > 0.05:  # >5% return  
            logger.info("📈 Profitable whale-enhanced strategy")
        else:
            logger.warning("📉 Strategy needs optimization - check whale signals")
            
        logger.success("✅ Enhanced backtest with whale tracking completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Enhanced backtest failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
