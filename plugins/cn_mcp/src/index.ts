import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { getCnNews, getCnGlobalNews } from "./tools/news.js";
import { getCnDragonTiger, getCnDragonTigerStats } from "./tools/dragon-tiger.js";
import { getCnShareholderChanges } from "./tools/shareholder.js";
import { getCnStockInfo } from "./tools/stock-info.js";
import { getHkStockInfo } from "./tools/hk-stock-info.js";
import { getHkStockConnect } from "./tools/hk-stock-connect.js";
import { getHkHotRank } from "./tools/hk-hot-rank.js";
import { getCnStockQuote, getHkStockQuote } from "./tools/quote.js";

const server = new McpServer({
  name: "cn",
  version: "0.1.0",
});

// --- CN News ---
server.registerTool(
  "get_cn_news",
  {
    description: "Get company-specific news for a Chinese A-share stock",
    inputSchema: {
      symbol: z.string().describe("Ticker symbol (e.g. 600519.SS or 600519)"),
      limit: z.number().optional().default(20).describe("Max articles to return"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnNews(params) }],
  })
);

// --- CN Global News ---
server.registerTool(
  "get_cn_global_news",
  {
    description: "Get macro / A-share global news",
    inputSchema: {
      limit: z.number().optional().default(20).describe("Max articles to return"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnGlobalNews(params) }],
  })
);

// --- CN Dragon Tiger ---
server.registerTool(
  "get_cn_dragon_tiger",
  {
    description: "Get Dragon Tiger (龙虎榜) list details for a specific stock within a date range",
    inputSchema: {
      symbol: z.string().describe("Ticker symbol (e.g. 600519.SS or 600519)"),
      start_date: z.string().describe("Start date in YYYYMMDD format"),
      end_date: z.string().describe("End date in YYYYMMDD format"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnDragonTiger(params) }],
  })
);

// --- CN Dragon Tiger Stats ---
server.registerTool(
  "get_cn_dragon_tiger_stats",
  {
    description: "Get aggregated Dragon Tiger (龙虎榜) statistics for a time period",
    inputSchema: {
      period: z.string().optional().default("近一月").describe("Period: 近一月 / 近三月 / 近六月 / 近一年"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnDragonTigerStats(params) }],
  })
);

// --- CN Shareholder Changes ---
server.registerTool(
  "get_cn_shareholder_changes",
  {
    description: "Get top-10 shareholders and recent shareholder changes for a Chinese A-share stock",
    inputSchema: {
      symbol: z.string().describe("Ticker symbol (e.g. 600519.SS or 600519)"),
      date: z.string().describe("Report date in YYYYMMDD format"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnShareholderChanges(params) }],
  })
);

// --- CN Stock Info ---
server.registerTool(
  "get_cn_stock_info",
  {
    description: "Get basic information for a Chinese A-share stock (profile, listing date, market cap, etc.)",
    inputSchema: {
      symbol: z.string().describe("Ticker symbol (e.g. 600519.SS or 600519)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnStockInfo(params) }],
  })
);

// --- HK Stock Info ---
server.registerTool(
  "get_hk_stock_info",
  {
    description: "Get basic information for a Hong Kong stock (company profile, listing info, financial indicators)",
    inputSchema: {
      symbol: z.string().describe("HK stock code (e.g. 00700, 0700.HK, or 700)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getHkStockInfo(params) }],
  })
);

// --- HK Stock Connect ---
server.registerTool(
  "get_hk_stock_connect",
  {
    description: "Get Stock Connect (港股通) southbound holding data and trend for a Hong Kong stock",
    inputSchema: {
      symbol: z.string().describe("HK stock code (e.g. 00700, 0700.HK, or 700)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getHkStockConnect(params) }],
  })
);

// --- HK Hot Rank ---
server.registerTool(
  "get_hk_hot_rank",
  {
    description: "Get Hong Kong stock popularity / hot rank. Without symbol: top-20 hottest HK stocks. With symbol: historical rank trend for that stock.",
    inputSchema: {
      symbol: z.string().optional().describe("HK stock code (optional — omit for overall top-20 ranking)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getHkHotRank(params) }],
  })
);

// --- CN Stock Quote ---
server.registerTool(
  "get_cn_stock_quote",
  {
    description: "Get A-share realtime quote with 5-level order book (latest price, bid/ask 1-5, volume, turnover). Delay ~3s.",
    inputSchema: {
      symbol: z.string().describe("Ticker symbol (e.g. 600519.SS or 600519)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getCnStockQuote(params) }],
  })
);

// --- HK Stock Quote ---
server.registerTool(
  "get_hk_stock_quote",
  {
    description: "Get HK stock near-realtime quote via 1-min K-line last bar. Latest price + today's OHLC + volume. Delay ~0-60s. Note: 5-level order book requires paid LV1 feed.",
    inputSchema: {
      symbol: z.string().describe("HK stock code (e.g. 00700, 0700.HK, or 700)"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await getHkStockQuote(params) }],
  })
);

// --- Start server ---
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
