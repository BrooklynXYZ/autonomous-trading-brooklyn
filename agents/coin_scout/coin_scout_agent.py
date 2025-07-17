import asyncio
import grpc
from concurrent import futures
import logging
from typing import List, Dict, Optional
import time
import json
import websockets
import requests
from dataclasses import dataclass
from datetime import datetime, timedelta

import trading_agents_pb2
import trading_agents_pb2_grpc
from .dex_scanner import DEXScanner
from .pair_detector import PairDetector
from .config import CoinScoutConfig

@dataclass
class TokenPair:
    symbol: str
    address: str
    dex: str
    price: float
    volume_24h: float
    liquidity: float
    created_at: int

class CoinScoutAgent(trading_agents_pb2_grpc.CoinScoutServiceServicer):
    def __init__(self, config: CoinScoutConfig):
        self.config = config
        self.dex_scanner = DEXScanner(config.dex_config)
        self.pair_detector = PairDetector(config.detection_config)
        self.discovered_pairs: Dict[str, TokenPair] = {}
        self.logger = logging.getLogger(__name__)
        
        # Start background tasks
        self.running = True
        asyncio.create_task(self.continuous_scanning())
        
    async def continuous_scanning(self):
        """Continuously scan for new pairs"""
        while self.running:
            try:
                # Scan each configured DEX
                for dex_name in self.config.dex_list:
                    new_pairs = await self.dex_scanner.scan_dex(dex_name)
                    for pair in new_pairs:
                        if pair.symbol not in self.discovered_pairs:
                            self.discovered_pairs[pair.symbol] = pair
                            self.logger.info(f"Discovered new pair: {pair.symbol} on {pair.dex}")
                
                await asyncio.sleep(self.config.scan_interval)
                
            except Exception as e:
                self.logger.error(f"Error in continuous scanning: {e}")
                await asyncio.sleep(30)

    async def GetNewPairs(self, request, context):
        """Get newly discovered pairs"""
        try:
            # Filter pairs discovered in the last hour
            recent_pairs = []
            current_time = int(time.time())
            
            for pair in self.discovered_pairs.values():
                if current_time - pair.created_at < 3600:  # Last hour
                    recent_pairs.append(trading_agents_pb2.TokenPair(
                        symbol=pair.symbol,
                        address=pair.address,
                        dex=pair.dex,
                        price=pair.price,
                        volume_24h=pair.volume_24h,
                        liquidity=pair.liquidity,
                        created_at=pair.created_at
                    ))
            
            return trading_agents_pb2.PairListResponse(pairs=recent_pairs)
            
        except Exception as e:
            self.logger.error(f"Error getting new pairs: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return trading_agents_pb2.PairListResponse()

    async def ScanDEXPairs(self, request, context):
        """Scan specific DEX for pairs"""
        try:
            pairs = await self.dex_scanner.scan_dex(
                request.dex,
                min_liquidity=request.min_liquidity,
                max_age_hours=request.max_age_hours
            )
            
            grpc_pairs = [
                trading_agents_pb2.TokenPair(
                    symbol=pair.symbol,
                    address=pair.address,
                    dex=pair.dex,
                    price=pair.price,
                    volume_24h=pair.volume_24h,
                    liquidity=pair.liquidity,
                    created_at=pair.created_at
                ) for pair in pairs
            ]
            
            return trading_agents_pb2.PairListResponse(pairs=grpc_pairs)
            
        except Exception as e:
            self.logger.error(f"Error scanning DEX pairs: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return trading_agents_pb2.PairListResponse()

    async def GetPairDetails(self, request, context):
        """Get detailed information about a specific pair"""
        try:
            pair = self.discovered_pairs.get(request.symbol)
            if not pair:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Pair {request.symbol} not found")
                return trading_agents_pb2.PairDetailsResponse()
            
            # Get price history
            price_history = await self.dex_scanner.get_price_history(pair.address)
            
            grpc_pair = trading_agents_pb2.TokenPair(
                symbol=pair.symbol,
                address=pair.address,
                dex=pair.dex,
                price=pair.price,
                volume_24h=pair.volume_24h,
                liquidity=pair.liquidity,
                created_at=pair.created_at
            )
            
            grpc_price_history = [
                trading_agents_pb2.PricePoint(
                    timestamp=point['timestamp'],
                    price=point['price'],
                    volume=point['volume']
                ) for point in price_history
            ]
            
            return trading_agents_pb2.PairDetailsResponse(
                pair=grpc_pair,
                price_history=grpc_price_history,
                market_cap=pair.price * pair.volume_24h,  # Simplified calculation
                contract_verified="true"  # TODO: Implement contract verification
            )
            
        except Exception as e:
            self.logger.error(f"Error getting pair details: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return trading_agents_pb2.PairDetailsResponse()

def serve():
    config = CoinScoutConfig.load_from_file('config/agents/coin_scout.yaml')
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    
    coin_scout_agent = CoinScoutAgent(config)
    trading_agents_pb2_grpc.add_CoinScoutServiceServicer_to_server(
        coin_scout_agent, server
    )
    
    listen_addr = f'[::]:{config.grpc_port}'
    server.add_insecure_port(listen_addr)
    
    logging.info(f"Coin Scout Agent starting on {listen_addr}")
    return server

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    server = serve()
    
    async def run_server():
        await server.start()
        await server.wait_for_termination()
    
    asyncio.run(run_server())
