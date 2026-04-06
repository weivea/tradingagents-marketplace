import { callPython } from "./call-python.js";

export interface GetHkStockInfoParams {
  symbol: string;
}

export async function getHkStockInfo(params: GetHkStockInfoParams): Promise<string> {
  const { symbol } = params;
  const args = ["hk-stock-info", symbol];
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching HK stock info: ${error.message}`;
  }
}
