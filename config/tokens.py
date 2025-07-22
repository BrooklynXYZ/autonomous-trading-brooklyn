"""
Token addresses and chain configurations for Recall Network trading
"""

# Token configurations based on Recall Network supported tokens
TOKENS = {
    # Ethereum Mainnet
    "USDC_ETH": {
        "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "symbol": "USDC",
        "chain": "evm",
        "specificChain": "eth",
        "decimals": 6
    },
    "WETH_ETH": {
        "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "symbol": "WETH",
        "chain": "evm", 
        "specificChain": "eth",
        "decimals": 18
    },
    
    # Solana
    "SOL_SVM": {
        "address": "So11111111111111111111111111111111111111112",
        "symbol": "SOL",
        "chain": "svm",
        "specificChain": "svm",
        "decimals": 9
    },
    "USDC_SVM": {
        "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "symbol": "USDC",
        "chain": "svm",
        "specificChain": "svm", 
        "decimals": 6
    },
    
    # Polygon
    "USDC_POLYGON": {
        "address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "symbol": "USDC",
        "chain": "evm",
        "specificChain": "polygon",
        "decimals": 6
    },
    
    # Base
    "USDBC_BASE": {
        "address": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
        "symbol": "USDbC",
        "chain": "evm",
        "specificChain": "base",
        "decimals": 6
    },
    
    # Arbitrum
    "USDC_ARBITRUM": {
        "address": "0xaf88d065e77c8cc2239327c5edb3a432268e5831",
        "symbol": "USDC",
        "chain": "evm",
        "specificChain": "arbitrum",
        "decimals": 6
    },
    
    # Optimism
    "USDC_OPTIMISM": {
        "address": "0x7f5c764cbc14f9669b88837ca1490cca17c31607",
        "symbol": "USDC",
        "chain": "evm",
        "specificChain": "optimism",
        "decimals": 6
    }
}

# Trading pairs we'll focus on
TRADING_PAIRS = [
    {
        "name": "WETH/USDC_ETH",
        "base": TOKENS["WETH_ETH"],
        "quote": TOKENS["USDC_ETH"],
        "priority": 1
    },
    {
        "name": "SOL/USDC_SVM", 
        "base": TOKENS["SOL_SVM"],
        "quote": TOKENS["USDC_SVM"],
        "priority": 2
    }
] 