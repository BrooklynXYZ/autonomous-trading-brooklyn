# Ai trading agent 

- we're making an Ai trading agent for recall.network trading competition....
- we need to first make the ai bot's logic to make profit (you wrote the plan)
- then we need to integrate the recall endpoints and start doing the actuall trades....
- there's 4 endpoints that are only usefull for the bot  
  - /api/trade/execute ==> Make an actuall trade (need to specify pairs and amount) (must use !!!)
  - /api/agent/trades ==> display all trades made by this agent (optional for you to use... you can skip if you dont have a use for it)
  - /api/agent/balances ==> display all tokens/holdings with chain/symbol/date created (optional for you to use... you can skip if you dont have a use for it)
  - /api/agent/portfolio ==> display all tokens + amount + real price (optional for you to use... you can skip if you dont have a use for it)

# API output Sample

### making a trade /api/trade/execute
```bash
❯ curl -X POST "https://api.sandbox.competitions.recall.network/api/trade/execute" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 06f9c24ca6209d7f_be021cdd05a09516" \
  -d '{
    "fromToken": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "toToken": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "amount": "100",
    "reason": "Trading 100 USDC to Weth Eth Mainnet to verify my Recall developer account"
  }' | jq
{
    "success": true,
    "transaction": {
        "id": "eb69dc9c-29fd-4005-b3a3-ed5664cabd48",
        "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
        "competitionId": "104e8ced-e2df-4b82-92e7-e62229b39fe8",
        "fromToken": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "toToken": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "fromAmount": 100,
        "toAmount": 0.026576389836311613,
        "price": 0.0002657638983631161,
        "tradeAmountUsd": 99.94,
        "toTokenSymbol": "WETH",
        "fromTokenSymbol": "USDC",
        "success": true,
        "error": null,
        "reason": "Trading 100 USDC to Weth Eth Mainnet to verify my Recall developer account",
        "timestamp": "2025-07-21T23:47:15.984Z",
        "fromChain": "evm",
        "toChain": "evm",
        "fromSpecificChain": "eth",
        "toSpecificChain": "eth"
    }
}
```
Request body as per the docs:
```text
Request Body type: application/json

fromToken 
string
Required - Token address to sell

toToken
string
Required - Token address to buy

amount 
string
Required - Amount of fromToken to trade

reason
string
Required - Reason for executing this trade

slippageTolerance
string
Optional - slippage tolerance in percentage

fromChain
string
Optional - Blockchain type for fromToken

fromSpecificChain
string
Optional - Specific chain for fromToken

toChain
string
Optional - Blockchain type for toToken

toSpecificChain
string
Optional - Specific chain for toToken
```

TS ready Response Type from the docs:
```ts
export interface Response {
  /**
   * Whether the trade was successfully executed
   */
  success?: boolean;
  transaction?: {
    /**
     * Unique trade ID
     */
    id?: string;
    /**
     * Agent ID that executed the trade
     */
    agentId?: string;
    /**
     * ID of the competition this trade is part of
     */
    competitionId?: string;
    /**
     * Token address that was sold
     */
    fromToken?: string;
    /**
     * Token address that was bought
     */
    toToken?: string;
    /**
     * Amount of fromToken that was sold
     */
    fromAmount?: number;
    /**
     * Amount of toToken that was received
     */
    toAmount?: number;
    /**
     * Price at which the trade was executed
     */
    price?: number;
    /**
     * Whether the trade was successfully completed
     */
    success?: boolean;
    /**
     * Error message if the trade failed
     */
    error?: string | null;
    /**
     * Reason provided for executing the trade
     */
    reason?: string;
    /**
     * The USD value of the trade at execution time
     */
    tradeAmountUsd?: number;
    /**
     * Timestamp of when the trade was executed
     */
    timestamp?: string;
    /**
     * Blockchain type of the source token
     */
    fromChain?: string;
    /**
     * Blockchain type of the destination token
     */
    toChain?: string;
    /**
     * Specific chain for the source token
     */
    fromSpecificChain?: string;
    /**
     * Specific chain for the destination token
     */
    toSpecificChain?: string;
    /**
     * Symbol of the destination token
     */
    toTokenSymbol?: string;
    /**
     * Symbol of the source token
     */
    fromTokenSymbol?: string;
  };
}
```
### checking trades /api/agent/trades
```bash
❯ curl -X GET "https://api.sandbox.competitions.recall.network/api/agent/trades" -H "Authorization: Bearer 06f9c24ca6209d7f_be021cdd05a09516" | jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:--   0     0    0     0    0     0      0      0 --:--:-- --:--:-- 100   725  100   725    0     0   1461      0 --:--:-- --:--:-- --:--:--  1461
{
  "success": true,
  "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
  "trades": [
    {
      "id": "eb69dc9c-29fd-4005-b3a3-ed5664cabd48",
      "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
      "competitionId": "104e8ced-e2df-4b82-92e7-e62229b39fe8",
      "fromToken": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "toToken": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
      "fromAmount": 100,
      "toAmount": 0.026576389836311613,
      "price": 0.0002657638983631161,
      "tradeAmountUsd": 99.94,
      "toTokenSymbol": "WETH",
      "fromTokenSymbol": "USDC",
      "success": true,
      "error": null,
      "reason": "Trading 100 USDC to Weth Eth Mainnet to verify my Recall developer account",
      "timestamp": "2025-07-21T23:47:15.984Z",
      "fromChain": "evm",
      "toChain": "evm",
      "fromSpecificChain": "eth",
      "toSpecificChain": "eth"
    }
  ]
}
```
TS ready Response Type from the docs:
```ts
export interface Response {
  success?: boolean;
  agentId?: string;
  trades?: {
    id?: string;
    agentId?: string;
    competitionId?: string;
    /**
     * Source token address
     */
    fromToken?: string;
    /**
     * Destination token address
     */
    toToken?: string;
    /**
     * Amount traded from source token
     */
    fromAmount?: number;
    /**
     * Amount received in destination token
     */
    toAmount?: number;
    /**
     * Price at which the trade was executed
     */
    price?: number;
    /**
     * USD value of the trade at execution time
     */
    tradeAmountUsd?: number;
    /**
     * Symbol of the destination token
     */
    toTokenSymbol?: string;
    /**
     * Symbol of the source token
     */
    fromTokenSymbol?: string;
    /**
     * Whether the trade was successfully completed
     */
    success?: boolean;
    /**
     * Error message if the trade failed
     */
    error?: string | null;
    /**
     * Reason for the trade
     */
    reason?: string;
    /**
     * When the trade was executed
     */
    timestamp?: string;
    /**
     * Blockchain type of the source token
     */
    fromChain?: string;
    /**
     * Blockchain type of the destination token
     */
    toChain?: string;
    /**
     * Specific chain for the source token
     */
    fromSpecificChain?: string | null;
    /**
     * Specific chain for the destination token
     */
    toSpecificChain?: string | null;
  }[];
}
```

### Checking balances /api/agent/balances
```bash
❯ curl -X GET "https://api.sandbox.competitions.recall.network/api/agent/balances" \
  -H "Authorization: Bearer 06f9c24ca6209d7f_be021cdd05a09516" | jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  2254  100  2254    0     0   1454      0  0:00:01  0:00:01 --:--:--  1455
{
  "success": true,
  "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
  "balances": [
    {
      "id": 2084259,
      "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
      "tokenAddress": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "amount": 4900,
      "createdAt": "2025-07-19T22:55:04.628Z",
      "updatedAt": "2025-07-21T23:47:15.908Z",
      "specificChain": "eth",
      "symbol": "USDC",
      "chain": "evm"
    },
    {
      "id": 2084260,
      "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
      "tokenAddress": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
      "amount": 5000,
      "createdAt": "2025-07-19T22:55:04.628Z",
      "updatedAt": "2025-07-19T22:55:04.628Z",
      "specificChain": "polygon",
      "symbol": "USDC",
      "chain": "evm"
    },
    {
      "id": 2084261,
      "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
      "tokenAddress": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
      "amount": 5000,
      "createdAt": "2025-07-19T22:55:04.628Z",
      "updatedAt": "2025-07-19T22:55:04.628Z",
      "specificChain": "base",
      "symbol": "USDbC",
      "chain": "evm"
    },
    {
      "id": 2084262,
      "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
      "tokenAddress": "0xaf88d065e77c8cc2239327c5edb3a432268e5831",
      "amount": 5000,
      "createdAt": "2025-07-19T22:55:04.628Z",
      "updatedAt": "2025-07-19T22:55:04.628Z",
      "specificChain": "arbitrum",
      "symbol": "USDC",
      "chain": "evm"
    },
    {
      "id": 2084263,
      "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
      "tokenAddress": "0x7f5c764cbc14f9669b88837ca1490cca17c31607",
      "amount": 5000,
      "createdAt": "2025-07-19T22:55:04.628Z",
      "updatedAt": "2025-07-19T22:55:04.628Z",
      "specificChain": "optimism",
      "symbol": "USDC",
      "chain": "evm"
    },
    {
      "id": 2084264,
      "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
      "tokenAddress": "So11111111111111111111111111111111111111112",
      "amount": 10,
      "createdAt": "2025-07-19T22:55:04.628Z",
      "updatedAt": "2025-07-19T22:55:04.628Z",
      "specificChain": "svm",
      "symbol": "SOL",
      "chain": "svm"
    },
    {
      "id": 2084265,
      "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
      "tokenAddress": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
      "amount": 5000,
      "createdAt": "2025-07-19T22:55:04.628Z",
      "updatedAt": "2025-07-19T22:55:04.628Z",
      "specificChain": "svm",
      "symbol": "USDC",
      "chain": "svm"
    },
    {
      "id": 2087603,
      "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
      "tokenAddress": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
      "amount": 0.026576389836311613,
      "createdAt": "2025-07-21T23:47:15.958Z",
      "updatedAt": "2025-07-21T23:47:15.958Z",
      "specificChain": "eth",
      "symbol": "WETH",
      "chain": "evm"
    }
  ]
}
```
TS ready Response Type from the docs:
```ts
export interface Response {
  success?: boolean;
  agentId?: string;
  balances?: {
    tokenAddress?: string;
    amount?: number;
    symbol?: string;
    chain?: "evm" | "svm";
    specificChain?: string;
  }[];
}
```

### Checking portfolio /api/agent/portfolio
```bash
❯ curl -X GET "https://api.sandbox.competitions.recall.network/api/agent/portfolio" -H "Authorization: Bearer 06f9c24ca6209d7f_be021cdd05a09516"  | jq
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:-- --:--:-- 100  1308  100  1308    0     0   1940      0 --:--:-- --:--:-- --:--:--  1940
{
  "success": true,
  "agentId": "b2f21646-9479-4b7f-a8e8-2788806f5fa4",
  "totalValue": 31953.693368828328,
  "tokens": [
    {
      "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
      "amount": 4900,
      "price": 0.9994,
      "value": 4897.0599999999995,
      "chain": "evm",
      "symbol": "USDC"
    },
    {
      "token": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
      "amount": 5000,
      "price": 0.9996,
      "value": 4998,
      "chain": "evm",
      "symbol": "USDC"
    },
    {
      "token": "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA",
      "amount": 5000,
      "price": 1.00071,
      "value": 5003.55,
      "chain": "evm",
      "symbol": "USDbC"
    },
    {
      "token": "0xaf88d065e77c8cc2239327c5edb3a432268e5831",
      "amount": 5000,
      "price": 0.9993,
      "value": 4996.5,
      "chain": "evm",
      "symbol": "USDC"
    },
    {
      "token": "0x7f5c764cbc14f9669b88837ca1490cca17c31607",
      "amount": 5000,
      "price": 0.9994,
      "value": 4997,
      "chain": "evm",
      "symbol": "USDC"
    },
    {
      "token": "So11111111111111111111111111111111111111112",
      "amount": 10,
      "price": 196.47,
      "value": 1964.7,
      "chain": "svm",
      "specificChain": "svm",
      "symbol": "SOL"
    },
    {
      "token": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
      "amount": 5000,
      "price": 0.9993993609840485,
      "value": 4996.9968049202425,
      "chain": "svm",
      "specificChain": "svm",
      "symbol": "USDC"
    },
    {
      "token": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
      "amount": 0.026576389836311613,
      "price": 3758.47,
      "value": 99.8865639080821,
      "chain": "evm",
      "symbol": "WETH"
    }
  ],
  "snapshotTime": "2025-07-21T23:47:16.010Z",
  "source": "snapshot"
}
```
TS ready Response Type from the docs:
```ts
export interface Response {
  success?: boolean;
  agentId?: string;
  /**
   * Total portfolio value in USD
   */
  totalValue?: number;
  tokens?: {
    /**
     * Token address
     */
    token?: string;
    /**
     * Token amount
     */
    amount?: number;
    /**
     * Token price in USD
     */
    price?: number;
    /**
     * Token value in USD
     */
    value?: number;
    chain?: "evm" | "svm";
    specificChain?: string;
    symbol?: string;
  }[];
  /**
   * Data source (snapshot or live-calculation)
   */
  source?: "snapshot" | "live-calculation";
  /**
   * Time of snapshot (only present if source is snapshot)
   */
  snapshotTime?: string;
}
```


