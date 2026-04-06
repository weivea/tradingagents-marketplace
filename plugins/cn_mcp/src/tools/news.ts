import { callPython } from "./call-python.js";

/** Strip .SS / .SZ suffix from symbol for the Python side. */
function stripSuffix(symbol: string): string {
  return symbol.split(".")[0];
}

export interface GetCnNewsParams {
  symbol: string;
  limit?: number;
}

export async function getCnNews(params: GetCnNewsParams): Promise<string> {
  const { symbol, limit } = params;
  const code = stripSuffix(symbol);
  const args = ["cn-news", code];
  if (limit !== undefined) args.push("--limit", String(limit));
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching CN news: ${error.message}`;
  }
}

export interface GetCnGlobalNewsParams {
  limit?: number;
}

export async function getCnGlobalNews(params: GetCnGlobalNewsParams): Promise<string> {
  const { limit } = params;
  const args = ["cn-global-news"];
  if (limit !== undefined) args.push("--limit", String(limit));
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching CN global news: ${error.message}`;
  }
}
