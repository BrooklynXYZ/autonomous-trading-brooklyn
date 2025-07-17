import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import time
import json
import websockets
from web3 import Web3
from eth_utils import to_checksum_address

@dataclass
class DEXConfig:
    uniswap_v2_factory: str
    pancakeswap_factory: str
    sushiswap_factory: str
    rpc_endpoints: Dict[str, str]
    api_keys: Dict[str, str]

class DEXScanner:
    def __init__(self, config: DEXConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.web3_connections = {}
        
        # Initialize Web3 connections
        for chain, rpc_url in config.rpc_endpoints.items():
            self.web3_connections[chain] = Web3(Web3.HTTPProvider(rpc_url))
    
    async def scan_dex(self, dex_name: str, min_liquidity: int = 1000, max_age_hours: int = 24) -> List:
        """Scan a specific DEX for new pairs"""
        try:
            if dex_name.lower() == 'uniswap':
                return await self._scan_uniswap(min_liquidity, max_age_hours)
            elif dex_name.lower() == 'pancakeswap':
                return await self._scan_pancakeswap(min_liquidity, max_age_hours)
            elif dex_name.lower() == 'sushiswap':
                return await self._scan_sushiswap(min_liquidity, max_age_hours)
            else:
                self.logger.warning(f"Unsupported DEX: {dex_name}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error scanning {dex_name}: {e}")
            return []
    
    async def _scan_uniswap(self, min_liquidity: int, max_age_hours: int) -> List:
        """Scan Uniswap V2 for new pairs"""
        try:
            # Use DexScreener API for real-time data
            url = "https://api.dexscreener.com/latest/dex/tokens"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    pairs = []
                    current_time = int(time.time())
                    
                    for pair_data in data.get('pairs', []):
                        if pair_data.get('dexId') == 'uniswap':
                            # Filter by age and liquidity
                            created_at = pair_data.get('pairCreatedAt', 0)
                            liquidity = float(pair_data.get('liquidity', {}).get('usd', 0))
                            
                            if (current_time - created_at) <= (max_age_hours * 3600) and liquidity >= min_liquidity:
                                from agents.coin_scout.coin_scout_agent import TokenPair
                                
                                pair = TokenPair(
                                    symbol=pair_data['baseToken']['symbol'],
                                    address=pair_data['baseToken']['address'],
                                    dex='uniswap',
                                    price=float(pair_data['priceUsd']),
                                    volume_24h=float(pair_data['volume']['h24']),
                                    liquidity=liquidity,
                                    created_at=created_at
                                )
                                pairs.append(pair)
                    
                    return pairs
                    
        except Exception as e:
            self.logger.error(f"Error scanning Uniswap: {e}")
            return []
    
    async def _scan_pancakeswap(self, min_liquidity: int, max_age_hours: int) -> List:
        """Scan PancakeSwap for new pairs"""
        try:
            # PancakeSwap API endpoint
            url = "https://api.pancakeswap.info/api/v2/pairs"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    pairs = []
                    current_time = int(time.time())
                    
                    for pair_id, pair_data in data.get('data', {}).items():
                        # Filter by age and liquidity
                        liquidity = float(pair_data.get('reserve_usd', 0))
                        
                        if liquidity >= min_liquidity:
                            from agents.coin_scout.coin_scout_agent import TokenPair
                            
                            pair = TokenPair(
                                symbol=pair_data['token0']['symbol'],
                                address=pair_data['token0']['id'],
                                dex='pancakeswap',
                                price=float(pair_data['token0_price']),
                                volume_24h=float(pair_data['volume_usd']),
                                liquidity=liquidity,
                                created_at=current_time  # PancakeSwap doesn't provide creation time
                            )
                            pairs.append(pair)
                    
                    return pairs
                    
        except Exception as e:
            self.logger.error(f"Error scanning PancakeSwap: {e}")
            return []
    
    async def _scan_sushiswap(self, min_liquidity: int, max_age_hours: int) -> List:
        """Scan SushiSwap for new pairs"""
        try:
            # SushiSwap subgraph query
            query = """
            {
                pairs(first: 100, orderBy: createdAtTimestamp, orderDirection: desc) {
                    id
                    token0 {
                        id
                        symbol
                        name
                    }
                    token1 {
                        id
                        symbol
                        name
                    }
                    reserve0
                    reserve1
                    reserveUSD
                    volumeUSD
                    createdAtTimestamp
                }
            }
            """
            
            url = "https://api.thegraph.com/subgraphs/name/sushiswap/exchange"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={'query': query}) as response:
                    data = await response.json()
                    
                    pairs = []
                    current_time = int(time.time())
                    
                    for pair_data in data.get('data', {}).get('pairs', []):
                        created_at = int(pair_data['createdAtTimestamp'])
                        liquidity = float(pair_data['reserveUSD'])
                        
                        if (current_time - created_at) <= (max_age_hours * 3600) and liquidity >= min_liquidity:
                            from agents.coin_scout.coin_scout_agent import TokenPair
                            
                            pair = TokenPair(
                                symbol=pair_data['token0']['symbol'],
                                address=pair_data['token0']['id'],
                                dex='sushiswap',
                                price=0.0,  # Calculate from reserves
                                volume_24h=float(pair_data['volumeUSD']),
                                liquidity=liquidity,
                                created_at=created_at
                            )
                            pairs.append(pair)
                    
                    return pairs
                    
        except Exception as e:
            self.logger.error(f"Error scanning SushiSwap: {e}")
            return []
    
    async def get_price_history(self, token_address: str) -> List[Dict]:
        """Get price history for a token"""
        try:
            # Use DexScreener API for price history
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    data = await response.json()
                    
                    price_history = []
                    for pair in data.get('pairs', []):
                        # Generate mock price history (in real implementation, use actual historical data)
                        current_time = int(time.time())
                        current_price = float(pair['priceUsd'])
                        
                        for i in range(24):  # Last 24 hours
                            timestamp = current_time - (i * 3600)
                            # Mock price variation
                            price_variation = 1 + (i * 0.001)  # Simple variation
                            price = current_price * price_variation
                            
                            price_history.append({
                                'timestamp': timestamp,
                                'price': price,
                                'volume': float(pair['volume']['h24']) / 24  # Average hourly volume
                            })
                    
                    return price_history
                    
        except Exception as e:
            self.logger.error(f"Error getting price history: {e}")
            return []
    
    async def listen_to_new_pairs(self):
        """Listen to blockchain events for new pair creation"""
        try:
            # Listen to Uniswap V2 Factory PairCreated events
            if 'ethereum' in self.web3_connections:
                web3 = self.web3_connections['ethereum']
                
                # Contract ABI for PairCreated event
                pair_created_abi = [
                    {
                        "anonymous": False,
                        "inputs": [
                            {"indexed": True, "name": "token0", "type": "address"},
                            {"indexed": True, "name": "token1", "type": "address"},
                            {"indexed": False, "name": "pair", "type": "address"},
                            {"indexed": False, "name": "", "type": "uint256"}
                        ],
                        "name": "PairCreated",
                        "type": "event"
                    }
                ]
                
                factory_address = self.config.uniswap_v2_factory
                factory_contract = web3.eth.contract(
                    address=to_checksum_address(factory_address),
                    abi=pair_created_abi
                )
                
                # Create event filter
                event_filter = factory_contract.events.PairCreated.createFilter(fromBlock='latest')
                
                while True:
                    try:
                        for event in event_filter.get_new_entries():
                            self.logger.info(f"New pair created: {event['args']}")
                            # Process the new pair event
                            await self._process_pair_created_event(event)
                        
                        await asyncio.sleep(5)  # Check every 5 seconds
                        
                    except Exception as e:
                        self.logger.error(f"Error listening to events: {e}")
                        await asyncio.sleep(30)
                        
        except Exception as e:
            self.logger.error(f"Error setting up event listener: {e}")
    
    async def _process_pair_created_event(self, event):
        """Process a new pair creation event"""
        try:
            # Extract token addresses from event
            token0_address = event['args']['token0']
            token1_address = event['args']['token1']
            pair_address = event['args']['pair']
            
            # Get token information
            # This would typically involve calling token contracts to get symbol, name, etc.
            # For now, we'll create a basic pair entry
            
            from agents.coin_scout.coin_scout_agent import TokenPair
            
            pair = TokenPair(
                symbol=f"TOKEN_{token0_address[:6]}",  # Simplified
                address=token0_address,
                dex='uniswap',
                price=0.0,
                volume_24h=0.0,
                liquidity=0.0,
                created_at=int(time.time())
            )
            
            self.logger.info(f"Processed new pair: {pair.symbol}")
            
        except Exception as e:
            self.logger.error(f"Error processing pair created event: {e}")
