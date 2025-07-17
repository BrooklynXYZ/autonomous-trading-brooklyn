import asyncio
import aiohttp
import logging
from typing import Dict, List
import time
import json
import tweepy
from datetime import datetime, timedelta
import re

class TwitterScraper:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Twitter API client
        self.client = tweepy.Client(
            bearer_token=config.bearer_token,
            consumer_key=config.consumer_key,
            consumer_secret=config.consumer_secret,
            access_token=config.access_token,
            access_token_secret=config.access_token_secret,
            wait_on_rate_limit=True
        )
        
        # Crypto influencers to monitor
        self.crypto_influencers = [
            'elonmusk',
            'VitalikButerin',
            'cz_binance',
            'brian_armstrong',
            'aantonop',
            'APompliano',
            'naval',
            'balajis'
        ]
    
    async def get_sentiment(self, token: str) -> Dict:
        """Get sentiment for a token from Twitter"""
        try:
            # Search for tweets mentioning the token
            tweets = await self._search_token_tweets(token)
            
            if not tweets:
                return {'sentiment': 0.0, 'mentions': 0}
            
            # Analyze sentiment
            sentiment_score = await self._analyze_sentiment(tweets)
            
            return {
                'sentiment': sentiment_score,
                'mentions': len(tweets),
                'platform': 'twitter'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Twitter sentiment: {e}")
            return {'sentiment': 0.0, 'mentions': 0}
    
    async def _search_token_tweets(self, token: str) -> List[str]:
        """Search for tweets mentioning the token"""
        try:
            tweets = []
            search_terms = [token, f"${token}", f"#{token}"]
            
            for term in search_terms:
                try:
                    # Search recent tweets
                    query = f"{term} -is:retweet lang:en"
                    
                    # Get tweets from the last 24 hours
                    end_time = datetime.now()
                    start_time = end_time - timedelta(days=1)
                    
                    response = self.client.search_recent_tweets(
                        query=query,
                        max_results=100,
                        start_time=start_time,
                        end_time=end_time,
                        tweet_fields=['created_at', 'public_metrics', 'lang']
                    )
                    
                    if response.data:
                        for tweet in response.data:
                            tweets.append(tweet.text)
                    
                    if len(tweets) >= 200:  # Limit to avoid rate limits
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error searching for {term}: {e}")
                    continue
            
            # Also check influencer tweets
            influencer_tweets = await self._get_influencer_tweets(token)
            tweets.extend(influencer_tweets)
            
            return tweets
            
        except Exception as e:
            self.logger.error(f"Error searching token tweets: {e}")
            return []
    
    async def _get_influencer_tweets(self, token: str) -> List[str]:
        """Get tweets from crypto influencers mentioning the token"""
        try:
            tweets = []
            token_lower = token.lower()
            
            for username in self.crypto_influencers:
                try:
                    # Get user's recent tweets
                    user = self.client.get_user(username=username)
                    if not user.data:
                        continue
                    
                    user_tweets = self.client.get_users_tweets(
                        id=user.data.id,
                        max_results=50,
                        tweet_fields=['created_at']
                    )
                    
                    if user_tweets.data:
                        for tweet in user_tweets.data:
                            if token_lower in tweet.text.lower():
                                tweets.append(tweet.text)
                    
                    if len(tweets) >= 50:  # Limit per influencer
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error getting tweets from {username}: {e}")
                    continue
            
            return tweets
            
        except Exception as e:
            self.logger.error(f"Error getting influencer tweets: {e}")
            return []
    
    async def _analyze_sentiment(self, tweets: List[str]) -> float:
        """Analyze sentiment of tweets"""
        try:
            from textblob import TextBlob
            
            if not tweets:
                return 0.0
            
            total_sentiment = 0.0
            valid_tweets = 0
            
            for tweet in tweets:
                try:
                    # Clean tweet
                    cleaned_tweet = self._clean_tweet(tweet)
                    
                    if len(cleaned_tweet) < 10:  # Skip very short tweets
                        continue
                    
                    # Analyze sentiment
                    blob = TextBlob(cleaned_tweet)
                    sentiment = blob.sentiment.polarity
                    
                    total_sentiment += sentiment
                    valid_tweets += 1
                    
                except Exception as e:
                    continue
            
            if valid_tweets == 0:
                return 0.0
            
            average_sentiment = total_sentiment / valid_tweets
            return average_sentiment
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return 0.0
    
    def _clean_tweet(self, tweet: str) -> str:
        """Clean tweet for sentiment analysis"""
        try:
            # Remove URLs
            tweet = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', tweet)
            
            # Remove mentions and hashtags (but keep the content)
            tweet = re.sub(r'@[A-Za-z0-9_]+', '', tweet)
            tweet = re.sub(r'#([A-Za-z0-9_]+)', r'\1', tweet)
            
            # Remove extra whitespace
            tweet = ' '.join(tweet.split())
            
            return tweet
            
        except Exception as e:
            self.logger.error(f"Error cleaning tweet: {e}")
            return tweet
