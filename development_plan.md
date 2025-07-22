# Development Plan: LLM-Powered Trading Agent (ETH/SOL) with Mastra

## Overview
This document tracks the full implementation of an LLM-driven trading agent for ETH and SOL pairs using the Mastra framework and Recall Network. It is structured as a checklist for systematic progress, with sections for TODOs, issues, and deployment notes.

---

## Phase 1: Infrastructure Setup

- [x] **Initialize Mastra Project**
  - [x] Set up project structure (src/mastra/agents, tools, workflows)
  - [x] Install dependencies (Mastra, Recall SDK, CoinGecko/CMC clients)
  - [x] Configure TypeScript and project settings

- [x] **Configure Recall MCP Server**
  - [x] Obtain and store Recall MCP API credentials
  - [x] Set up connection logic in tools/recall-tools.ts and mcp.ts

- [x] **Build Market Data Tools**
  - [x] Implement CoinGecko/CMC integration (tools/coingecko-tools.ts, coinmarketcap-tools.ts)
  - [ ] Add technical indicator calculations (RSI, EMA, Bollinger Bands) **[TODO]**
  - [ ] Create data formatting utilities for LLM input (AnalysisFormatter) **[TODO]**

- [x] **Test Data Fetching & Formatting**
  - [x] Validate data retrieval for ETH/SOL (1H, 4H candles)
  - [ ] Test indicator calculations and LLM formatting **[TODO]**

---

## Phase 2: Strategy Implementation

- [x] **Trading Workflow Scaffold**
  - [x] Create trading-workflow.ts with all step definitions and structure
  - [ ] Implement logic for each workflow step (see below)

- [ ] **Implement Workflow Step Logic**
  - [ ] Fetch Market Data: Integrate CoinGecko/CMC tools
  - [ ] Calculate Technical Indicators: Implement RSI, EMA, Bollinger Bands, volume ratio, price change
  - [ ] Format Market Summary: Implement LLM summary formatting
  - [ ] Fetch Portfolio State: Integrate Recall API for portfolio, balances, trades
  - [ ] Format Portfolio State: Implement portfolio summary and risk metrics
  - [ ] ETH Trading Decision: Call trading agent with ETH prompt
  - [ ] SOL Trading Decision: Call trading agent with SOL prompt
  - [ ] Risk/Compliance Checks: Validate trades against risk/compliance rules
  - [ ] Trade Execution: Execute trades via Recall API
  - [ ] Logging & Monitoring: Log all decisions, trades, and errors
  - [ ] Error Handling & Circuit Breakers: Handle errors and trigger circuit breakers if needed

- [ ] **Agent & Prompt Engineering**
  - [ ] Specialize trading agent for ETH/SOL, add advanced prompt structure (ACTION|AMOUNT|REASONING|RISK_LEVEL) **[DONE]**
  - [ ] Integrate Groq Llama 4 model (already using Groq, update if needed) **[IN PROGRESS]**
  - [ ] Fine-tune prompts for ETH and SOL **[TODO]**

- [ ] **Error Handling & Position Sizing**
  - [ ] Add error handling for API failures and edge cases **[TODO]**
  - [ ] Implement position sizing logic (risk management, max allocation) **[TODO]**

---

## Phase 3: Testing & Optimization

- [ ] **Paper Trading Validation**
  - [ ] Run workflow in paper trading mode **[TODO]**
  - [ ] Log and review trade decisions and executions **[TODO]**

- [ ] **Prompt Refinement**
  - [ ] Analyze LLM outputs for consistency and quality **[TODO]**
  - [ ] Adjust prompts and agent config as needed **[TODO]**

- [ ] **Performance Monitoring**
  - [ ] Set up logging for trades, errors, and agent decisions **[TODO]**
  - [ ] Monitor risk metrics (drawdown, win rate, Sharpe ratio) **[TODO]**

- [ ] **Risk Management Validation**
  - [ ] Test position limits, daily loss limits, and circuit breakers **[TODO]**
  - [ ] Simulate API failures and volatility events **[TODO]**

---

## Deployment & Documentation

- [ ] **Deployment**
  - [ ] Prepare deployment scripts/configs **[TODO]**
  - [ ] Document environment variables and secrets **[TODO]**
  - [ ] Deploy to production or cloud environment **[TODO]**

- [ ] **Developer Documentation**
  - [ ] Add code comments and usage docs **[TODO]**
  - [ ] Update README.md with setup and usage instructions **[TODO]**

---

## Issues & Notes
- [ ] Track any blockers, bugs, or design changes here
  - [x] Trading workflow file and step structure are now in place (trading-workflow.ts)
  - [ ] Technical indicator utilities (RSI, EMA, Bollinger Bands) missing
  - [ ] No analysis formatter for LLM input
  - [ ] Workflow step logic needs implementation

---

## API Keys & Credentials Required

- [x] **Recall MCP API Key**: For portfolio, trade, and balance management
- [x] **CoinGecko API Key** (if using paid tier; public endpoints may suffice)
- [x] **CoinMarketCap API Key**: For alternative or backup market data
- [x] **Groq API Key**: For Llama 4 model access (replace OpenAI key)
- [ ] **OpenAI API Key** (optional, for fallback or comparison)
- [ ] **Any Exchange API Keys** (if executing real trades, e.g., Binance, Coinbase)

---

## Progress Checklist
- [x] Phase 1: Infrastructure Setup (except indicators/formatting)
- [x] Trading Workflow Scaffold
- [ ] Phase 2: Strategy Implementation (step logic)
- [ ] Phase 3: Testing & Optimization
- [ ] Deployment & Documentation

---

*Update this file as you complete tasks or encounter new requirements.* 