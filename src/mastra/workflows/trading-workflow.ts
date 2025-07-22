import { createStep, createWorkflow } from '@mastra/core/workflows';
import { z } from 'zod';
import { getHistoricalCryptoPrices } from '../tools/coingecko-tools';
import {
  getRecallAgentPortfolio,
  getRecallAgentBalances,
  getRecallAgentTrades,
  executeRecallTrade,
} from '../tools/recall-tools';

// --- Utility Functions for Technical Indicators ---
function calculateEMA(prices: number[], period: number): number[] {
  const k = 2 / (period + 1);
  let ema: number[] = [];
  let prevEma = prices[0];
  ema.push(prevEma);
  for (let i = 1; i < prices.length; i++) {
    prevEma = prices[i] * k + prevEma * (1 - k);
    ema.push(prevEma);
  }
  return ema;
}

function calculateRSI(prices: number[], period: number): number {
  let gains = 0;
  let losses = 0;
  for (let i = prices.length - period; i < prices.length - 1; i++) {
    const diff = prices[i + 1] - prices[i];
    if (diff > 0) gains += diff;
    else losses -= diff;
  }
  const avgGain = gains / period;
  const avgLoss = losses / period;
  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

function calculateBollingerBands(prices: number[], period: number = 20, numStdDev: number = 2) {
  if (prices.length < period) return { upper: null, lower: null, middle: null, position: null };
  const slice = prices.slice(-period);
  const mean = slice.reduce((a, b) => a + b, 0) / period;
  const variance = slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / period;
  const stdDev = Math.sqrt(variance);
  const upper = mean + numStdDev * stdDev;
  const lower = mean - numStdDev * stdDev;
  const last = prices[prices.length - 1];
  let position = 'middle';
  if (last > upper) position = 'above';
  else if (last < lower) position = 'below';
  return { upper, lower, middle: mean, position };
}

// 1. Fetch Market Data
export const fetchMarketDataStep = createStep({
  id: 'fetchMarketData',
  description: 'Fetches 1H and 4H candles for ETH and SOL',
  inputSchema: z.object({}),
  outputSchema: z.object({
    ethRaw: z.any(),
    solRaw: z.any(),
  }),
  execute: async ({ runtimeContext }) => {
    let eth1h: any[] = [];
    let sol1h: any[] = [];
    if (getHistoricalCryptoPrices && getHistoricalCryptoPrices.execute) {
      const ethResult = await getHistoricalCryptoPrices.execute({ context: { id: 'ethereum', days: 30 }, runtimeContext });
      const solResult = await getHistoricalCryptoPrices.execute({ context: { id: 'solana', days: 30 }, runtimeContext });
      eth1h = Array.isArray(ethResult) ? ethResult : [];
      sol1h = Array.isArray(solResult) ? solResult : [];
    }
    return { ethRaw: eth1h, solRaw: sol1h };
  },
});

// 2. Calculate Technical Indicators
export const calculateIndicatorsStep = createStep({
  id: 'calculateIndicators',
  description: 'Calculates RSI, EMA, Bollinger Bands, volume ratio, price change',
  inputSchema: z.object({
    ethRaw: z.any(),
    solRaw: z.any(),
  }),
  outputSchema: z.object({
    ethIndicators: z.any(),
    solIndicators: z.any(),
  }),
  execute: async ({ inputData }) => {
    // Assume ethRaw/solRaw is an array of { timestamp, price, volume }
    const extractPrices = (raw: any) => (Array.isArray(raw) ? raw.map((d: any) => d.price) : []);
    const extractVolumes = (raw: any) => (Array.isArray(raw) ? raw.map((d: any) => d.volume) : []);
    const ethPrices = extractPrices(inputData.ethRaw);
    const solPrices = extractPrices(inputData.solRaw);
    const ethVolumes = extractVolumes(inputData.ethRaw);
    const solVolumes = extractVolumes(inputData.solRaw);
    // Calculate indicators for last 21/20/14 periods
    const ethRSI = calculateRSI(ethPrices, 14);
    const ethEMA21 = calculateEMA(ethPrices, 21).slice(-1)[0];
    const ethBoll = calculateBollingerBands(ethPrices, 20);
    const ethChange = ethPrices.length > 24 ? (ethPrices[ethPrices.length - 1] - ethPrices[ethPrices.length - 25]) / ethPrices[ethPrices.length - 25] : 0;
    // Volume ratio: latest volume / average volume
    const ethAvgVol = ethVolumes.length > 0 ? ethVolumes.reduce((a, b) => a + b, 0) / ethVolumes.length : 0;
    const ethVolRatio = ethAvgVol > 0 ? (ethVolumes[ethVolumes.length - 1] / ethAvgVol) : 0;
    const ethIndicators = {
      rsi: ethRSI,
      ema21: ethEMA21,
      bollinger: ethBoll,
      price_change_24h: ethChange,
      volume_ratio: ethVolRatio,
    };
    const solRSI = calculateRSI(solPrices, 14);
    const solEMA21 = calculateEMA(solPrices, 21).slice(-1)[0];
    const solBoll = calculateBollingerBands(solPrices, 20);
    const solChange = solPrices.length > 24 ? (solPrices[solPrices.length - 1] - solPrices[solPrices.length - 25]) / solPrices[solPrices.length - 25] : 0;
    const solAvgVol = solVolumes.length > 0 ? solVolumes.reduce((a, b) => a + b, 0) / solVolumes.length : 0;
    const solVolRatio = solAvgVol > 0 ? (solVolumes[solVolumes.length - 1] / solAvgVol) : 0;
    const solIndicators = {
      rsi: solRSI,
      ema21: solEMA21,
      bollinger: solBoll,
      price_change_24h: solChange,
      volume_ratio: solVolRatio,
    };
    return { ethIndicators, solIndicators };
  },
});

// 3. Format Market Summary for LLM
export const formatMarketSummaryStep = createStep({
  id: 'formatMarketSummary',
  description: 'Formats technicals into LLM-readable summary',
  inputSchema: z.object({
    ethIndicators: z.any(),
    solIndicators: z.any(),
  }),
  outputSchema: z.object({
    ethSummary: z.string(),
    solSummary: z.string(),
    ethIndicators: z.any(),
    solIndicators: z.any(),
  }),
  execute: async ({ inputData }) => {
    // Simple formatter for LLM prompt context
    const format = (label: string, ind: any) =>
      `${label} Market Summary:\n` +
      `- RSI: ${ind.rsi?.toFixed(2)}\n` +
      `- EMA(21): ${ind.ema21?.toFixed(2)}\n` +
      `- Bollinger: [${ind.bollinger?.position}] (U:${ind.bollinger?.upper?.toFixed(2)}, L:${ind.bollinger?.lower?.toFixed(2)})\n` +
      `- 24h Change: ${(ind.price_change_24h * 100).toFixed(2)}%\n`;
    return {
      /*  ...inputData,*/
      ethSummary: format('ETH', inputData.ethIndicators),
      solSummary: format('SOL', inputData.solIndicators),
    };
  },
});

// 4. Fetch Portfolio State
export const fetchPortfolioStep = createStep({
  id: 'fetchPortfolio',
  description: 'Fetches portfolio, balances, and trades from Recall',
  inputSchema: z.object({
    ethSummary: z.string(),
    solSummary: z.string(),
  }),
  outputSchema: z.object({
    ethSummary: z.string(),
    solSummary: z.string(),
    portfolio: z.any(),
    balances: z.any(),
    trades: z.any(),
  }),
  execute: async ({ inputData, runtimeContext }) => {
    let portfolio = {};
    let balances = {};
    let trades = [];
    if (getRecallAgentPortfolio && getRecallAgentPortfolio.execute) {
      const result = await getRecallAgentPortfolio.execute({ context: {}, runtimeContext });
      portfolio = (result && typeof result === 'object' && !Array.isArray(result)) ? result : {};
    }
    if (getRecallAgentBalances && getRecallAgentBalances.execute) {
      const result = await getRecallAgentBalances.execute({ context: {}, runtimeContext });
      balances = (result && typeof result === 'object' && !Array.isArray(result)) ? result : {};
    }
    if (getRecallAgentTrades && getRecallAgentTrades.execute) {
      const result = await getRecallAgentTrades.execute({ context: {}, runtimeContext });
      // Patch: parse trades from API response (see PLan.md)
      trades = (result && Array.isArray(result.trades)) ? result.trades : [];
    }
    return {
      ethSummary: inputData.ethSummary,
      solSummary: inputData.solSummary,
      portfolio,
      balances,
      trades,
    };
  },
});

// 5. Format Portfolio State for LLM
export const formatPortfolioStep = createStep({
  id: 'formatPortfolio',
  description: 'Formats portfolio and risk metrics for LLM',
  inputSchema: z.object({
    ethSummary: z.string(),
    solSummary: z.string(),
    portfolio: z.any(),
    balances: z.any(),
    trades: z.any(),
  }),
  outputSchema: z.object({
    ethSummary: z.string(),
    solSummary: z.string(),
    portfolioSummary: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
    trades: z.any(),
  }),
  execute: async ({ inputData }) => {
    // Patch: count all trades as completed (Recall API does not provide open/closed status)
    const trades = Array.isArray(inputData.trades) ? inputData.trades : [];
    const openPositions = trades.length; // All trades are completed
    let availableCash = 0;
    if (Array.isArray(inputData.portfolio?.tokens)) {
      availableCash = inputData.portfolio.tokens
        .filter((t: any) => t.symbol === 'USDC' || t.symbol === 'USDbC')
        .reduce((sum: number, t: any) => sum + Number(t.value || 0), 0);
    }
    const summary = `Portfolio Value: $${inputData.portfolio?.totalValue || 'N/A'}\n` +
      `Completed Trades: ${openPositions}\n` +
      `Available Cash: $${availableCash}`;
    return {
      ethSummary: inputData.ethSummary,
      solSummary: inputData.solSummary,
      portfolioSummary: summary,
      openPositions,
      availableCash,
      trades,
    };
  },
});

// 6. ETH Trading Decision
export const ethTradingDecisionStep = createStep({
  id: 'ethTradingDecision',
  description: 'LLM makes ETH trading decision',
  inputSchema: z.object({
    ethSummary: z.string(),
    portfolioSummary: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
    solSummary: z.string(),
/*     ethIndicators: z.any(),
    solIndicators: z.any(), */
/*     portfolio: z.any(), */
    balances: z.any(),
    trades: z.any(),
  }),
  outputSchema: z.object({
    ethSummary: z.string(),
    portfolioSummary: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
    solSummary: z.string(),
/*     ethIndicators: z.any(),
    solIndicators: z.any(), */
/*     portfolio: z.any(), */
    balances: z.any(),
    trades: z.any(),
    ethDecision: z.string(),
  }),
  execute: async ({ inputData, mastra }) => {
    const agent = mastra?.getAgent?.('tradingAgent');
    if (!agent) return { ...inputData, ethDecision: 'HOLD|--|No agent available|LOW' };
    const prompt = `TRADING ANALYSIS - ETHEREUM (ETH/USDC)\n\n${inputData.ethSummary}\n\n${inputData.portfolioSummary}\n\nCURRENT POSITION:\n${inputData.openPositions && inputData.openPositions.length > 0 ? JSON.stringify(inputData.openPositions) : 'NO OPEN POSITION'}\n\nAVAILABLE CASH: $${inputData.availableCash}\n\nTRADING RULES:\n1. POSITION MANAGEMENT (if position exists):\n   - Exit if profit target reached (+3% momentum, +2% mean reversion)\n   - Exit if stop loss triggered (-2%)\n   - Exit if RSI reverses through 50 level\n   - Consider adding if strong confirmation and within risk limits\n2. NEW POSITION ENTRY (if no position):\n   - LONG: RSI < 30 AND price below lower Bollinger Band\n   - SHORT: RSI > 70 AND volume spike >150% AND 21-EMA downtrend\n   - Position size: 10-15% of available cash\n   - Never risk more than 2% of portfolio\n\nDECISION REQUIRED:\nBased on current conditions, what action should be taken for ETH?\nProvide specific trade details: BUY/SELL/HOLD, amount, reasoning, and risk assessment.\nFormat: ACTION|AMOUNT|REASONING|RISK_LEVEL`;
    const decision = await agent.generate(prompt);
    return { ...inputData, ethDecision: decision.text || 'HOLD|--|No decision|LOW' };
  },
});

// 7. SOL Trading Decision
export const solTradingDecisionStep = createStep({
  id: 'solTradingDecision',
  description: 'LLM makes SOL trading decision',
  inputSchema: z.object({
    solSummary: z.string(),
    portfolioSummary: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
    ethSummary: z.string(),
/*     ethIndicators: z.any(),
    solIndicators: z.any(), */
/*     portfolio: z.any(), */
    balances: z.any(),
    trades: z.any(),
    ethDecision: z.string(),
  }),
  outputSchema: z.object({
    solSummary: z.string(),
    portfolioSummary: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
    ethSummary: z.string(),
/*     ethIndicators: z.any(),
    solIndicators: z.any(), */
    portfolio: z.any(),
    balances: z.any(),
    trades: z.any(),
    ethDecision: z.string(),
    solDecision: z.string(),
  }),
  execute: async ({ inputData, mastra }) => {
    const agent = mastra?.getAgent?.('tradingAgent');
    if (!agent) return { ...inputData, solDecision: 'HOLD|--|No agent available|LOW' };
    const prompt = `TRADING ANALYSIS - SOLANA (SOL/USDC)\n\n${inputData.solSummary}\n\n${inputData.portfolioSummary}\n\nCURRENT POSITION:\n${inputData.openPositions && inputData.openPositions.length > 0 ? JSON.stringify(inputData.openPositions) : 'NO OPEN POSITION'}\n\nAVAILABLE CASH: $${inputData.availableCash}\n\nTRADING RULES:\n1. POSITION MANAGEMENT (if position exists):\n   - Exit if profit target reached (+3% momentum, +2% mean reversion)\n   - Exit if stop loss triggered (-2%)\n   - Exit if RSI reverses through 50 level\n   - Consider adding if strong confirmation and within risk limits\n2. NEW POSITION ENTRY (if no position):\n   - LONG: RSI < 30 AND price below lower Bollinger Band\n   - SHORT: RSI > 70 AND volume spike >150% AND 21-EMA downtrend\n   - Position size: 10-15% of available cash\n   - Never risk more than 2% of portfolio\n\nDECISION REQUIRED:\nBased on current conditions, what action should be taken for SOL?\nProvide specific trade details: BUY/SELL/HOLD, amount, reasoning, and risk assessment.\nFormat: ACTION|AMOUNT|REASONING|RISK_LEVEL`;
    const decision = await agent.generate(prompt);
    return { ...inputData, solDecision: decision.text || 'HOLD|--|No decision|LOW' };
  },
});

// 8. Risk/Compliance Checks
export const riskCheckStep = createStep({
  id: 'riskCheck',
  description: 'Validates proposed trades against risk/compliance rules',
  inputSchema: z.object({
    ethDecision: z.string(),
    solDecision: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
/*     portfolio: z.any(), */
    ethSummary: z.string(),
    solSummary: z.string(),
/*     ethIndicators: z.any(),
    solIndicators: z.any(), */
    balances: z.any(),
    trades: z.any(),
    portfolioSummary: z.string(),
  }),
  outputSchema: z.object({
    ethDecision: z.string(),
    solDecision: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
/*     portfolio: z.any(), */
    ethSummary: z.string(),
    solSummary: z.string(),
/*     ethIndicators: z.any(),
    solIndicators: z.any(), */
    balances: z.any(),
    trades: z.any(),
    portfolioSummary: z.string(),
    approvedEthTrade: z.any(),
    approvedSolTrade: z.any(),
  }),
  execute: async ({ inputData }) => {
    function parseDecision(decision: string) {
      const [action, amount, reasoning, risk] = decision.split('|').map(s => s.trim());
      return { action, amount, reasoning, risk };
    }
    const eth = parseDecision(inputData.ethDecision || '');
    const sol = parseDecision(inputData.solDecision || '');
    function approve(trade: any) {
      if (!trade.action || trade.action === 'HOLD' || trade.action === 'EXIT') return null;
      const amt = parseFloat(trade.amount.replace('$', ''));
      if (isNaN(amt) || amt > inputData.availableCash || amt <= 0) return null;
      return trade;
    }
    return {
      ...inputData,
      approvedEthTrade: approve(eth),
      approvedSolTrade: approve(sol),
    };
  },
});

// 9. Trade Execution
export const tradeExecutionStep = createStep({
  id: 'tradeExecution',
  description: 'Executes approved trades via Recall API',
  inputSchema: z.object({
    approvedEthTrade: z.any(),
    approvedSolTrade: z.any(),
    ethDecision: z.string(),
    solDecision: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
/*     portfolio: z.any(), */
    ethSummary: z.string(),
    solSummary: z.string(),
/*     ethIndicators: z.any(),
    solIndicators: z.any(), */
    balances: z.any(),
    trades: z.any(),
    portfolioSummary: z.string(),
  }),
  outputSchema: z.object({
    approvedEthTrade: z.any(),
    approvedSolTrade: z.any(),
    ethDecision: z.string(),
    solDecision: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
/*     portfolio: z.any(), */
    ethSummary: z.string(),
    solSummary: z.string(),
/*     ethIndicators: z.any(),
    solIndicators: z.any(), */
    balances: z.any(),
    trades: z.any(),
    portfolioSummary: z.string(),
    ethTradeResult: z.any(),
    solTradeResult: z.any(),
  }),
  execute: async ({ inputData, runtimeContext }) => {
    async function exec(trade: any, pair: 'ETH' | 'SOL') {
      if (!trade || !executeRecallTrade || !executeRecallTrade.execute) return null;
      const fromToken = trade.action === 'BUY' ? 'USDC' : pair;
      const toToken = trade.action === 'BUY' ? pair : 'USDC';
      const amount = trade.amount.replace('$', '').trim();
      const reason = `LLM Decision: ${trade.reasoning}`;
      try {
        return await executeRecallTrade.execute({
          context: { fromToken, toToken, amount, reason },
          runtimeContext,
        });
      } catch (e) {
        return { error: String(e) };
      }
    }
    const ethTradeResult = await exec(inputData.approvedEthTrade, 'ETH');
    const solTradeResult = await exec(inputData.approvedSolTrade, 'SOL');
    return {
      ...inputData,
      ethTradeResult,
      solTradeResult,
    };
  },
});

// 10. Logging & Monitoring
export const loggingStep = createStep({
  id: 'logging',
  description: 'Logs all decisions, trades, and errors',
  inputSchema: z.object({
    ethTradeResult: z.any(),
    solTradeResult: z.any(),
    approvedEthTrade: z.any(),
    approvedSolTrade: z.any(),
    ethDecision: z.string(),
    solDecision: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
/*     portfolio: z.any(), */
    ethSummary: z.string(),
    solSummary: z.string(),
    ethIndicators: z.any(),
    solIndicators: z.any(),
    balances: z.any(),
    trades: z.any(),
    portfolioSummary: z.string(),
  }),
  outputSchema: z.object({
    ethTradeResult: z.any(),
    solTradeResult: z.any(),
    approvedEthTrade: z.any(),
    approvedSolTrade: z.any(),
    ethDecision: z.string(),
    solDecision: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
/*     portfolio: z.any(), */
    ethSummary: z.string(),
    solSummary: z.string(),
/*     ethIndicators: z.any(),
    solIndicators: z.any(), */
    balances: z.any(),
    trades: z.any(),
    portfolioSummary: z.string(),
    logId: z.string(),
  }),
  execute: async ({ inputData }) => {
    return {
      ...inputData,
      logId: `log_${Date.now()}`,
    };
  },
});

// 11. Error Handling & Circuit Breakers
export const errorHandlingStep = createStep({
  id: 'errorHandling',
  description: 'Handles errors and triggers circuit breakers if needed',
  inputSchema: z.object({
    logId: z.string(),
    ethTradeResult: z.any(),
    solTradeResult: z.any(),
    approvedEthTrade: z.any(),
    approvedSolTrade: z.any(),
    ethDecision: z.string(),
    solDecision: z.string(),
    openPositions: z.any(),
    availableCash: z.number(),
/*     portfolio: z.any(), */ 
    ethSummary: z.string(),
    solSummary: z.string(),
/*       ethIndicators: z.any(),
      solIndicators: z.any(), */
    balances: z.any(),
    trades: z.any(),
    portfolioSummary: z.string(),
  }),
  outputSchema: z.object({
    status: z.string(),
  }),
  execute: async ({ inputData }) => {
    return { status: 'ok' };
  },
});

// Assemble the workflow (chain only the first two steps for now to avoid schema mismatch)
export const tradingWorkflow = createWorkflow({
  id: 'eth-sol-trading-workflow',
  inputSchema: z.object({}),
  outputSchema: z.object({
    status: z.string(),
  }),
  steps: [
    fetchMarketDataStep,
    calculateIndicatorsStep,
    formatMarketSummaryStep,
    fetchPortfolioStep,
    formatPortfolioStep,
    ethTradingDecisionStep,
    solTradingDecisionStep,
    riskCheckStep,
    tradeExecutionStep,
    loggingStep,
    errorHandlingStep,
  ],
})
  .then(fetchMarketDataStep)
  .then(calculateIndicatorsStep)
  .then(formatMarketSummaryStep)
  .then(fetchPortfolioStep)
  .then(formatPortfolioStep)
  .then(ethTradingDecisionStep)
  .then(solTradingDecisionStep)
  .then(riskCheckStep)
  .then(tradeExecutionStep)
  .then(loggingStep)
  .then(errorHandlingStep)
  .commit(); 

