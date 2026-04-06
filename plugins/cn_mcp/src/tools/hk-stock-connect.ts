import { callPython } from "./call-python.js";

export interface GetHkStockConnectParams {
  symbol: string;
}

export async function getHkStockConnect(params: GetHkStockConnectParams): Promise<string> {
  const { symbol } = params;
  const args = ["hk-stock-connect", symbol];
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching HK Stock Connect data: ${error.message}`;
  }
}
