# LLM-Powered Trading Agent with Mastra: Complete Strategy & Implementation Plan

Based on my research into Mastra and MCP architectures, here's a comprehensive plan for building an LLM-driven trading agent for ETH and SOL pairs on Recall Network.

## Mastra Framework Analysis

### Core Capabilities
**Mastra** is a TypeScript-native agent framework designed for production AI applications[1]. Key features relevant to our trading use case:

- **Graph-based State Machines**: Workflows are durable, deterministic systems that handle loops, branching, error handling, and retries[1][2]
- **Agent Orchestration**: Built-in support for multi-agent coordination with memory and tool execution[1]
- **Production-Ready**: Includes observability, evaluation capabilities, and REST API endpoints[3]
- **MCP Integration**: Seamless integration with Model Context Protocol servers for external data sources[4]

### Workflow Architecture
Mastra workflows use discrete steps with clear inputs/outputs, making them perfect for systematic trading operations[1]. The framework supports:
- Sequential step execution with data flow between steps
- Conditional branching based on market conditions
- Error handling and retry mechanisms for API failures
- State persistence across trading cycles

## Recommended Trading Strategy

### Hybrid Momentum-Mean Reversion Strategy
**Core Philosophy**: Combine trend-following with contrarian signals for conservative, high-probability trades.

**Entry Conditions**:
- **Momentum Entry**: RSI > 70 with volume spike (>150% avg) for short positions
- **Mean Reversion Entry**: RSI 
  calculateRSI(prices: number[], period: number): Promise
  calculateBollingerBands(prices: number[], period: number): Promise
  calculateEMA(prices: number[], period: number): Promise
  formatForLLM(data: TechnicalData): Promise
}
```

**Tool 2: Trade Analysis Formatter**
```typescript
// Formats market conditions into LLM-readable analysis
interface AnalysisFormatter {
  formatMarketSummary(ethData: MarketData, solData: MarketData): string
  formatSignalStrength(signals: TradingSignals): string
  formatRiskMetrics(portfolio: PortfolioData): string
}
```

## Complete Mastra Workflow Implementation

### Step 1: Market Data Collection
```typescript
const fetchMarketDataStep = new Step({
  id: "fetchMarketData",
  execute: async ({ context }) => {
    // Fetch 4H and 1H candles for both pairs
    const ethData = await marketDataTool.fetchCandles("ethereum", "1h");
    const solData = await marketDataTool.fetchCandles("solana", "1h");
    
    // Calculate technical indicators
    const ethAnalysis = {
      rsi: await marketDataTool.calculateRSI(ethData.closes, 14),
      ema21: await marketDataTool.calculateEMA(ethData.closes, 21),
      bollinger: await marketDataTool.calculateBollingerBands(ethData.closes, 20),
      volume_ratio: ethData.volume / ethData.avgVolume,
      price_change_24h: (ethData.close - ethData.open24h) / ethData.open24h
    };
    
    const solAnalysis = { /* Similar calculations for SOL */ };
    
    return {
      ethData: ethAnalysis,
      solData: solAnalysis,
      marketSummary: await analysisFormatter.formatMarketSummary(ethAnalysis, solAnalysis)
    };
  }
});
```

### Step 2: Portfolio State Analysis
```typescript
const portfolioAnalysisStep = new Step({
  id: "portfolioAnalysis", 
  execute: async ({ context }) => {
    // Using existing Recall MCP Server
    const portfolio = await recallMCP.getPortfolio();
    const trades = await recallMCP.getTrades();
    const balances = await recallMCP.getBalances();
    
    const openPositions = trades.filter(t => t.status === 'open');
    const portfolioValue = portfolio.totalValue;
    
    return {
      openPositions,
      availableCash: balances.find(b => b.symbol === 'USDC')?.amount || 0,
      portfolioValue,
      positionSummary: formatPositionsForLLM(openPositions)
    };
  }
});
```

### Step 3: ETH Trading Decisions
```typescript
const ethTradingStep = new Step({
  id: "ethTrading",
  execute: async ({ context }) => {
    const { ethData } = context.getStepResult("fetchMarketData");
    const { openPositions, availableCash } = context.getStepResult("portfolioAnalysis");
    
    const ethPosition = openPositions.find(p => p.symbol === 'ETH');
    
    const prompt = `
TRADING ANALYSIS - ETHEREUM (ETH/USDC)

CURRENT MARKET CONDITIONS:
- Price: $${ethData.price}
- RSI (14): ${ethData.rsi}
- 21-period EMA: $${ethData.ema21}
- Bollinger Band Position: ${ethData.bollinger.position}
- Volume Ratio: ${ethData.volume_ratio}x
- 24h Change: ${ethData.price_change_24h}%

CURRENT POSITION:
${ethPosition ? 
  `OPEN POSITION - ${ethPosition.size} ETH at $${ethPosition.entry_price} (${ethPosition.pnl_percent}% PnL)` : 
  'NO OPEN POSITION'
}

AVAILABLE CASH: $${availableCash}

TRADING RULES:
1. POSITION MANAGEMENT (if position exists):
   - Exit if profit target reached (+3% momentum, +2% mean reversion)
   - Exit if stop loss triggered (-2%)
   - Exit if RSI reverses through 50 level
   - Consider adding if strong confirmation and within risk limits

2. NEW POSITION ENTRY (if no position):
   - LONG: RSI  70 AND volume spike >150% AND 21-EMA downtrend
   - Position size: 10-15% of available cash
   - Never risk more than 2% of portfolio

DECISION REQUIRED:
Based on current conditions, what action should be taken for ETH?
Provide specific trade details: BUY/SELL/HOLD, amount, reasoning, and risk assessment.
Format: ACTION|AMOUNT|REASONING|RISK_LEVEL
`;

    const decision = await ethTradingAgent.generate(prompt);
    return { ethDecision: decision.text };
  }
});
```

### Step 4: SOL Trading Decisions
```typescript
const solTradingStep = new Step({
  id: "solTrading", 
  execute: async ({ context }) => {
    // Similar implementation for SOL with adjusted parameters
    // SOL typically more volatile, so wider stops and smaller positions
    const { solData } = context.getStepResult("fetchMarketData");
    
    const prompt = `/* Similar prompt structure for SOL with volatility adjustments */`;
    const decision = await solTradingAgent.generate(prompt);
    return { solDecision: decision.text };
  }
});
```

### Step 5: Trade Execution & Logging
```typescript
const tradeExecutionStep = new Step({
  id: "tradeExecution",
  execute: async ({ context }) => {
    const { ethDecision } = context.getStepResult("ethTrading");
    const { solDecision } = context.getStepResult("solTrading"); 
    
    const executions = [];
    
    // Parse and execute ETH decision
    if (ethDecision.includes("BUY") || ethDecision.includes("SELL")) {
      const [action, amount, reasoning] = ethDecision.split("|");
      const result = await recallMCP.executeTrade({
        fromToken: action === "BUY" ? "USDC" : "ETH",
        toToken: action === "BUY" ? "ETH" : "USDC", 
        amount: amount.trim(),
        reason: `LLM Decision: ${reasoning.trim()}`
      });
      executions.push({ pair: "ETH", result });
    }
    
    // Similar for SOL
    
    return { tradeExecutions: executions };
  }
});
```

### Complete Workflow Assembly
```typescript
export const tradingWorkflow = new Workflow({
  name: "eth-sol-trading-workflow",
  triggerSchema: z.object({
    timestamp: z.string().describe("Trading cycle timestamp")
  })
});

// Sequential execution with error handling
tradingWorkflow
  .step(fetchMarketDataStep)
  .then(portfolioAnalysisStep)
  .then(ethTradingStep) 
  .then(solTradingStep)
  .then(tradeExecutionStep)
  .commit();
```

## Agent Prompt Engineering

### Core Agent Configuration
```typescript
const tradingAgent = new Agent({
  name: 'Conservative Crypto Trader',
  instructions: `You are a professional cryptocurrency trader specializing in ETH and SOL.

CORE PRINCIPLES:
- Risk management is paramount - never risk more than 2% on any single trade
- Use technical analysis (RSI, moving averages, Bollinger Bands) for decision making
- Position sizes must be conservative (10-15% of available capital)
- Always provide clear reasoning for every decision
- Be decisive but not impulsive - wait for high-probability setups

RESPONSE FORMAT:
Always respond with: ACTION|AMOUNT|REASONING|RISK_LEVEL
- ACTION: BUY/SELL/HOLD/EXIT
- AMOUNT: Specific dollar amount or percentage
- REASONING: 1-2 sentence explanation
- RISK_LEVEL: LOW/MEDIUM/HIGH`,
  
  model: openai('gpt-4o-mini'), //change to groq Llama 4
  tools: { marketDataTool, recallMCP }
});
```

## Implementation Timeline & Deployment

### Phase 1: Infrastructure Setup (2-4 hours)
1. **Initialize Mastra project** with agents and workflows
2. **Configure Recall MCP server** with API credentials
3. **Build custom market data tools** for CoinGecko/CMC integration
4. **Test data fetching and formatting** pipelines

### Phase 2: Strategy Implementation (3-4 hours)
1. **Implement workflow steps** as defined above
2. **Fine-tune trading prompts** for consistent decision-making
3. **Add comprehensive error handling** for API failures
4. **Implement position sizing calculations**

### Phase 3: Testing & Optimization (2-3 hours)
1. **Paper trading validation** with small amounts
2. **Prompt engineering refinement** based on decision quality
3. **Performance monitoring setup** with logging
4. **Risk management validation**

## Expected Performance & Risk Management

### Performance Targets
- **Conservative Daily Return**: 2-5%
- **Risk-Adjusted Return**: Sharpe Ratio > 1.5
- **Win Rate**: Target 60-65% with proper risk/reward ratios
- **Maximum Drawdown**: <10% portfolio value

### Risk Controls
- **Position Limits**: Max 30% allocation per pair
- **Daily Loss Limits**: Stop trading if daily losses exceed 5%
- **API Failure Handling**: Graceful degradation with manual intervention triggers
- **Volatility Circuit Breakers**: Pause trading during extreme market conditions

