import duckdb
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime, timedelta
import asyncio
from .schemas import FeatureSchema, TokenFeatures, SentimentFeatures, TechnicalFeatures

class FeatureStore:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self.logger = logging.getLogger(__name__)
        
        # Initialize tables
        self._create_tables()
        
    def _create_tables(self):
        """Create feature store tables"""
        try:
            # Token features table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS token_features (
                    token_symbol VARCHAR,
                    timestamp TIMESTAMP,
                    price DOUBLE,
                    volume_24h DOUBLE,
                    liquidity DOUBLE,
                    market_cap DOUBLE,
                    holder_count INTEGER,
                    transaction_count INTEGER,
                    PRIMARY KEY (token_symbol, timestamp)
                )
            """)
            
            # Sentiment features table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_features (
                    token_symbol VARCHAR,
                    timestamp TIMESTAMP,
                    reddit_sentiment DOUBLE,
                    twitter_sentiment DOUBLE,
                    telegram_sentiment DOUBLE,
                    combined_sentiment DOUBLE,
                    total_mentions INTEGER,
                    sentiment_confidence DOUBLE,
                    PRIMARY KEY (token_symbol, timestamp)
                )
            """)
            
            # Technical features table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS technical_features (
                    token_symbol VARCHAR,
                    timestamp TIMESTAMP,
                    sma_20 DOUBLE,
                    sma_50 DOUBLE,
                    rsi DOUBLE,
                    macd DOUBLE,
                    bb_upper DOUBLE,
                    bb_lower DOUBLE,
                    volume_ma DOUBLE,
                    atr DOUBLE,
                    technical_signal VARCHAR,
                    technical_score DOUBLE,
                    PRIMARY KEY (token_symbol, timestamp)
                )
            """)
            
            # Combined features table for ML
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS combined_features (
                    token_symbol VARCHAR,
                    timestamp TIMESTAMP,
                    price DOUBLE,
                    volume_24h DOUBLE,
                    sentiment_score DOUBLE,
                    technical_score DOUBLE,
                    rsi DOUBLE,
                    macd DOUBLE,
                    atr DOUBLE,
                    final_signal VARCHAR,
                    confidence DOUBLE,
                    PRIMARY KEY (token_symbol, timestamp)
                )
            """)
            
            self.logger.info("Feature store tables created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            raise
    
    async def store_token_features(self, token_symbol: str, features: TokenFeatures):
        """Store token features"""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO token_features 
                (token_symbol, timestamp, price, volume_24h, liquidity, market_cap, holder_count, transaction_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                token_symbol,
                features.timestamp,
                features.price,
                features.volume_24h,
                features.liquidity,
                features.market_cap,
                features.holder_count,
                features.transaction_count
            ])
            
            self.logger.debug(f"Stored token features for {token_symbol}")
            
        except Exception as e:
            self.logger.error(f"Error storing token features: {e}")
            raise
    
    async def store_sentiment_features(self, token_symbol: str, features: SentimentFeatures):
        """Store sentiment features"""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO sentiment_features 
                (token_symbol, timestamp, reddit_sentiment, twitter_sentiment, telegram_sentiment, 
                 combined_sentiment, total_mentions, sentiment_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                token_symbol,
                features.timestamp,
                features.reddit_sentiment,
                features.twitter_sentiment,
                features.telegram_sentiment,
                features.combined_sentiment,
                features.total_mentions,
                features.sentiment_confidence
            ])
            
            self.logger.debug(f"Stored sentiment features for {token_symbol}")
            
        except Exception as e:
            self.logger.error(f"Error storing sentiment features: {e}")
            raise
    
    async def store_technical_features(self, token_symbol: str, features: TechnicalFeatures):
        """Store technical features"""
        try:
            self.conn.execute("""
                INSERT OR REPLACE INTO technical_features 
                (token_symbol, timestamp, sma_20, sma_50, rsi, macd, bb_upper, bb_lower, 
                 volume_ma, atr, technical_signal, technical_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                token_symbol,
                features.timestamp,
                features.sma_20,
                features.sma_50,
                features.rsi,
                features.macd,
                features.bb_upper,
                features.bb_lower,
                features.volume_ma,
                features.atr,
                features.technical_signal,
                features.technical_score
            ])
            
            self.logger.debug(f"Stored technical features for {token_symbol}")
            
        except Exception as e:
            self.logger.error(f"Error storing technical features: {e}")
            raise
    
    async def get_latest_features(self, token_symbol: str) -> Optional[Dict]:
        """Get latest features for a token"""
        try:
            # Get latest features from all tables
            query = """
                SELECT 
                    cf.token_symbol,
                    cf.timestamp,
                    cf.price,
                    cf.volume_24h,
                    cf.sentiment_score,
                    cf.technical_score,
                    cf.rsi,
                    cf.macd,
                    cf.atr,
                    cf.final_signal,
                    cf.confidence,
                    tf.sma_20,
                    tf.sma_50,
                    tf.bb_upper,
                    tf.bb_lower,
                    sf.reddit_sentiment,
                    sf.twitter_sentiment,
                    sf.telegram_sentiment,
                    sf.total_mentions
                FROM combined_features cf
                LEFT JOIN technical_features tf ON cf.token_symbol = tf.token_symbol 
                    AND cf.timestamp = tf.timestamp
                LEFT JOIN sentiment_features sf ON cf.token_symbol = sf.token_symbol 
                    AND cf.timestamp = sf.timestamp
                WHERE cf.token_symbol = ?
                ORDER BY cf.timestamp DESC
                LIMIT 1
            """
            
            result = self.conn.execute(query, [token_symbol]).fetchone()
            
            if result:
                return {
                    'token_symbol': result[0],
                    'timestamp': result[1],
                    'price': result[2],
                    'volume_24h': result[3],
                    'sentiment_score': result[4],
                    'technical_score': result[5],
                    'rsi': result[6],
                    'macd': result[7],
                    'atr': result[8],
                    'final_signal': result[9],
                    'confidence': result[10],
                    'sma_20': result[11],
                    'sma_50': result[12],
                    'bb_upper': result[13],
                    'bb_lower': result[14],
                    'reddit_sentiment': result[15],
                    'twitter_sentiment': result[16],
                    'telegram_sentiment': result[17],
                    'total_mentions': result[18]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting latest features: {e}")
            return None
    
    async def get_historical_features(self, token_symbol: str, hours: int = 24) -> pd.DataFrame:
        """Get historical features for a token"""
        try:
            query = """
                SELECT *
                FROM combined_features
                WHERE token_symbol = ?
                AND timestamp >= ?
                ORDER BY timestamp ASC
            """
            
            start_time = datetime.now() - timedelta(hours=hours)
            
            result = self.conn.execute(query, [token_symbol, start_time]).fetchdf()
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting historical features: {e}")
            return pd.DataFrame()
    
    async def create_combined_features(self, token_symbol: str):
        """Create combined features for ML model"""
        try:
            # Get latest features from all tables
            token_features = self.conn.execute("""
                SELECT * FROM token_features 
                WHERE token_symbol = ? 
                ORDER BY timestamp DESC LIMIT 1
            """, [token_symbol]).fetchone()
            
            sentiment_features = self.conn.execute("""
                SELECT * FROM sentiment_features 
                WHERE token_symbol = ? 
                ORDER BY timestamp DESC LIMIT 1
            """, [token_symbol]).fetchone()
            
            technical_features = self.conn.execute("""
                SELECT * FROM technical_features 
                WHERE token_symbol = ? 
                ORDER BY timestamp DESC LIMIT 1
            """, [token_symbol]).fetchone()
            
            if not all([token_features, sentiment_features, technical_features]):
                self.logger.warning(f"Missing features for {token_symbol}")
                return
            
            # Calculate final signal and confidence
            final_signal, confidence = self._calculate_final_signal(
                sentiment_features, technical_features
            )
            
            # Store combined features
            self.conn.execute("""
                INSERT OR REPLACE INTO combined_features 
                (token_symbol, timestamp, price, volume_24h, sentiment_score, technical_score, 
                 rsi, macd, atr, final_signal, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                token_symbol,
                datetime.now(),
                token_features[3],  # price
                token_features[4],  # volume_24h
                sentiment_features[4],  # combined_sentiment
                technical_features[11],  # technical_score
                technical_features[4],  # rsi
                technical_features[5],  # macd
                technical_features[9],  # atr
                final_signal,
                confidence
            ])
            
            self.logger.debug(f"Created combined features for {token_symbol}")
            
        except Exception as e:
            self.logger.error(f"Error creating combined features: {e}")
            raise
    
    def _calculate_final_signal(self, sentiment_features, technical_features) -> tuple:
        """Calculate final signal and confidence"""
        try:
            # Weight different signals
            sentiment_weight = 0.4
            technical_weight = 0.6
            
            sentiment_score = sentiment_features[4]  # combined_sentiment
            technical_score = technical_features[11]  # technical_score
            
            # Combine signals
            final_score = (sentiment_score * sentiment_weight + 
                          technical_score * technical_weight)
            
            # Determine signal
            if final_score > 0.3:
                final_signal = 'buy'
            elif final_score < -0.3:
                final_signal = 'sell'
            else:
                final_signal = 'hold'
            
            # Calculate confidence
            confidence = min(abs(final_score), 1.0)
            
            return final_signal, confidence
            
        except Exception as e:
            self.logger.error(f"Error calculating final signal: {e}")
            return 'hold', 0.0
    
    async def get_training_data(self, token_symbols: List[str], days: int = 30) -> pd.DataFrame:
        """Get training data for ML models"""
        try:
            placeholders = ','.join(['?' for _ in token_symbols])
            query = f"""
                SELECT *
                FROM combined_features
                WHERE token_symbol IN ({placeholders})
                AND timestamp >= ?
                ORDER BY timestamp ASC
            """
            
            start_time = datetime.now() - timedelta(days=days)
            params = token_symbols + [start_time]
            
            result = self.conn.execute(query, params).fetchdf()
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting training data: {e}")
            return pd.DataFrame()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
