import asyncio
import logging
import signal
import sys
from concurrent.futures import ThreadPoolExecutor
import grpc
from typing import List, Dict
import time
import json

# Import all agents
from agents.coin_scout.coin_scout_agent import CoinScoutAgent
from agents.sentiment_pulse.sentiment_agent import SentimentPulseAgent
from agents.technical_edge.technical_agent import TechnicalEdgeAgent
from agents.trade_brain.trade_brain_agent import TradeBrainAgent

# Import feature store
from feature_store.feature_store import FeatureStore

# Import configs
from agents.coin_scout.config import CoinScoutConfig
from agents.sentiment_pulse.config import SentimentPulseConfig
from agents.technical_edge.config import TechnicalEdgeConfig
from agents.trade_brain.config import TradeBrainConfig

class MultiAgentOrchestrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agents = {}
        self.servers = {}
        self.feature_store = FeatureStore()
        self.running = False
        
    async def start_all_agents(self):
        """Start all agents"""
        try:
            self.logger.info("Starting Multi-Agent Trading System...")
            
            # Load configurations
            coin_scout_config = CoinScoutConfig.load_from_file('config/agents/coin_scout.yaml')
            sentiment_config = SentimentPulseConfig.load_from_file('config/agents/sentiment_pulse.yaml')
            technical_config = TechnicalEdgeConfig.load_from_file('config/agents/technical_edge.yaml')
            trade_brain_config = TradeBrainConfig.load_from_file('config/agents/trade_brain.yaml')
            
            # Start Coin Scout Agent
            await self._start_coin_scout(coin_scout_config)
            
            # Start Sentiment Pulse Agent
            await self._start_sentiment_pulse(sentiment_config)
            
            # Start Technical Edge Agent
            await self._start_technical_edge(technical_config)
            
            # Start Trade Brain Agent
            await self._start_trade_brain(trade_brain_config)
            
            # Start data pipeline
            await self._start_data_pipeline()
            
            self.running = True
            self.logger.info("All agents started successfully!")
            
        except Exception as e:
            self.logger.error(f"Error starting agents: {e}")
            raise
    
    async def _start_coin_scout(self, config: CoinScoutConfig):
        """Start Coin Scout Agent"""
        try:
            server = grpc.aio.server(ThreadPoolExecutor(max_workers=10))
            
            coin_scout_agent = CoinScoutAgent(config)
            self.agents['coin_scout'] = coin_scout_agent
            
            # Add to gRPC server
            import trading_agents_pb2_grpc
            trading_agents_pb2_grpc.add_CoinScoutServiceServicer_to_server(
                coin_scout_agent, server
            )
            
            listen_addr = f'[::]:{config.grpc_port}'
            server.add_insecure_port(listen_addr)
            
            await server.start()
            self.servers['coin_scout'] = server
            
            self.logger.info(f"Coin Scout Agent started on {listen_addr}")
            
        except Exception as e:
            self.logger.error(f"Error starting Coin Scout Agent: {e}")
            raise
    
    async def _start_sentiment_pulse(self, config: SentimentPulseConfig):
        """Start Sentiment Pulse Agent"""
        try:
            server = grpc.aio.server(ThreadPoolExecutor(max_workers=10))
            
            sentiment_agent = SentimentPulseAgent(config)
            self.agents['sentiment_pulse'] = sentiment_agent
            
            # Add to gRPC server
            import trading_agents_pb2_grpc
            trading_agents_pb2_grpc.add_SentimentPulseServiceServicer_to_server(
                sentiment_agent, server
            )
            
            listen_addr = f'[::]:{config.grpc_port}'
            server.add_insecure_port(listen_addr)
            
            await server.start()
            self.servers['sentiment_pulse'] = server
            
            self.logger.info(f"Sentiment Pulse Agent started on {listen_addr}")
            
        except Exception as e:
            self.logger.error(f"Error starting Sentiment Pulse Agent: {e}")
            raise
    
    async def _start_technical_edge(self, config: TechnicalEdgeConfig):
        """Start Technical Edge Agent"""
        try:
            server = grpc.aio.server(ThreadPoolExecutor(max_workers=10))
            
            technical_agent = TechnicalEdgeAgent(config)
            self.agents['technical_edge'] = technical_agent
            
            # Add to gRPC server
            import trading_agents_pb2_grpc
            trading_agents_pb2_grpc.add_TechnicalEdgeServiceServicer_to_server(
                technical_agent, server
            )
            
            listen_addr = f'[::]:{config.grpc_port}'
            server.add_insecure_port(listen_addr)
            
            await server.start()
            self.servers['technical_edge'] = server
            
            self.logger.info(f"Technical Edge Agent started on {listen_addr}")
            
        except Exception as e:
            self.logger.error(f"Error starting Technical Edge Agent: {e}")
            raise
    
    async def _start_trade_brain(self, config: TradeBrainConfig):
        """Start Trade Brain Agent"""
        try:
            server = grpc.aio.server(ThreadPoolExecutor(max_workers=10))
            
            trade_brain_agent = TradeBrainAgent(config)
            self.agents['trade_brain'] = trade_brain_agent
            
            # Add to gRPC server
            import trading_agents_pb2_grpc
            trading_agents_pb2_grpc.add_TradeBrainServiceServicer_to_server(
                trade_brain_agent, server
            )
            
            listen_addr = f'[::]:{config.grpc_port}'
            server.add_insecure_port(listen_addr)
            
            await server.start()
            self.servers['trade_brain'] = server
            
            self.logger.info(f"Trade Brain Agent started on {listen_addr}")
            
        except Exception as e:
            self.logger.error(f"Error starting Trade Brain Agent: {e}")
            raise
    
    async def _start_data_pipeline(self):
        """Start data pipeline for feature collection"""
        try:
            # This would typically start Apache Airflow or similar
            # For now, we'll start a simple background task
            asyncio.create_task(self._data_collection_loop())
            
            self.logger.info("Data pipeline started")
            
        except Exception as e:
            self.logger.error(f"Error starting data pipeline: {e}")
            raise
    
    async def _data_collection_loop(self):
        """Background task for data collection and feature creation"""
        while self.running:
            try:
                # Get new pairs from Coin Scout
                if 'coin_scout' in self.agents:
                    coin_scout = self.agents['coin_scout']
                    
                    # This would be replaced with actual gRPC calls
                    # For now, we'll simulate the data flow
                    await self._collect_and_store_features()
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in data collection loop: {e}")
                await asyncio.sleep(60)
    
    async def _collect_and_store_features(self):
        """Collect and store features from all agents"""
        try:
            # Get list of tokens to monitor
            monitored_tokens = ['BTC', 'ETH', 'SOL']  # This would come from Coin Scout
            
            for token in monitored_tokens:
                # Collect features from all agents
                # This would be done via gRPC calls in production
                
                # For now, simulate feature collection
                await self._simulate_feature_collection(token)
            
        except Exception as e:
            self.logger.error(f"Error collecting features: {e}")
    
    async def _simulate_feature_collection(self, token: str):
        """Simulate feature collection for a token"""
        try:
            # This would be replaced with actual gRPC calls to agents
            # For now, create mock features
            from feature_store.schemas import TokenFeatures, SentimentFeatures, TechnicalFeatures
            from datetime import datetime
            
            # Mock token features
            token_features = TokenFeatures(
                timestamp=datetime.now(),
                price=50000.0,
                volume_24h=1000000.0,
                liquidity=5000000.0,
                market_cap=1000000000.0,
                holder_count=1000000,
                transaction_count=50000
            )
            
            # Mock sentiment features
            sentiment_features = SentimentFeatures(
                timestamp=datetime.now(),
                reddit_sentiment=0.2,
                twitter_sentiment=0.3,
                telegram_sentiment=0.1,
                combined_sentiment=0.2,
                total_mentions=500,
                sentiment_confidence=0.7
            )
            
            # Mock technical features
            technical_features = TechnicalFeatures(
                timestamp=datetime.now(),
                sma_20=49000.0,
                sma_50=48000.0,
                rsi=60.0,
                macd=100.0,
                bb_upper=51000.0,
                bb_lower=47000.0,
                volume_ma=800000.0,
                atr=2000.0,
                technical_signal='buy',
                technical_score=0.6
            )
            
            # Store in feature store
            await self.feature_store.store_token_features(token, token_features)
            await self.feature_store.store_sentiment_features(token, sentiment_features)
            await self.feature_store.store_technical_features(token, technical_features)
            
            # Create combined features
            await self.feature_store.create_combined_features(token)
            
            self.logger.debug(f"Collected and stored features for {token}")
            
        except Exception as e:
            self.logger.error(f"Error simulating feature collection: {e}")
    
    async def shutdown(self):
        """Shutdown all agents"""
        try:
            self.logger.info("Shutting down Multi-Agent Trading System...")
            
            self.running = False
            
            # Stop all servers
            for name, server in self.servers.items():
                self.logger.info(f"Stopping {name} server...")
                await server.stop(5)
            
            # Close feature store
            self.feature_store.close()
            
            self.logger.info("All agents stopped successfully!")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    async def run(self):
        """Main run loop"""
        try:
            await self.start_all_agents()
            
            # Wait for shutdown signal
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Error in main run loop: {e}")
        finally:
            await self.shutdown()

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/multi_agent.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

async def main():
    """Main function"""
    setup_logging()
    
    orchestrator = MultiAgentOrchestrator()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        orchestrator.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await orchestrator.run()

if __name__ == '__main__':
    asyncio.run(main())
