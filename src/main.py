import asyncio
import logging
import signal
import sys
from datetime import datetime

from trading.recall_client import RecallClient
from trading.strategy_engine import StrategyEngine
from config.config import config
from utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class TradingBot:
    """Main trading bot orchestrator"""
    
    def __init__(self):
        self.recall_client = RecallClient()
        self.strategy_engine = StrategyEngine(self.recall_client)
        self.running = False
        
    async def start(self):
        """Start the trading bot"""
        
        logger.info("🚀 Starting Recall Network AI Trading Bot")
        logger.info(f"📊 Initial Balance: ${config.INITIAL_BALANCE:,.2f}")
        logger.info(f"⚠️  Max Risk: {config.MAX_PORTFOLIO_RISK:.1%}")
        logger.info(f"📈 Max Position Size: {config.MAX_POSITION_SIZE:.1%}")
        
        self.running = True
        
        # Initial portfolio sync
        logger.info("📋 Syncing initial portfolio state...")
        await self.strategy_engine.portfolio_manager.update_portfolio_state()
        
        # Main trading loop
        try:
            while self.running:
                logger.info("🔄 Starting trading cycle...")
                
                success = await self.strategy_engine.execute_trading_cycle()
                
                if not success:
                    logger.error("❌ Trading cycle failed, waiting before retry...")
                    await asyncio.sleep(30)
                else:
                    logger.info("✅ Trading cycle completed successfully")
                
                # Wait before next cycle
                logger.info(f"⏳ Waiting {config.UPDATE_FREQUENCY} seconds for next cycle...")
                await asyncio.sleep(config.UPDATE_FREQUENCY)
                
        except KeyboardInterrupt:
            logger.info("🛑 Received stop signal, shutting down...")
            await self.stop()
        except Exception as e:
            logger.error(f"💥 Fatal error in main loop: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop the trading bot"""
        
        logger.info("🛑 Stopping trading bot...")
        self.running = False
        
        # Get final portfolio state
        try:
            await self.strategy_engine.portfolio_manager.update_portfolio_state()
            metrics = self.strategy_engine.portfolio_manager.get_portfolio_metrics()
            
            logger.info("📊 Final Performance Summary:")
            logger.info(f"  💰 Final Portfolio Value: ${metrics.get('total_value', 0):,.2f}")
            logger.info(f"  📈 Total Return: {metrics.get('total_return', 0):.2%}")
            logger.info(f"  💵 P&L: ${metrics.get('profit_loss', 0):,.2f}")
            logger.info(f"  🔄 Total Trades: {self.strategy_engine.performance_metrics['total_trades']}")
            
        except Exception as e:
            logger.error(f"Error getting final metrics: {e}")
        
        logger.info("👋 Trading bot stopped successfully")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {sig}, initiating shutdown...")
    sys.exit(0)

async def main():
    """Main entry point"""
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start trading bot
    bot = TradingBot()
    
    try:
        await bot.start()
    except Exception as e:
        logger.error(f"Failed to start trading bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
