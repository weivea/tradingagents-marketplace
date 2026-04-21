import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { callPython } from "./tools/call-python.js";

const server = new McpServer({ name: "paper_trading", version: "0.1.0" });

function textResult(text: string) {
  return { content: [{ type: "text" as const, text }] };
}

server.registerTool(
  "place_order",
  {
    description: "Place a paper-trading order (market/limit/stop). Market orders require ref_price.",
    inputSchema: {
      account_id: z.enum(["aggressive", "neutral", "conservative"]),
      symbol: z.string(),
      market: z.enum(["CN", "HK", "US"]),
      side: z.enum(["buy", "sell"]),
      qty: z.number().positive(),
      order_type: z.enum(["market", "limit", "stop"]),
      price: z.number().optional(),
      ref_price: z.number().optional(),
    },
  },
  async (p) => {
    const args = [
      "place-order",
      "--account-id", p.account_id,
      "--symbol", p.symbol,
      "--market", p.market,
      "--side", p.side,
      "--qty", String(p.qty),
      "--order-type", p.order_type,
    ];
    if (p.price !== undefined) args.push("--price", String(p.price));
    if (p.ref_price !== undefined) args.push("--ref-price", String(p.ref_price));
    return textResult(await callPython(args));
  }
);

server.registerTool(
  "cancel_order",
  {
    description: "Cancel a pending paper-trading order.",
    inputSchema: {
      account_id: z.enum(["aggressive", "neutral", "conservative"]),
      order_id: z.number().int(),
    },
  },
  async (p) =>
    textResult(await callPython([
      "cancel-order", "--account-id", p.account_id,
      "--order-id", String(p.order_id),
    ]))
);

server.registerTool(
  "tick_pending_orders",
  {
    description: "Settle T+1 CN buys and sweep pending limit/stop orders using the provided price map.",
    inputSchema: {
      account_id: z.enum(["aggressive", "neutral", "conservative"]),
      price_map: z.record(z.number()).optional(),
    },
  },
  async (p) => {
    const args = ["tick-pending-orders", "--account-id", p.account_id];
    if (p.price_map) args.push("--price-map", JSON.stringify(p.price_map));
    return textResult(await callPython(args));
  }
);

server.registerTool(
  "get_portfolio",
  {
    description: "Get cash + positions (optionally with current market values via price_map).",
    inputSchema: {
      account_id: z.enum(["aggressive", "neutral", "conservative"]),
      price_map: z.record(z.number()).optional(),
    },
  },
  async (p) => {
    const args = ["get-portfolio", "--account-id", p.account_id];
    if (p.price_map) args.push("--price-map", JSON.stringify(p.price_map));
    return textResult(await callPython(args));
  }
);

server.registerTool(
  "get_positions",
  {
    description: "List current positions for an account.",
    inputSchema: { account_id: z.enum(["aggressive", "neutral", "conservative"]) },
  },
  async (p) =>
    textResult(await callPython(["get-positions", "--account-id", p.account_id]))
);

server.registerTool(
  "get_cash",
  {
    description: "Return CNY/HKD/USD cash balances.",
    inputSchema: { account_id: z.enum(["aggressive", "neutral", "conservative"]) },
  },
  async (p) =>
    textResult(await callPython(["get-cash", "--account-id", p.account_id]))
);

server.registerTool(
  "get_pending_orders",
  {
    description: "List unfilled limit/stop orders.",
    inputSchema: { account_id: z.enum(["aggressive", "neutral", "conservative"]) },
  },
  async (p) =>
    textResult(await callPython(["get-pending-orders", "--account-id", p.account_id]))
);

server.registerTool(
  "get_order_history",
  {
    description: "Query order history by date range.",
    inputSchema: {
      account_id: z.enum(["aggressive", "neutral", "conservative"]),
      start_date: z.string().optional(),
      end_date: z.string().optional(),
    },
  },
  async (p) => {
    const args = ["get-order-history", "--account-id", p.account_id];
    if (p.start_date) args.push("--start-date", p.start_date);
    if (p.end_date) args.push("--end-date", p.end_date);
    return textResult(await callPython(args));
  }
);

server.registerTool(
  "get_pnl",
  {
    description: "Return realized (from filled orders) and unrealized (from price_map) PnL per currency.",
    inputSchema: {
      account_id: z.enum(["aggressive", "neutral", "conservative"]),
      date: z.string().optional(),
      price_map: z.record(z.number()).optional(),
    },
  },
  async (p) => {
    const args = ["get-pnl", "--account-id", p.account_id];
    if (p.date) args.push("--date", p.date);
    if (p.price_map) args.push("--price-map", JSON.stringify(p.price_map));
    return textResult(await callPython(args));
  }
);

server.registerTool(
  "append_journal",
  {
    description: "Append markdown to this account's daily journal.",
    inputSchema: {
      account_id: z.enum(["aggressive", "neutral", "conservative"]),
      date: z.string(),
      markdown: z.string(),
    },
  },
  async (p) =>
    textResult(await callPython([
      "append-journal", "--account-id", p.account_id,
      "--date", p.date, "--markdown", p.markdown,
    ]))
);

server.registerTool(
  "read_journal",
  {
    description: "Read the full markdown of an account's daily journal.",
    inputSchema: {
      account_id: z.enum(["aggressive", "neutral", "conservative"]),
      date: z.string(),
    },
  },
  async (p) =>
    textResult(await callPython([
      "read-journal", "--account-id", p.account_id, "--date", p.date,
    ]))
);

server.registerTool(
  "init_discussion",
  {
    description:
      "Create the shared discussion markdown file with header + today's PnL summary. " +
      "pnl_summary keys must be exactly 'aggressive' | 'neutral' | 'conservative' " +
      "(no currency suffix). Values are daily return PERCENTAGES " +
      "(e.g. 1.23 renders as '+1.2%'). Unknown keys are silently ignored.",
    inputSchema: {
      date: z.string(),
      pnl_summary: z.record(z.number()).optional(),
      force: z.boolean().optional(),
    },
  },
  async (p) => {
    const args = ["init-discussion", "--date", p.date];
    if (p.pnl_summary) args.push("--pnl-summary", JSON.stringify(p.pnl_summary));
    if (p.force) args.push("--force");
    return textResult(await callPython(args));
  }
);

server.registerTool(
  "read_discussion",
  {
    description: "Read the full discussion markdown for a date.",
    inputSchema: { date: z.string() },
  },
  async (p) =>
    textResult(await callPython(["read-discussion", "--date", p.date]))
);

server.registerTool(
  "append_discussion",
  {
    description: "Append a speaker's turn, including a next_speaker directive (embedded as HTML comment for the orchestrator).",
    inputSchema: {
      date: z.string(),
      speaker: z.enum(["aggressive", "neutral", "conservative"]),
      markdown: z.string(),
      next_speaker: z.enum(["aggressive", "neutral", "conservative", "end"]),
      reason: z.string().optional(),
    },
  },
  async (p) => {
    const args = [
      "append-discussion", "--date", p.date, "--speaker", p.speaker,
      "--markdown", p.markdown, "--next-speaker", p.next_speaker,
    ];
    if (p.reason) args.push("--reason", p.reason);
    return textResult(await callPython(args));
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
