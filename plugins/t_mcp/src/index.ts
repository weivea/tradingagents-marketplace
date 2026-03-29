import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { getStockData } from "./tools/stock-data.js";
import { getIndicators } from "./tools/indicators.js";
import {
  getFundamentals,
  getBalanceSheet,
  getCashflow,
  getIncomeStatement,
} from "./tools/fundamentals.js";
import {
  getNews,
  getGlobalNews,
  getInsiderTransactions,
} from "./tools/news.js";

const server = new McpServer({
  name: "ta",
  version: "0.1.0",
});

// --- Stock Data ---
server.registerTool(
  "get_stock_data",
  {
    description: "Retrieve OHLCV stock price data for a given ticker symbol and date range",
    inputSchema: {
      symbol: z.string().describe("Ticker symbol (e.g. AAPL, NVDA, TSM)"),
      start_date: z.string().describe("Start date in yyyy-mm-dd format"),
      end_date: z.string().describe("End date in yyyy-mm-dd format"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getStockData(params) }],
  })
);

// --- Technical Indicators ---
server.registerTool(
  "get_indicators",
  {
    description: "Compute a technical indicator for a ticker. Supported: close_50_sma, close_200_sma, close_10_ema, macd, macds, macdh, rsi, boll, boll_ub, boll_lb, atr, vwma",
    inputSchema: {
      symbol: z.string().describe("Ticker symbol"),
      indicator: z.string().describe("Indicator name (e.g. rsi, macd, close_50_sma)"),
      curr_date: z.string().describe("Current/end date in yyyy-mm-dd format"),
      look_back_days: z.number().optional().default(365).describe("Days of history to use for calculation"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getIndicators(params) }],
  })
);

// --- Fundamentals ---
server.registerTool(
  "get_fundamentals",
  {
    description: "Get comprehensive company fundamentals: profile, financial data, key statistics",
    inputSchema: {
      ticker: z.string().describe("Ticker symbol"),
      curr_date: z.string().optional().describe("Reference date (optional)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getFundamentals(params) }],
  })
);

server.registerTool(
  "get_balance_sheet",
  {
    description: "Get balance sheet data for a company (quarterly or annual)",
    inputSchema: {
      ticker: z.string().describe("Ticker symbol"),
      freq: z.enum(["quarterly", "annual"]).optional().default("quarterly").describe("Frequency"),
      curr_date: z.string().optional().describe("Reference date (optional)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getBalanceSheet(params) }],
  })
);

server.registerTool(
  "get_cashflow",
  {
    description: "Get cash flow statement for a company (quarterly or annual)",
    inputSchema: {
      ticker: z.string().describe("Ticker symbol"),
      freq: z.enum(["quarterly", "annual"]).optional().default("quarterly").describe("Frequency"),
      curr_date: z.string().optional().describe("Reference date (optional)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCashflow(params) }],
  })
);

server.registerTool(
  "get_income_statement",
  {
    description: "Get income statement for a company (quarterly or annual)",
    inputSchema: {
      ticker: z.string().describe("Ticker symbol"),
      freq: z.enum(["quarterly", "annual"]).optional().default("quarterly").describe("Frequency"),
      curr_date: z.string().optional().describe("Reference date (optional)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getIncomeStatement(params) }],
  })
);

// --- News ---
server.registerTool(
  "get_news",
  {
    description: "Get company-specific news for a ticker within a date range",
    inputSchema: {
      ticker: z.string().describe("Ticker symbol"),
      start_date: z.string().describe("Start date in yyyy-mm-dd format"),
      end_date: z.string().describe("End date in yyyy-mm-dd format"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getNews(params) }],
  })
);

server.registerTool(
  "get_global_news",
  {
    description: "Get global macroeconomic and market news",
    inputSchema: {
      curr_date: z.string().describe("Current date in yyyy-mm-dd format"),
      look_back_days: z.number().optional().default(7).describe("Days to look back"),
      limit: z.number().optional().default(10).describe("Max articles to return"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getGlobalNews(params) }],
  })
);

server.registerTool(
  "get_insider_transactions",
  {
    description: "Get insider trading transactions and holdings for a company",
    inputSchema: {
      ticker: z.string().describe("Ticker symbol"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getInsiderTransactions(params) }],
  })
);

// --- Start server ---
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
