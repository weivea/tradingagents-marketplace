import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { parseReport } from "./tools/parse.js";
import { generateTts } from "./tools/tts.js";
import { renderFrames } from "./tools/render.js";
import { composeVideo } from "./tools/compose.js";
import { generateVideo } from "./tools/generate.js";

const server = new McpServer({
  name: "gv",
  version: "0.1.0",
});

// --- Parse Report ---
server.registerTool(
  "parse_report",
  {
    description: "Parse a Chinese Markdown analysis report into structured sections with metadata (ticker, date, rating)",
    inputSchema: {
      report_path: z.string().describe("Path to *_zh.md report file"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await parseReport(params) }],
  })
);

// --- Generate TTS ---
server.registerTool(
  "generate_tts",
  {
    description: "Generate Chinese TTS audio with word-level timestamps and SRT subtitles using edge-tts",
    inputSchema: {
      text: z.string().describe("Chinese text to synthesize"),
      output_dir: z.string().describe("Directory to write audio, timestamps, and SRT files"),
      voice: z.string().optional().describe("TTS voice (default: zh-CN-YunyangNeural)"),
      rate: z.string().optional().describe("Speech rate e.g. '+5%' (default: '+0%')"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await generateTts(params) }],
  })
);

// --- Render Frames ---
server.registerTool(
  "render_frames",
  {
    description: "Render report sections as images: full layout creates one tall scroll image, short layout creates per-slide images",
    inputSchema: {
      sections_path: z.string().describe("Path to sections JSON file"),
      layout: z.enum(["full", "short"]).describe("'full' for scroll image, 'short' for per-slide images"),
      output_dir: z.string().describe("Directory to write output images"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await renderFrames(params) }],
  })
);

// --- Compose Video ---
server.registerTool(
  "compose_video",
  {
    description: "Compose final MP4 video from rendered frames and TTS audio with synchronized scrolling/transitions",
    inputSchema: {
      frames_dir: z.string().describe("Frames directory (short) or scroll image path (full)"),
      audio_path: z.string().describe("Path to TTS audio file"),
      timestamps_path: z.string().describe("Path to timestamps JSON"),
      layout: z.enum(["full", "short"]).describe("'full' for scroll, 'short' for slides"),
      output_path: z.string().describe("Output MP4 file path"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await composeVideo(params) }],
  })
);

// --- Generate Video (one-click) ---
server.registerTool(
  "generate_video",
  {
    description: "One-click: convert a Chinese analysis report to narrated scrolling video (full, short, or both versions)",
    inputSchema: {
      report_path: z.string().describe("Path to *_zh.md report file"),
      version: z.enum(["full", "short", "both"]).optional().default("both").describe("Which version(s) to generate"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await generateVideo(params) }],
  })
);

// --- Start server ---
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
