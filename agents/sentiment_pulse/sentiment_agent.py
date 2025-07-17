import asyncio
import grpc
from concurrent import futures
import logging
from typing import List, Dict, Optional
import time
import json
from datetime import datetime, timedelta
import numpy as np

import trading_agents_pb2
import trading_agents_pb2_grpc
from .scrapers.reddit_scraper import RedditScraper
from .scrapers.twitter_scraper import TwitterScraper
from .scrapers.telegram_scraper import TelegramScraper
from .sentiment_model import SentimentModel
from .config import SentimentPulseConfig

class SentimentPulseAgent(trading_agents_pb2_grpc.SentimentPulseServiceServicer):
    def __init__(self, config: SentimentPulseConfig):
        self.config = config
        self.reddit_scraper = RedditScraper(config.reddit_config)
        self.twitter_scraper = TwitterScraper(config.twitter_config)
        self.telegram_scraper = TelegramScraper(config.telegram_config)
        self.sentiment_model = SentimentModel(config.model_config)
        
        self.logger = logging.getLogger(__name__)
        self.sentiment_cache: Dict[str, Dict] = {}
        
        # Start background tasks
        self.running = True
        asyncio.create_task(self.continuous_sentiment_monitoring())
    
    async def continuous_sentiment_monitoring(self):
        """Continuously monitor sentiment across platforms"""
        while self.running:
            try:
                # Get trending tokens to monitor
                trending_tokens = await self._get_trending_tokens()
                
                for token in trending_tokens:
                    # Scrape sentiment data
                    sentiment_data = await self._collect_sentiment_data(token)
                    
                    # Update cache
                    self.sentiment_cache[token] = {
                        'data': sentiment_data,
                        'timestamp': int(time.time())
                    }
                
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in continuous sentiment monitoring: {e}")
                await asyncio.sleep(60)
    
    async def _get_trending_tokens(self) -> List[str]:
        """Get list of trending tokens to monitor"""
        # This would typically come from the Coin Scout agent
        # For now, return a static list
        return ['BTC', 'ETH', 'SOL', 'DOGE', 'PEPE', 'SHIB']
    
    async def _collect_sentiment_data(self, token: str) -> Dict:
        """Collect sentiment data from all sources"""
        try:
            # Collect from all sources concurrently
            reddit_task = self.reddit_scraper.get_sentiment(token)
            twitter_task = self.twitter_scraper.get_sentiment(token)
            telegram_task = self.telegram_scraper.get_sentiment(token)
            
            reddit_data, twitter_data, telegram_data = await asyncio.gather(
                reddit_task, twitter_task, telegram_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(reddit_data, Exception):
                self.logger.error(f"Reddit scraping error: {reddit_data}")
                reddit_data = {'sentiment': 0.0, 'mentions': 0}
            
            if isinstance(twitter_data, Exception):
                self.logger.error(f"Twitter scraping error: {twitter_data}")
                twitter_data = {'sentiment': 0.0, 'mentions': 0}
            
            if isinstance(telegram_data, Exception):
                self.logger.error(f"Telegram scraping error: {telegram_data}")
                telegram_data = {'sentiment': 0.0, 'mentions': 0}
            
            return {
                'reddit': reddit_data,
                'twitter': twitter_data,
                'telegram': telegram_data,
                'timestamp': int(time.time())
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting sentiment data: {e}")
            return {
                'reddit': {'sentiment': 0.0, 'mentions': 0},
                'twitter': {'sentiment': 0.0, 'mentions': 0},
                'telegram': {'sentiment': 0.0, 'mentions': 0},
                'timestamp': int(time.time())
            }
    
    async def GetSentimentSignal(self, request, context):
        """Get sentiment signal for a token"""
        try:
            token = request.symbol
            time_window = request.time_window_hours
            
            # Check cache first
            if token in self.sentiment_cache:
                cached_data = self.sentiment_cache[token]
                current_time = int(time.time())
                
                # Use cached data if it's fresh (within 15 minutes)
                if current_time - cached_data['timestamp'] < 900:
                    sentiment_data = cached_data['data']
                else:
                    # Refresh data
                    sentiment_data = await self._collect_sentiment_data(token)
                    self.sentiment_cache[token] = {
                        'data': sentiment_data,
                        'timestamp': current_time
                    }
            else:
                # Collect fresh data
                sentiment_data = await self._collect_sentiment_data(token)
                self.sentiment_cache[token] = {
                    'data': sentiment_data,
                    'timestamp': int(time.time())
                }
            
            # Calculate combined sentiment
            combined_sentiment = self._calculate_combined_sentiment(sentiment_data)
            
            # Create response
            sources = [
                trading_agents_pb2.SentimentSource(
                    platform="reddit",
                    score=sentiment_data['reddit']['sentiment'],
                    count=sentiment_data['reddit']['mentions']
                ),
                trading_agents_pb2.SentimentSource(
                    platform="twitter",
                    score=sentiment_data['twitter']['sentiment'],
                    count=sentiment_data['twitter']['mentions']
                ),
                trading_agents_pb2.SentimentSource(
                    platform="telegram",
                    score=sentiment_data['telegram']['sentiment'],
                    count=sentiment_data['telegram']['mentions']
                )
            ]
            
            return trading_agents_pb2.SentimentResponse(
                symbol=token,
                sentiment_score=combined_sentiment['score'],
                confidence=combined_sentiment['confidence'],
                mentions_count=combined_sentiment['total_mentions'],
                sources=sources
            )
            
        except Exception as e:
            self.logger.error(f"Error getting sentiment signal: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return trading_agents_pb2.SentimentResponse()
    
    def _calculate_combined_sentiment(self, sentiment_data: Dict) -> Dict:
        """Calculate combined sentiment from all sources"""
        try:
            # Weight different sources
            weights = {
                'reddit': 0.4,
                'twitter': 0.4,
                'telegram': 0.2
            }
            
            weighted_sentiment = 0.0
            total_mentions = 0
            total_weight = 0.0
            
            for platform, weight in weights.items():
                if platform in sentiment_data:
                    mentions = sentiment_data[platform]['mentions']
                    sentiment = sentiment_data[platform]['sentiment']
                    
                    # Weight by mentions count (more mentions = more weight)
                    mention_weight = min(mentions / 100, 1.0)  # Cap at 100 mentions
                    final_weight = weight * mention_weight
                    
                    weighted_sentiment += sentiment * final_weight
                    total_mentions += mentions
                    total_weight += final_weight
            
            # Normalize
            if total_weight > 0:
                final_sentiment = weighted_sentiment / total_weight
            else:
                final_sentiment = 0.0
            
            # Calculate confidence based on total mentions and consistency
            confidence = min(total_mentions / 50, 1.0)  # Higher mentions = higher confidence
            
            return {
                'score': final_sentiment,
                'confidence': confidence,
                'total_mentions': total_mentions
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating combined sentiment: {e}")
            return {
                'score': 0.0,
                'confidence': 0.0,
                'total_mentions': 0
            }

def serve():
    config = SentimentPulseConfig.load_from_file('config/agents/sentiment_pulse.yaml')
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    
    sentiment_agent = SentimentPulseAgent(config)
    trading_agents_pb2_grpc.add_SentimentPulseServiceServicer_to_server(
        sentiment_agent, server
    )
    
    listen_addr = f'[::]:{config.grpc_port}'
    server.add_insecure_port(listen_addr)
    
    logging.info(f"Sentiment Pulse Agent starting on {listen_addr}")
    return server

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    server = serve()
    
    async def run_server():
        await server.start()
        await server.wait_for_termination()
    
    asyncio.run(run_server())
