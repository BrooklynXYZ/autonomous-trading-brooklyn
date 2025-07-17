import asyncio
import aiohttp
import logging
from typing import Dict, List
import time
import json
import praw
from datetime import datetime, timedelta
import re

class RedditScraper:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Reddit API client
        self.reddit = praw.Reddit(
            client_id=config.client_id,
            client_secret=config.client_secret,
            user_agent=config.user_agent,
            username=config.username,
            password=config.password
        )
        
        # Crypto-related subreddits
        self.crypto_subreddits = [
            'CryptoCurrency',
            'Bitcoin',
            'ethereum',
            'SatoshiStreetBets',
            'CryptoMoonShots',
            'CryptoMarkets',
            'altcoin',
            'defi'
        ]
    
    async def get_sentiment(self, token: str) -> Dict:
        """Get sentiment for a token from Reddit"""
        try:
            posts = await self._search_token_posts(token)
            comments = await self._search_token_comments(token)
            
            # Combine posts and comments
            all_text = posts + comments
            
            if not all_text:
                return {'sentiment': 0.0, 'mentions': 0}
            
            # Analyze sentiment
            sentiment_score = await self._analyze_sentiment(all_text)
            
            return {
                'sentiment': sentiment_score,
                'mentions': len(all_text),
                'platform': 'reddit'
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Reddit sentiment: {e}")
            return {'sentiment': 0.0, 'mentions': 0}
    
    async def _search_token_posts(self, token: str) -> List[str]:
        """Search for posts mentioning the token"""
        try:
            posts = []
            search_terms = [token, f"${token}", f"#{token}"]
            
            for subreddit_name in self.crypto_subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    for term in search_terms:
                        # Search recent posts
                        for submission in subreddit.search(term, time_filter='day', limit=20):
                            # Check if post is recent (last 24 hours)
                            post_time = datetime.fromtimestamp(submission.created_utc)
                            if (datetime.now() - post_time).days < 1:
                                post_text = f"{submission.title} {submission.selftext}"
                                posts.append(post_text)
                            
                            if len(posts) >= 100:  # Limit to avoid rate limits
                                break
                        
                        if len(posts) >= 100:
                            break
                    
                    if len(posts) >= 100:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error searching {subreddit_name}: {e}")
                    continue
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Error searching token posts: {e}")
            return []
    
    async def _search_token_comments(self, token: str) -> List[str]:
        """Search for comments mentioning the token"""
        try:
            comments = []
            search_terms = [token, f"${token}", f"#{token}"]
            
            for subreddit_name in self.crypto_subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Get hot posts and search their comments
                    for submission in subreddit.hot(limit=10):
                        submission.comments.replace_more(limit=0)
                        
                        for comment in submission.comments:
                            comment_text = comment.body.lower()
                            
                            # Check if comment mentions the token
                            for term in search_terms:
                                if term.lower() in comment_text:
                                    comments.append(comment.body)
                                    break
                            
                            if len(comments) >= 100:
                                break
                        
                        if len(comments) >= 100:
                            break
                    
                    if len(comments) >= 100:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"Error searching comments in {subreddit_name}: {e}")
                    continue
            
            return comments
            
        except Exception as e:
            self.logger.error(f"Error searching token comments: {e}")
            return []
    
    async def _analyze_sentiment(self, texts: List[str]) -> float:
        """Analyze sentiment of text list"""
        try:
            from textblob import TextBlob
            
            if not texts:
                return 0.0
            
            total_sentiment = 0.0
            valid_texts = 0
            
            for text in texts:
                try:
                    # Clean text
                    cleaned_text = self._clean_text(text)
                    
                    if len(cleaned_text) < 10:  # Skip very short texts
                        continue
                    
                    # Analyze sentiment
                    blob = TextBlob(cleaned_text)
                    sentiment = blob.sentiment.polarity
                    
                    total_sentiment += sentiment
                    valid_texts += 1
                    
                except Exception as e:
                    continue
            
            if valid_texts == 0:
                return 0.0
            
            average_sentiment = total_sentiment / valid_texts
            return average_sentiment
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {e}")
            return 0.0
    
    def _clean_text(self, text: str) -> str:
        """Clean text for sentiment analysis"""
        try:
            # Remove URLs
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
            
            # Remove special characters but keep emoticons
            text = re.sub(r'[^\w\s\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', ' ', text)
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error cleaning text: {e}")
            return text
