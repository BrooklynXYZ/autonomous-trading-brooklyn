# =============================================================================
# SENTIMENT ANALYSIS MODULE
# =============================================================================

import asyncio
import aiohttp
import tweepy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
import re
from loguru import logger

from ..utils.config_loader import config
from .types import SentimentEvent, SentimentLabel, DataBuffer

class CryptoSentimentAnalyzer:
    """
    Multi-source sentiment analysis for cryptocurrency trading
    Supports Twitter, news sentiment, and social media engagement weighting
    """

    def __init__(self):
        self.config = config
        self.sentiment_buffers: Dict[str, DataBuffer] = {}

        # Sentiment analyzers
        self.vader = SentimentIntensityAnalyzer()

        # Initialize Twitter client
        self._setup_twitter()

        # Crypto-specific keywords
        self.crypto_keywords = {
            'BTC': ['bitcoin', 'btc', '$btc', '#bitcoin', '#btc', 'satoshi'],
            'ETH': ['ethereum', 'eth', '$eth', '#ethereum', '#eth', 'vitalik'],
            'crypto_general': ['crypto', 'cryptocurrency', 'blockchain', 
                             'defi', 'nft', 'web3', 'hodl', 'moon', 'dump', 'pump']
        }

        # Sentiment weight factors
        self.weight_factors = {
            'follower_weight': 0.3,
            'engagement_weight': 0.4,
            'recency_weight': 0.3
        }

        logger.info("Sentiment analyzer initialized")

    def _setup_twitter(self):
        """Setup Twitter API client"""
        try:
            if self.config.twitter_bearer_token:
                self.twitter_client = tweepy.Client(
                    bearer_token=self.config.twitter_bearer_token,
                    wait_on_rate_limit=True
                )
                logger.success("Twitter client initialized")
            else:
                logger.warning("Twitter Bearer token not found")
                self.twitter_client = None
        except Exception as e:
            logger.error(f"Twitter setup failed: {e}")
            self.twitter_client = None

    async def get_crypto_sentiment(self, symbol: str, hours_back: int = 1) -> Dict[str, float]:
        """
        Get comprehensive sentiment analysis for a cryptocurrency
        """
        logger.info(f"Analyzing sentiment for {symbol} (last {hours_back} hours)")

        # Get Twitter sentiment
        twitter_sentiment = await self.get_twitter_sentiment(symbol, hours_back)

        # Get news sentiment (placeholder for news API integration)
        news_sentiment = self._get_news_sentiment(symbol, hours_back)

        # Combine sentiments with weights
        combined_sentiment = self._combine_sentiment_scores(
            twitter_sentiment, news_sentiment
        )

        logger.info(f"Combined sentiment for {symbol}: {combined_sentiment['score']:.3f}")
        return combined_sentiment

    async def get_twitter_sentiment(self, symbol: str, hours_back: int = 1) -> Dict[str, Any]:
        """
        Analyze Twitter sentiment for a cryptocurrency
        """
        if not self.twitter_client:
            logger.warning("Twitter client not available")
            return self._get_neutral_sentiment()

        try:
            # Get keywords for this symbol
            keywords = self.crypto_keywords.get(symbol.split('/')[0], 
                                              self.crypto_keywords['crypto_general'])

            # Build search query
            query = ' OR '.join(keywords)
            query += ' -is:retweet lang:en'  # Exclude retweets, English only

            # Calculate time range
            start_time = datetime.utcnow() - timedelta(hours=hours_back)

            # Fetch tweets
            tweets = tweepy.Paginator(
                self.twitter_client.search_recent_tweets,
                query=query,
                tweet_fields=['public_metrics', 'created_at', 'author_id'],
                user_fields=['public_metrics'],
                expansions=['author_id'],
                start_time=start_time,
                max_results=100
            ).flatten(limit=500)  # Limit for rate limiting

            # Process tweets
            tweet_data = []
            tweet_list = list(tweets)

            if len(tweet_list) == 0:
                logger.warning(f"No tweets found for {symbol}")
                return self._get_neutral_sentiment()

            # Get user data
            users_data = {}
            if hasattr(tweets, 'includes') and 'users' in tweets.includes:
                for user in tweets.includes['users']:
                    users_data[user.id] = user

            for tweet in tweet_list:
                try:
                    # Get user metrics
                    user_followers = 0
                    if tweet.author_id in users_data:
                        user_followers = users_data[tweet.author_id].public_metrics['followers_count']

                    # Analyze sentiment
                    sentiment_scores = self._analyze_tweet_sentiment(tweet.text)

                    # Calculate engagement score
                    engagement = (
                        tweet.public_metrics['like_count'] + 
                        tweet.public_metrics['retweet_count'] + 
                        tweet.public_metrics['reply_count']
                    )

                    tweet_data.append({
                        'text': tweet.text,
                        'sentiment_score': sentiment_scores['compound'],
                        'sentiment_label': sentiment_scores['label'],
                        'confidence': abs(sentiment_scores['compound']),
                        'engagement': engagement,
                        'followers': user_followers,
                        'timestamp': tweet.created_at
                    })

                except Exception as e:
                    logger.warning(f"Error processing tweet: {e}")
                    continue

            if not tweet_data:
                return self._get_neutral_sentiment()

            # Calculate weighted sentiment
            weighted_sentiment = self._calculate_weighted_sentiment(tweet_data)

            return {
                'sentiment_score': weighted_sentiment['score'],
                'confidence': weighted_sentiment['confidence'],
                'sentiment_label': weighted_sentiment['label'],
                'tweet_count': len(tweet_data),
                'total_engagement': sum(t['engagement'] for t in tweet_data),
                'avg_followers': np.mean([t['followers'] for t in tweet_data])
            }

        except Exception as e:
            logger.error(f"Twitter sentiment analysis failed: {e}")
            return self._get_neutral_sentiment()

    def _analyze_tweet_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of individual tweet using multiple methods
        """
        # Clean text
        cleaned_text = self._clean_tweet_text(text)

        # VADER sentiment (better for social media)
        vader_scores = self.vader.polarity_scores(cleaned_text)

        # TextBlob sentiment
        blob = TextBlob(cleaned_text)
        textblob_score = blob.sentiment.polarity

        # Combine scores (VADER weighted higher for social media)
        combined_score = 0.7 * vader_scores['compound'] + 0.3 * textblob_score

        # Determine label
        if combined_score > 0.1:
            label = SentimentLabel.BULLISH
        elif combined_score < -0.1:
            label = SentimentLabel.BEARISH
        else:
            label = SentimentLabel.NEUTRAL

        return {
            'compound': combined_score,
            'label': label,
            'vader_scores': vader_scores,
            'textblob_score': textblob_score
        }

    def _clean_tweet_text(self, text: str) -> str:
        """Clean tweet text for sentiment analysis"""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)

        # Remove user mentions and hashtags symbols (keep the text)
        text = re.sub(r'[@#]', '', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def _calculate_weighted_sentiment(self, tweet_data: List[Dict]) -> Dict[str, Any]:
        """
        Calculate weighted sentiment based on engagement and follower count
        """
        if not tweet_data:
            return {'score': 0.0, 'confidence': 0.0, 'label': SentimentLabel.NEUTRAL}

        total_weight = 0
        weighted_score = 0
        confidence_scores = []

        # Calculate max values for normalization
        max_engagement = max(t['engagement'] for t in tweet_data) or 1
        max_followers = max(t['followers'] for t in tweet_data) or 1

        for tweet in tweet_data:
            # Calculate weights
            engagement_weight = np.log1p(tweet['engagement']) / np.log1p(max_engagement)
            follower_weight = np.log1p(tweet['followers']) / np.log1p(max_followers)

            # Time decay (more recent tweets weighted higher)
            hours_old = (datetime.utcnow() - tweet['timestamp']).total_seconds() / 3600
            time_weight = np.exp(-hours_old / 24)  # Decay over 24 hours

            # Combined weight
            weight = (
                self.weight_factors['engagement_weight'] * engagement_weight +
                self.weight_factors['follower_weight'] * follower_weight +
                self.weight_factors['recency_weight'] * time_weight
            )

            weighted_score += tweet['sentiment_score'] * weight
            total_weight += weight
            confidence_scores.append(tweet['confidence'])

        if total_weight == 0:
            return {'score': 0.0, 'confidence': 0.0, 'label': SentimentLabel.NEUTRAL}

        final_score = weighted_score / total_weight
        avg_confidence = np.mean(confidence_scores)

        # Determine label
        if final_score > 0.1:
            label = SentimentLabel.BULLISH
        elif final_score < -0.1:
            label = SentimentLabel.BEARISH
        else:
            label = SentimentLabel.NEUTRAL

        return {
            'score': final_score,
            'confidence': avg_confidence,
            'label': label
        }

    def _get_news_sentiment(self, symbol: str, hours_back: int) -> Dict[str, Any]:
        """
        Get news sentiment (placeholder - can integrate with news APIs)
        """
        # This is a placeholder for news sentiment analysis
        # You can integrate with NewsAPI, CoinTelegraph, etc.
        return {
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'article_count': 0,
            'label': SentimentLabel.NEUTRAL
        }

    def _combine_sentiment_scores(self, twitter: Dict, news: Dict) -> Dict[str, Any]:
        """
        Combine multiple sentiment sources with appropriate weights
        """
        # Weight Twitter higher as it's more real-time
        twitter_weight = 0.8
        news_weight = 0.2

        combined_score = (
            twitter_weight * twitter['sentiment_score'] +
            news_weight * news['sentiment_score']
        )

        combined_confidence = (
            twitter_weight * twitter['confidence'] +
            news_weight * news['confidence']
        )

        # Determine label
        if combined_score > 0.1:
            label = SentimentLabel.BULLISH
        elif combined_score < -0.1:
            label = SentimentLabel.BEARISH
        else:
            label = SentimentLabel.NEUTRAL

        return {
            'score': combined_score,
            'confidence': combined_confidence,
            'label': label,
            'twitter_metrics': twitter,
            'news_metrics': news
        }

    def _get_neutral_sentiment(self) -> Dict[str, Any]:
        """Return neutral sentiment when analysis fails"""
        return {
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'sentiment_label': SentimentLabel.NEUTRAL,
            'tweet_count': 0,
            'total_engagement': 0,
            'avg_followers': 0
        }

# Global sentiment analyzer instance
sentiment_analyzer = CryptoSentimentAnalyzer()
