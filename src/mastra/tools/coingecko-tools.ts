import { createTool } from "@mastra/core/tools";
import { z } from "zod";

export const searchCryptoCoins = createTool({
  id: "Search crypto coins",
  inputSchema: z.object({ keyword: z.string() }),
  description: "Search all available crypto coins by a keyword",
  execute: async ({ context }) => {
    const coinListUrl = `https://api.coingecko.com/api/v3/coins/list`;

    const options = {
      method: "GET",
      headers: {
        accept: "application/json",
        "x-cg-demo-api-key": process.env.COINGECKO_API_KEY!,
      },
    };

    const response = await fetch(coinListUrl, options);
    const data = await response.json();

    // First try to find an exact match.
    const exactMatch = data.find(
      (coin: any) => coin.name.toLowerCase() === context.keyword.toLowerCase()
    );

    if (exactMatch) {
      console.log("searchCryptoCoins exactMatch", exactMatch);
      return exactMatch;
    }

    // If no exact match is found, return first coin that contains the keyword.
    const coin = data.filter((coin: any) =>
      coin.name.toLowerCase().includes(context.keyword.toLowerCase())
    );

    if (coin.length >= 0) {
      console.log("searchCryptoCoins containsMatch", coin[0]);
      return coin[0];
    }

    return null;
  },
});

export const getCryptoPrice = createTool({
  id: "Get crypto price by id",
  inputSchema: z.object({ id: z.string() }),
  description: "Get crypto price by id",
  execute: async ({ context: { id } }) => {
    console.log("getCryptoPrice for", id);
    const coinListUrl = `https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=${id}`;

    const options = {
      method: "GET",
      headers: {
        accept: "application/json",
        "x-cg-demo-api-key": process.env.COINGECKO_API_KEY!,
      },
    };

    const response = await fetch(coinListUrl, options);
    const data = await response.json();

    if (data.length === 0) {
      return null;
    }

    return data[0];
  },
});

export const getHistoricalCryptoPrices = createTool({
  id: "Get historical crypto prices for use in a chart",
  inputSchema: z.object({ id: z.string(), days: z.number() }),
  description: "Get historical crypto prices for use in a chart, now includes volume as well.",
  execute: async ({ context: { id, days } }) => {
    console.log("getHistoricalCryptoPrices for", id);
    const url = `https://api.coingecko.com/api/v3/coins/${id}/market_chart?vs_currency=usd&days=${days}`;

    const options = {
      method: "GET",
      headers: {
        accept: "application/json",
        "x-cg-demo-api-key": process.env.COINGECKO_API_KEY!,
      },
    };

    const response = await fetch(url, options);
    const data = await response.json();

    // Patch: include volume from total_volumes
    const prices = data.prices || [];
    const volumes = data.total_volumes || [];
    // Match price and volume by timestamp
    return prices.map((priceArr: number[], i: number) => {
      const timestamp = priceArr[0];
      const price = priceArr[1];
      // Find matching volume by timestamp (may not be exact, so fallback to same index)
      let volume = 0;
      if (volumes[i] && volumes[i][0] === timestamp) {
        volume = volumes[i][1];
      } else if (volumes[i]) {
        volume = volumes[i][1];
      }
      return { timestamp, price, volume };
    });
  },
});
