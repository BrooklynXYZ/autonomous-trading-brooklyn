from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
import numpy as np

class Chain(Enum):
    ETHEREUM = "ethereum"
    SOLANA = "solana"
    BASE = "base"
    BSC = "bsc"
    ARBITRUM = "arbitrum"

class TransactionType(Enum):
    TRANSFER = "transfer"
    EXCHANGE_DEPOSIT = "exchange_deposit"
    EXCHANGE_WITHDRAWAL = "exchange_withdrawal"
    SWAP = "swap"
    MINT = "mint"
    BURN = "burn"


from dataclasses import dataclass
from datetime import datetime

@dataclass
class BacktestResult:
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    avg_trade_duration: float
    trades: list
    equity_curve: list
    timestamps: list


@dataclass
class WhaleTransaction:
    chain: Chain
    hash: str
    from_address: str
    to_address: str
    amount: float
    value_usd: float
    token_symbol: str
    token_address: Optional[str]
    timestamp: datetime
    transaction_type: TransactionType
    block_number: int
    gas_used: Optional[int] = None
    exchange_detected: Optional[str] = None

@dataclass
class WhaleWallet:
    address: str
    chain: Chain
    balance_usd: float
    token_holdings: Dict[str, float]
    transaction_count: int
    first_seen: datetime
    last_activity: datetime
    risk_score: float = 0.0
    ai_analysis: Optional[str] = None

@dataclass
class WhaleAlert:
    transaction: WhaleTransaction
    wallet: WhaleWallet
    alert_type: str
    confidence: float
    ai_reasoning: str
    created_at: datetime

@dataclass
class TradingState:
    timestamp: datetime
    price_data: Dict[str, float]
    whale_signals: List[WhaleAlert]
    technical_indicators: np.ndarray
    sentiment_score: float
    market_regime: str

class OrderAction(Enum):
    HOLD = 0
    BUY = 1
    SELL = 2

@dataclass
class TradeSignal:
    symbol: str
    timestamp: datetime
    action: OrderAction
    confidence: float
    price: float
    quantity: Optional[float]
    source_agent: str
    reasoning: str
