import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from loguru import logger
import openai
from dataclasses import asdict

from .types import Chain, WhaleTransaction, WhaleWallet, WhaleAlert, TransactionType

class MultiChainWhaleTracker:
    """
    Unified whale tracker using Etherscan v2 API for EVM chains and Solscan for Solana
    Enhanced with AI analysis via OpenAI
    """
    
    def __init__(self):
        self.etherscan_key = os.getenv('ETHERSCAN_API_KEY')
        self.solscan_key = os.getenv('SOLSCAN_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
        if not self.etherscan_key or not self.solscan_key:
            raise ValueError("Missing required API keys")
        
        # Initialize OpenAI
        openai.api_key = self.openai_key
        
        # Chain configurations using Etherscan v2
        self.chain_configs = {
            Chain.ETHEREUM: {'chain_id': 1, 'name': 'Ethereum Mainnet'},
            Chain.BASE: {'chain_id': 8453, 'name': 'Base Mainnet'},
            Chain.BSC: {'chain_id': 56, 'name': 'BNB Smart Chain'},
            Chain.ARBITRUM: {'chain_id': 42161, 'name': 'Arbitrum One'},
            Chain.SOLANA: {'rpc': 'https://public-api.solscan.io', 'name': 'Solana'}
        }
        
        # Whale thresholds
        self.whale_threshold = float(os.getenv('WHALE_THRESHOLD_MIN', 500000))
        self.large_tx_threshold = float(os.getenv('LARGE_TX_THRESHOLD', 100000))
        
        # Session for async requests
        self.session = None
        
        logger.info("MultiChainWhaleTracker initialized")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_large_transactions(self, chains: List[Chain] = None, 
                                   hours_back: int = 24) -> List[WhaleTransaction]:
        """Get large transactions across multiple chains"""
        if chains is None:
            chains = list(Chain)
        
        all_transactions = []
        
        tasks = []
        for chain in chains:
            if chain == Chain.SOLANA:
                tasks.append(self._get_solana_whale_transactions(hours_back))
            else:
                tasks.append(self._get_evm_whale_transactions(chain, hours_back))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error fetching transactions: {result}")
                continue
            all_transactions.extend(result)
        
        # Sort by value and return top transactions
        all_transactions.sort(key=lambda x: x.value_usd, reverse=True)
        return all_transactions[:100]  # Return top 100

    async def _get_evm_whale_transactions(self, chain: Chain, hours_back: int) -> List[WhaleTransaction]:
        """Get whale transactions for EVM chains using Etherscan v2 API"""
        config = self.chain_configs[chain]
        chain_id = config['chain_id']
        
        # Get latest block
        latest_block = await self._get_latest_block(chain_id)
        if not latest_block:
            return []
        
        # Calculate block range (approximate)
        blocks_per_hour = self._get_blocks_per_hour(chain)
        start_block = max(1, latest_block - (hours_back * blocks_per_hour))
        
        # Get large transactions
        transactions = []
        
        # We'll check recent blocks for large transactions
        for block_num in range(start_block, latest_block + 1, 100):  # Check every 100 blocks
            block_txs = await self._get_block_transactions(chain_id, block_num)
            
            for tx in block_txs:
                if self._is_whale_transaction(tx):
                    whale_tx = await self._parse_evm_transaction(tx, chain)
                    if whale_tx and whale_tx.value_usd >= self.large_tx_threshold:
                        transactions.append(whale_tx)
        
        return transactions

    async def _get_solana_whale_transactions(self, hours_back: int) -> List[WhaleTransaction]:
        """Get whale transactions for Solana using Solscan API"""
        url = "https://public-api.solscan.io/transaction/last"
        params = {
            'limit': 40,  # Max limit for free API
        }
        
        if self.solscan_key:
            headers = {'Authorization': f'Bearer {self.solscan_key}'}
        else:
            headers = {}
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Solscan API error: {response.status}")
                    return []
                
                data = await response.json()
                transactions = []
                
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                
                for tx_data in data.get('data', []):
                    tx_time = datetime.fromtimestamp(tx_data.get('blockTime', 0))
                    if tx_time < cutoff_time:
                        continue
                    
                    # Get detailed transaction info
                    whale_tx = await self._parse_solana_transaction(tx_data)
                    if whale_tx and whale_tx.value_usd >= self.large_tx_threshold:
                        transactions.append(whale_tx)
                
                return transactions
                
        except Exception as e:
            logger.error(f"Error fetching Solana transactions: {e}")
            return []

    async def _get_latest_block(self, chain_id: int) -> Optional[int]:
        """Get latest block number for EVM chain"""
        url = "https://api.etherscan.io/v2/api"
        params = {
            'chainid': chain_id,
            'module': 'proxy',
            'action': 'eth_blockNumber',
            'apikey': self.etherscan_key
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('result'):
                        return int(data['result'], 16)  # Convert from hex
        except Exception as e:
            logger.error(f"Error getting latest block: {e}")
        
        return None

    async def _get_block_transactions(self, chain_id: int, block_num: int) -> List[Dict]:
        """Get transactions from a specific block"""
        url = "https://api.etherscan.io/v2/api"
        params = {
            'chainid': chain_id,
            'module': 'proxy',
            'action': 'eth_getBlockByNumber',
            'tag': hex(block_num),
            'boolean': 'true',
            'apikey': self.etherscan_key
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('result') and data['result'].get('transactions'):
                        return data['result']['transactions']
        except Exception as e:
            logger.error(f"Error getting block transactions: {e}")
        
        return []

    def _get_blocks_per_hour(self, chain: Chain) -> int:
        """Estimate blocks per hour for different chains"""
        blocks_per_hour = {
            Chain.ETHEREUM: 300,    # ~12 second blocks
            Chain.BASE: 1800,       # ~2 second blocks  
            Chain.BSC: 1200,        # ~3 second blocks
            Chain.ARBITRUM: 240,    # ~15 second blocks
        }
        return blocks_per_hour.get(chain, 300)

    def _is_whale_transaction(self, tx: Dict) -> bool:
        """Check if transaction meets whale criteria"""
        try:
            value_wei = int(tx.get('value', '0x0'), 16)
            value_eth = value_wei / 1e18
            
            # Rough USD conversion (you'd want real-time prices)
            eth_price = 3000  # Placeholder
            value_usd = value_eth * eth_price
            
            return value_usd >= self.large_tx_threshold
        except:
            return False

    async def _parse_evm_transaction(self, tx: Dict, chain: Chain) -> Optional[WhaleTransaction]:
        """Parse EVM transaction data into WhaleTransaction"""
        try:
            value_wei = int(tx.get('value', '0x0'), 16)
            value_eth = value_wei / 1e18
            
            # Get USD value (you'd want to fetch real prices)
            eth_price = await self._get_token_price('ethereum')
            value_usd = value_eth * eth_price
            
            block_num = int(tx.get('blockNumber', '0x0'), 16)
            
            # Determine transaction type
            to_addr = tx.get('to', '').lower()
            tx_type = self._classify_transaction_type(to_addr)
            
            return WhaleTransaction(
                chain=chain,
                hash=tx.get('hash', ''),
                from_address=tx.get('from', ''),
                to_address=tx.get('to', ''),
                amount=value_eth,
                value_usd=value_usd,
                token_symbol='ETH',  # Simplified
                token_address=None,
                timestamp=datetime.now(),  # You'd get real timestamp from block
                transaction_type=tx_type,
                block_number=block_num,
                gas_used=int(tx.get('gasUsed', '0x0'), 16) if tx.get('gasUsed') else None
            )
        except Exception as e:
            logger.error(f"Error parsing EVM transaction: {e}")
            return None

    async def _parse_solana_transaction(self, tx_data: Dict) -> Optional[WhaleTransaction]:
        """Parse Solana transaction data"""
        try:
            # Solana transaction parsing is more complex
            # This is a simplified version
            
            signature = tx_data.get('txHash', '')
            
            # Get detailed transaction info
            detailed_tx = await self._get_solana_transaction_details(signature)
            if not detailed_tx:
                return None
            
            # Extract SOL transfers (simplified)
            sol_amount = 0
            sol_price = await self._get_token_price('solana')
            
            # Parse transaction for large transfers
            # This would need more sophisticated parsing
            
            return WhaleTransaction(
                chain=Chain.SOLANA,
                hash=signature,
                from_address='',  # Would extract from transaction
                to_address='',
                amount=sol_amount,
                value_usd=sol_amount * sol_price,
                token_symbol='SOL',
                token_address=None,
                timestamp=datetime.fromtimestamp(tx_data.get('blockTime', 0)),
                transaction_type=TransactionType.TRANSFER,
                block_number=tx_data.get('slot', 0)
            )
        except Exception as e:
            logger.error(f"Error parsing Solana transaction: {e}")
            return None

    async def _get_solana_transaction_details(self, signature: str) -> Optional[Dict]:
        """Get detailed Solana transaction info"""
        url = f"https://public-api.solscan.io/transaction/{signature}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error(f"Error getting Solana transaction details: {e}")
        
        return None

    def _classify_transaction_type(self, to_address: str) -> TransactionType:
        """Classify transaction type based on recipient"""
        # Known exchange addresses (simplified)
        exchange_addresses = {
            '0x28c6c06298d514db089934071355e5743bf21d60',  # Binance 14
            '0xdfd5293d8e347dfe59e90efd55b2956a1343963d',  # Binance 15
            '0x21a31ee1afc51d94c2efccaa2092ad1028285549',  # Binance 16
            # Add more known addresses
        }
        
        if to_address in exchange_addresses:
            return TransactionType.EXCHANGE_DEPOSIT
        
        return TransactionType.TRANSFER

    async def _get_token_price(self, token: str) -> float:
        """Get token price from a price API"""
        # Simplified price fetching
        prices = {
            'ethereum': 3000.0,
            'solana': 100.0,
            'bitcoin': 45000.0
        }
        return prices.get(token, 1.0)

    async def analyze_whale_with_ai(self, whale_transaction: WhaleTransaction) -> WhaleAlert:
        """Analyze whale transaction using OpenAI"""
        try:
            # Prepare context for AI analysis
            context = self._prepare_transaction_context(whale_transaction)
            
            prompt = f"""
            Analyze this large cryptocurrency transaction and provide insights:

            {context}

            Please analyze:
            1. The significance of this transaction size
            2. Potential market impact
            3. Whether this indicates accumulation or distribution
            4. Risk level (1-10)
            5. Recommended action for traders

            Provide a concise analysis in JSON format with fields:
            - significance: string
            - market_impact: string  
            - action_type: "accumulation" | "distribution" | "neutral"
            - risk_score: number (1-10)
            - trader_action: "bullish" | "bearish" | "neutral"
            - reasoning: string
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            ai_analysis = response.choices[0].message.content
            
            try:
                analysis_json = json.loads(ai_analysis)
                confidence = (11 - analysis_json.get('risk_score', 5)) / 10
            except:
                confidence = 0.5
                analysis_json = {'reasoning': ai_analysis}
            
            # Create whale wallet info
            whale_wallet = WhaleWallet(
                address=whale_transaction.from_address,
                chain=whale_transaction.chain,
                balance_usd=whale_transaction.value_usd,  # Simplified
                token_holdings={whale_transaction.token_symbol: whale_transaction.amount},
                transaction_count=1,
                first_seen=whale_transaction.timestamp,
                last_activity=whale_transaction.timestamp,
                ai_analysis=ai_analysis
            )
            
            return WhaleAlert(
                transaction=whale_transaction,
                wallet=whale_wallet,
                alert_type="large_transaction",
                confidence=confidence,
                ai_reasoning=analysis_json.get('reasoning', ai_analysis),
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            
            # Fallback analysis
            whale_wallet = WhaleWallet(
                address=whale_transaction.from_address,
                chain=whale_transaction.chain,
                balance_usd=whale_transaction.value_usd,
                token_holdings={whale_transaction.token_symbol: whale_transaction.amount},
                transaction_count=1,
                first_seen=whale_transaction.timestamp,
                last_activity=whale_transaction.timestamp
            )
            
            return WhaleAlert(
                transaction=whale_transaction,
                wallet=whale_wallet,
                alert_type="large_transaction",
                confidence=0.5,
                ai_reasoning="Large transaction detected - manual review recommended",
                created_at=datetime.now()
            )

    def _prepare_transaction_context(self, tx: WhaleTransaction) -> str:
        """Prepare transaction context for AI analysis"""
        return f"""
        Chain: {tx.chain.value}
        Transaction Hash: {tx.hash}
        Amount: {tx.amount:.4f} {tx.token_symbol}
        USD Value: ${tx.value_usd:,.2f}
        From: {tx.from_address}
        To: {tx.to_address}
        Type: {tx.transaction_type.value}
        Time: {tx.timestamp}
        Block: {tx.block_number}
        """

    async def get_whale_wallets(self, chain: Chain, min_balance_usd: float = None) -> List[WhaleWallet]:
        """Get list of known whale wallets for a chain"""
        if min_balance_usd is None:
            min_balance_usd = self.whale_threshold
        
        # This would implement wallet discovery based on transaction history
        # For now, return empty list
        return []

    async def monitor_continuous(self, chains: List[Chain], callback=None):
        """Continuously monitor for whale transactions"""
        logger.info(f"Starting continuous monitoring for chains: {[c.value for c in chains]}")
        
        while True:
            try:
                transactions = await self.get_large_transactions(chains, hours_back=1)
                
                for tx in transactions:
                    alert = await self.analyze_whale_with_ai(tx)
                    
                    if callback:
                        await callback(alert)
                    else:
                        logger.info(f"Whale Alert: {tx.chain.value} - ${tx.value_usd:,.2f}")
                
                # Wait before next check
                await asyncio.sleep(300)  # 5 minutes
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

# Utility function for easy usage
async def get_multi_chain_whale_data(chains: List[str] = None) -> List[WhaleAlert]:
    """Convenience function to get whale data across chains"""
    if chains is None:
        chains = ['ethereum', 'solana', 'base', 'bsc', 'arbitrum']
    
    chain_enums = [Chain(chain) for chain in chains]
    
    async with MultiChainWhaleTracker() as tracker:
        transactions = await tracker.get_large_transactions(chain_enums)
        
        alerts = []
        for tx in transactions[:20]:  # Limit to top 20
            alert = await tracker.analyze_whale_with_ai(tx)
            alerts.append(alert)
        
        return alerts
