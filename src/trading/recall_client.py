import requests
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from config.config import config

logger = logging.getLogger(__name__)

class RecallClient:
    """Client for interacting with Recall Network API"""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or config.RECALL_API_TOKEN
        self.base_url = config.RECALL_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        })
    
    def execute_trade(
        self,
        from_token: str,
        to_token: str,
        amount: str,
        reason: str,
        slippage_tolerance: str = "1.0",
        from_chain: str = "evm",
        to_chain: str = "evm",
        from_specific_chain: str = None,
        to_specific_chain: str = None
    ) -> Dict[str, Any]:
        """
        Execute a trade on Recall Network
        
        Args:
            from_token: Token address to sell
            to_token: Token address to buy
            amount: Amount of from_token to trade
            reason: Reason for executing trade
            slippage_tolerance: Slippage tolerance percentage
            from_chain: Blockchain type for from_token
            to_chain: Blockchain type for to_token
            from_specific_chain: Specific chain for from_token
            to_specific_chain: Specific chain for to_token
            
        Returns:
            API response dict
        """
        
        payload = {
            "fromToken": from_token,
            "toToken": to_token,
            "amount": amount,
            "reason": reason,
            "slippageTolerance": slippage_tolerance
        }
        
        # Add chain information if provided
        if from_chain:
            payload["fromChain"] = from_chain
        if to_chain:
            payload["toChain"] = to_chain
        if from_specific_chain:
            payload["fromSpecificChain"] = from_specific_chain
        if to_specific_chain:
            payload["toSpecificChain"] = to_specific_chain
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/trade/execute",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Trade executed successfully: {result.get('transaction', {}).get('id')}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Trade execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_trades(self) -> Dict[str, Any]:
        """Get all trades for the agent"""
        
        try:
            response = self.session.get(f"{self.base_url}/api/agent/trades")
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch trades: {e}")
            return {"success": False, "error": str(e)}
    
    def get_balances(self) -> Dict[str, Any]:
        """Get all token balances for the agent"""
        
        try:
            response = self.session.get(f"{self.base_url}/api/agent/balances")
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch balances: {e}")
            return {"success": False, "error": str(e)}
    
    def get_portfolio(self) -> Dict[str, Any]:
        """Get portfolio information with real-time prices"""
        
        try:
            response = self.session.get(f"{self.base_url}/api/agent/portfolio")
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch portfolio: {e}")
            return {"success": False, "error": str(e)}
