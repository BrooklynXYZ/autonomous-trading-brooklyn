import { createTool } from "@mastra/core/tools";
import { z } from "zod";

/**
 * CoinMarketCap API Tools
 * 
 * API Plan Limitations (Basic Plan):
 * - Historical data endpoints require higher subscription
 * - Multiple currency conversions limited to 1 convert option
 * - Rate limits apply based on plan level
 * 
 * Available endpoints with Basic plan:
 * - /v1/cryptocurrency/map (search)
 * - /v2/cryptocurrency/quotes/latest (current prices)
 */

export const searchCryptoCoins = createTool({
  id: "Search crypto coins",
  inputSchema: z.object({ keyword: z.string() }),
  description: "Search all available crypto coins by a keyword using CoinMarketCap API v1",
  execute: async ({ context }) => {
    const coinListUrl = `https://pro-api.coinmarketcap.com/v1/cryptocurrency/map`;

    const options = {
      method: "GET",
      headers: {
        accept: "application/json",
        "X-CMC_PRO_API_KEY": process.env.COINMARKETCAP_API_KEY!,
      },
    };

    const response = await fetch(coinListUrl, options);
    const data = await response.json();

    if (!data.data) {
      return null;
    }

    // First try to find an exact match.
    const exactMatch = data.data.find(
      (coin: any) => coin.name.toLowerCase() === context.keyword.toLowerCase()
    );

    if (exactMatch) {
      console.log("searchCryptoCoins exactMatch", exactMatch);
      return exactMatch;
    }

    // If no exact match is found, return first coin that contains the keyword.
    const coin = data.data.filter((coin: any) =>
      coin.name.toLowerCase().includes(context.keyword.toLowerCase())
    );

    if (coin.length > 0) {
      console.log("searchCryptoCoins containsMatch", coin[0]);
      return coin[0];
    }

    return null;
  },
});

export const getCryptoPrice = createTool({
  id: "Get crypto price by id",
  inputSchema: z.object({ 
    id: z.string().optional(),
    slug: z.string().optional(),
    symbol: z.string().optional(),
    convert: z.string().optional(),
    aux: z.string().optional(),
    skip_invalid: z.boolean().optional()
  }),
  description: "Get crypto price by id, slug, or symbol using CoinMarketCap API v2. Supports multiple currencies and auxiliary data.",
  execute: async ({ context }) => {
    const { id, slug, symbol, convert, aux, skip_invalid } = context;
    
    // Validate that at least one identifier is provided
    if (!id && !slug && !symbol) {
      throw new Error("At least one of id, slug, or symbol is required");
    }

    // Build query parameters
    const params = new URLSearchParams();
    if (id) params.append("id", id);
    if (slug) params.append("slug", slug);
    if (symbol) params.append("symbol", symbol);
    if (convert) params.append("convert", convert);
    if (aux) params.append("aux", aux);
    if (skip_invalid) params.append("skip_invalid", skip_invalid.toString());

    const url = `https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest?${params.toString()}`;
    console.log("getCryptoPrice for", { id, slug, symbol, convert });

    const options = {
      method: "GET",
      headers: {
        accept: "application/json",
        "X-CMC_PRO_API_KEY": process.env.COINMARKETCAP_API_KEY!,
      },
    };

    const response = await fetch(url, options);
    const data = await response.json();

    if (!data.data || Object.keys(data.data).length === 0) {
      return null;
    }

    // If single ID was requested, return that specific coin
    if (id && data.data[id]) {
      return data.data[id];
    }

    // Otherwise return all results
    return data.data;
  },
});

export const getHistoricalCryptoPrices = createTool({
  id: "Get historical crypto prices for use in a chart",
  inputSchema: z.object({ id: z.string(), days: z.number() }),
  description: "Get historical crypto prices for use in a chart using CoinMarketCap API (Note: Requires higher subscription plan)",
  execute: async ({ context: { id, days } }) => {
    console.log("getHistoricalCryptoPrices for", id);
    
    // Try v2 first, then fallback to v1
    const endpoints = [
      `https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/historical?id=${id}&time_period=daily&count=${days}`,
      `https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/historical?id=${id}&time_period=daily&count=${days}`
    ];

    const options = {
      method: "GET",
      headers: {
        accept: "application/json",
        "X-CMC_PRO_API_KEY": process.env.COINMARKETCAP_API_KEY!,
      },
    };

    for (const url of endpoints) {
      try {
        const response = await fetch(url, options);
        const data = await response.json();

        if (data.status?.error_code === 1006) {
          console.log(`Historical data not available with current plan: ${data.status.error_message}`);
          continue;
        }

        if (data.data && data.data.quotes) {
          return data.data.quotes.map((quote: any) => ({
            timestamp: new Date(quote.timestamp).getTime(),
            price: quote.quote.USD.price,
          }));
        }
      } catch (error) {
        console.log(`Error with endpoint ${url}:`, error);
        continue;
      }
    }

    // If no historical data is available, return current price as fallback
    console.log("Historical data not available, returning current price as fallback");
    const currentPriceResponse = await fetch(`https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest?id=${id}`, options);
    const currentPriceData = await currentPriceResponse.json();
    
    if (currentPriceData.data && currentPriceData.data[id]) {
      const currentPrice = currentPriceData.data[id].quote.USD.price;
      const now = Date.now();
      return [{
        timestamp: now,
        price: currentPrice,
      }];
    }

    return [];
  },
}); 

export const getCryptoPriceMultiCurrency = createTool({
  id: "Get crypto price with multiple currency conversions",
  inputSchema: z.object({ 
    id: z.string().optional(),
    slug: z.string().optional(),
    symbol: z.string().optional(),
    convert: z.string(),
    aux: z.string().optional()
  }),
  description: "Get crypto price with multiple currency conversions. Note: Basic plan limited to 1 convert option. Example: convert='USD' or convert='EUR'",
  execute: async ({ context }) => {
    const { id, slug, symbol, convert, aux } = context;
    
    // Validate that at least one identifier is provided
    if (!id && !slug && !symbol) {
      throw new Error("At least one of id, slug, or symbol is required");
    }

    // Build query parameters
    const params = new URLSearchParams();
    if (id) params.append("id", id);
    if (slug) params.append("slug", slug);
    if (symbol) params.append("symbol", symbol);
    params.append("convert", convert);
    if (aux) params.append("aux", aux);

    const url = `https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest?${params.toString()}`;
    console.log("getCryptoPriceMultiCurrency for", { id, slug, symbol, convert });

    const options = {
      method: "GET",
      headers: {
        accept: "application/json",
        "X-CMC_PRO_API_KEY": process.env.COINMARKETCAP_API_KEY!,
      },
    };

    const response = await fetch(url, options);
    const data = await response.json();

    if (!data.data || Object.keys(data.data).length === 0) {
      return null;
    }

    return data.data;
  },
}); 