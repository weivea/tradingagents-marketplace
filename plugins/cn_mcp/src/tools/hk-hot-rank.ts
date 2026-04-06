import { callPython } from "./call-python.js";

export interface GetHkHotRankParams {
  symbol?: string;
}

export async function getHkHotRank(params: GetHkHotRankParams): Promise<string> {
  const { symbol } = params;
  const args = ["hk-hot-rank"];
  if (symbol) args.push(symbol);
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching HK hot rank: ${error.message}`;
  }
}
