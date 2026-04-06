import { callPython } from "./call-python.js";

/** Strip .SS / .SZ suffix from symbol for the Python side. */
function stripSuffix(symbol: string): string {
  return symbol.split(".")[0];
}

export interface GetCnDragonTigerParams {
  symbol: string;
  start_date: string;
  end_date: string;
}

export async function getCnDragonTiger(params: GetCnDragonTigerParams): Promise<string> {
  const { symbol, start_date, end_date } = params;
  const code = stripSuffix(symbol);
  const args = ["cn-dragon-tiger", code, "--start-date", start_date, "--end-date", end_date];
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching dragon tiger data: ${error.message}`;
  }
}

export interface GetCnDragonTigerStatsParams {
  period?: string;
}

export async function getCnDragonTigerStats(params: GetCnDragonTigerStatsParams): Promise<string> {
  const { period } = params;
  const args = ["cn-dragon-tiger-stats"];
  if (period !== undefined) args.push("--period", period);
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching dragon tiger stats: ${error.message}`;
  }
}
