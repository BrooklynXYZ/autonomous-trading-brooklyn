import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from .base_agent import BaseAgent
from ..data.types import OrderAction, TradeSignal, WhaleAlert, Chain
from ..features.ta import technical_analyzer
from ..data.whale_feed import MultiChainWhaleTracker

class BTCETHAgent(BaseAgent):
    """
    Enhanced BTC/ETH agent with multi-chain whale tracking
    """
    
    def __init__(self):
        # Increased state size to include whale features
        super().__init__(state_size=70, action_size=3)  # Expanded for whale data
        self.symbols = ['BTC/USDT', 'ETH/USDT']
        self.whale_tracker = None
        self.whale_cache = {}
        
        logger.info("Enhanced BTC/ETH Agent with whale tracking initialized")
    
    async def initialize_whale_tracker(self):
        """Initialize the whale tracker"""
        self.whale_tracker = MultiChainWhaleTracker()
        await self.whale_tracker.__aenter__()
    
    def preprocess(self, row):
        """Enhanced preprocessing with whale data"""
        # Original technical features (40 features)
        technical_features = self._extract_technical_features(row)
        
        # Sentiment features (10 features) 
        sentiment_features = self._extract_sentiment_features(row)
        
        # Enhanced whale features (20 features)
        whale_features = self._extract_whale_features(row)
        
        # Combine all features (70 total)
        state = np.concatenate([
            technical_features,      # 40 features
            sentiment_features,      # 10 features  
            whale_features          # 20 features
        ])
        
        return state
    
    def _extract_technical_features(self, row) -> np.ndarray:
        """Extract technical analysis features"""
        features = []
        
        # Basic price features
        features.extend([
            row.get('close', 0),
            row.get('volume', 0),
            row.get('high', 0),
            row.get('low', 0),
            row.get('open', 0)
        ])
        
        # Technical indicators
        features.extend([
            row.get('rsi', 50) / 100,
            row.get('macd', 0),
            row.get('macd_signal', 0),
            row.get('macd_histogram', 0),
            row.get('sma_fast', row.get('close', 0)) / max(row.get('close', 1), 0.001),
            row.get('sma_slow', row.get('close', 0)) / max(row.get('close', 1), 0.001),
            row.get('ema_fast', row.get('close', 0)) / max(row.get('close', 1), 0.001),
            row.get('ema_slow', row.get('close', 0)) / max(row.get('close', 1), 0.001),
            row.get('bb_upper', 0) / max(row.get('close', 1), 0.001),
            row.get('bb_middle', 0) / max(row.get('close', 1), 0.001),
            row.get('bb_lower', 0) / max(row.get('close', 1), 0.001),
            row.get('bb_width', 0),
            row.get('atr', 0) / max(row.get('close', 1), 0.001),
            row.get('stoch_k', 50) / 100,
            row.get('stoch_d', 50) / 100,
            row.get('williams_r', -50) / 100,
            row.get('cci', 0) / 200,
            row.get('roc', 0),
            row.get('mfi', 50) / 100,
            row.get('obv', 0) / 1000000,
            row.get('ad', 0) / 1000000,
            row.get('cmf', 0),
            row.get('vwap', 0) / max(row.get('close', 1), 0.001),
            row.get('pivot', 0) / max(row.get('close', 1), 0.001),
            row.get('r1', 0) / max(row.get('close', 1), 0.001),
            row.get('s1', 0) / max(row.get('close', 1), 0.001),
            row.get('kc_upper', 0) / max(row.get('close', 1), 0.001),
            row.get('kc_lower', 0) / max(row.get('close', 1), 0.001),
            row.get('dc_upper', 0) / max(row.get('close', 1), 0.001),
            row.get('dc_lower', 0) / max(row.get('close', 1), 0.001),
            row.get('price_change', 0),
            row.get('volume_ratio', 1),
            row.get('body_to_range', 0.5),
            row.get('upper_shadow', 0) / max(row.get('close', 1), 0.001),
            row.get('lower_shadow', 0) / max(row.get('close', 1), 0.001),
            min(row.get('gap_percent', 0), 1),
            row.get('total_range', 0) / max(row.get('close', 1), 0.001),
            row.get('typical_price', row.get('close', 0)) / max(row.get('close', 1), 0.001),
            row.get('weighted_close', row.get('close', 0)) / max(row.get('close', 1), 0.001),
            row.get('true_range', 0) / max(row.get('close', 1), 0.001)
        ])
        
        return np.array(features[:40])  # Ensure exactly 40 features
    
    def _extract_sentiment_features(self, row) -> np.ndarray:
        """Extract sentiment features"""
        features = [
            row.get('sentiment', 0),
            row.get('fear_greed_index', 50) / 100,
            row.get('social_volume', 0),
            row.get('twitter_sentiment', 0),
            row.get('news_sentiment', 0),
            row.get('google_trends', 0),
            row.get('reddit_sentiment', 0),
            row.get('telegram_sentiment', 0),
            row.get('discord_sentiment', 0),
            row.get('overall_sentiment_score', 0)
        ]
        
        return np.array(features)
    
    def _extract_whale_features(self, row) -> np.ndarray:
        """Extract enhanced whale tracking features"""
        features = []
        
        # Basic whale flow data
        features.extend([
            row.get('whale_flow', 0) / 1000000,  # Scale to millions
            row.get('whale_inflow', 0) / 1000000,
            row.get('whale_outflow', 0) / 1000000,
            row.get('net_whale_flow', 0) / 1000000
        ])
        
        # Multi-chain whale data
        chain_flows = ['eth', 'btc', 'sol', 'base', 'bsc', 'arb']
        for chain in chain_flows:
            features.append(row.get(f'{chain}_whale_flow', 0) / 1000000)
        
        # Whale transaction metrics
        features.extend([
            min(row.get('whale_tx_count', 0) / 50, 1),  # Normalize
            row.get('avg_whale_tx_size', 0) / 1000000,
            row.get('largest_whale_tx', 0) / 1000000,
            row.get('whale_concentration', 0),  # Gini coefficient
            row.get('new_whale_addresses', 0) / 10,  # Daily new whales
            row.get('active_whale_addresses', 0) / 100,  # Active whales
            row.get('whale_exchange_ratio', 0.5),  # % of whale txs to exchanges
            row.get('whale_accumulation_score', 0),  # AI-derived score
            row.get('whale_distribution_score', 0),  # AI-derived score
            row.get('whale_manipulation_risk', 0)   # AI risk assessment
        ])
        
        return np.array(features[:20])  # Ensure exactly 20 features
    
    async def get_enhanced_market_data(self, symbol: str) -> Dict:
        """Get market data enhanced with real whale tracking"""
        base_data = await self._get_basic_market_data(symbol)
        
        if self.whale_tracker:
            # Determine relevant chains based on symbol
            relevant_chains = self._get_relevant_chains(symbol)
            
            # Get recent whale transactions
            whale_transactions = await self.whale_tracker.get_large_transactions(
                chains=relevant_chains, 
                hours_back=24
            )
            
            # Analyze whale impact
            whale_analysis = await self._analyze_whale_impact(whale_transactions, symbol)
            base_data.update(whale_analysis)
        
        return base_data
    
    def _get_relevant_chains(self, symbol: str) -> List[Chain]:
        """Get relevant chains for a trading symbol"""
        if 'BTC' in symbol:
            return [Chain.ETHEREUM, Chain.BASE, Chain.ARBITRUM]  # BTC on EVM chains
        elif 'ETH' in symbol:
            return [Chain.ETHEREUM, Chain.BASE, Chain.ARBITRUM, Chain.BSC]
        else:
            return [Chain.ETHEREUM, Chain.SOLANA, Chain.BASE, Chain.BSC, Chain.ARBITRUM]
    
    async def _analyze_whale_impact(self, transactions: List, symbol: str) -> Dict:
        """Analyze whale transaction impact using AI"""
        if not transactions:
            return self._get_default_whale_features()
        
        # Calculate aggregate metrics
        total_volume = sum(tx.value_usd for tx in transactions)
        avg_size = total_volume / len(transactions) if transactions else 0
        largest_tx = max((tx.value_usd for tx in transactions), default=0)
        
        # Count by chain
        chain_volumes = {}
        for tx in transactions:
            chain_name = tx.chain.value
            chain_volumes[chain_name] = chain_volumes.get(chain_name, 0) + tx.value_usd
        
        # Analyze transaction types
        exchange_txs = [tx for tx in transactions if 'exchange' in tx.transaction_type.value]
        exchange_ratio = len(exchange_txs) / len(transactions) if transactions else 0
        
        # Calculate net flow
        deposits = sum(tx.value_usd for tx in transactions if tx.transaction_type.value == 'exchange_deposit')
        withdrawals = sum(tx.value_usd for tx in transactions if tx.transaction_type.value == 'exchange_withdrawal')
        net_flow = withdrawals - deposits
        
        return {
            'whale_flow': net_flow,
            'whale_inflow': deposits,
            'whale_outflow': withdrawals,
            'net_whale_flow': net_flow,
            'whale_tx_count': len(transactions),
            'avg_whale_tx_size': avg_size,
            'largest_whale_tx': largest_tx,
            'whale_exchange_ratio': exchange_ratio,
            'eth_whale_flow': chain_volumes.get('ethereum', 0),
            'btc_whale_flow': chain_volumes.get('bitcoin', 0),  # If tracking BTC
            'sol_whale_flow': chain_volumes.get('solana', 0),
            'base_whale_flow': chain_volumes.get('base', 0),
            'bsc_whale_flow': chain_volumes.get('bsc', 0),
            'arb_whale_flow': chain_volumes.get('arbitrum', 0),
            'whale_accumulation_score': self._calculate_accumulation_score(transactions),
            'whale_distribution_score': self._calculate_distribution_score(transactions),
            'whale_manipulation_risk': self._calculate_manipulation_risk(transactions)
        }
    
    def _get_default_whale_features(self) -> Dict:
        """Default whale features when no data available"""
        return {
            'whale_flow': 0, 'whale_inflow': 0, 'whale_outflow': 0, 'net_whale_flow': 0,
            'whale_tx_count': 0, 'avg_whale_tx_size': 0, 'largest_whale_tx': 0,
            'whale_exchange_ratio': 0.5, 'eth_whale_flow': 0, 'btc_whale_flow': 0,
            'sol_whale_flow': 0, 'base_whale_flow': 0, 'bsc_whale_flow': 0,
            'arb_whale_flow': 0, 'whale_accumulation_score': 0,
            'whale_distribution_score': 0, 'whale_manipulation_risk': 0,
            'whale_concentration': 0, 'new_whale_addresses': 0,
            'active_whale_addresses': 0
        }
    
    def _calculate_accumulation_score(self, transactions) -> float:
        """Calculate whale accumulation score based on transaction patterns"""
        if not transactions:
            return 0.0
        
        # More withdrawals from exchanges = accumulation
        withdrawals = [tx for tx in transactions if tx.transaction_type.value == 'exchange_withdrawal']
        deposits = [tx for tx in transactions if tx.transaction_type.value == 'exchange_deposit']
        
        withdrawal_volume = sum(tx.value_usd for tx in withdrawals)
        deposit_volume = sum(tx.value_usd for tx in deposits)
        
        total_volume = withdrawal_volume + deposit_volume
        if total_volume == 0:
            return 0.0
        
        # Score from -1 (full distribution) to +1 (full accumulation)
        return (withdrawal_volume - deposit_volume) / total_volume
    
    def _calculate_distribution_score(self, transactions) -> float:
        """Calculate whale distribution score"""
        return -self._calculate_accumulation_score(transactions)  # Inverse of accumulation
    
    def _calculate_manipulation_risk(self, transactions) -> float:
        """Calculate manipulation risk based on transaction patterns"""
        if not transactions:
            return 0.0
        
        # Factors that increase manipulation risk:
        # 1. Large transactions in short time
        # 2. Coordinated movements across chains
        # 3. Unusual transaction sizes
        
        # Time clustering
        time_window = 3600  # 1 hour
        current_time = datetime.now()
        recent_txs = [
            tx for tx in transactions 
            if (current_time - tx.timestamp).seconds < time_window
        ]
        
        time_clustering_score = len(recent_txs) / len(transactions) if transactions else 0
        
        # Size variance (high variance = manipulation risk)
        sizes = [tx.value_usd for tx in transactions]
        if len(sizes) > 1:
            size_variance = np.var(sizes) / np.mean(sizes) if np.mean(sizes) > 0 else 0
            size_variance_score = min(size_variance / 5, 1)  # Normalize
        else:
            size_variance_score = 0
        
        # Chain coordination (same addresses across chains)
        unique_addresses = set(tx.from_address for tx in transactions)
        address_reuse_score = 1 - (len(unique_addresses) / len(transactions)) if transactions else 0
        
        # Combine factors
        manipulation_risk = (
            time_clustering_score * 0.4 +
            size_variance_score * 0.3 +
            address_reuse_score * 0.3
        )
        
        return min(manipulation_risk, 1.0)
    
    async def _get_basic_market_data(self, symbol: str) -> Dict:
        """Get basic market data (placeholder - implement with real data)"""
        return {
            'close': 50000.0,
            'volume': 1000000,
            'high': 51000.0,
            'low': 49000.0,
            'open': 50500.0
        }

    async def cleanup(self):
        """Cleanup whale tracker connection"""
        if self.whale_tracker:
            await self.whale_tracker.__aexit__(None, None, None)
