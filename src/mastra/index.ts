import { Mastra } from "@mastra/core/mastra";
import { PinoLogger } from "@mastra/loggers";
import { LibSQLStore } from "@mastra/libsql";
import { weatherWorkflow } from "./workflows/weather-workflow";
import { tradingWorkflow } from "./workflows/trading-workflow";
import { weatherAgent } from "./agents/weather-agent";
import { tradingAgent } from "./agents/trading-agent";

export const mastra = new Mastra({
  workflows: { weatherWorkflow, tradingWorkflow },
  agents: {
    weatherAgent,
    tradingAgent,
  },
  storage: new LibSQLStore({
    // stores telemetry, evals, ... into memory storage, if it needs to persist, change to file:../mastra.db
    url: ":memory:",
  }),
  logger: new PinoLogger({
    name: 'Mastra',
    level: 'info',
  }),
});
