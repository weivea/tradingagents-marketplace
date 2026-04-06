import { callPython } from "./call-python.js";

/** Strip .SS / .SZ suffix from symbol for the Python side. */
function stripSuffix(symbol: string): string {
  return symbol.split(".")[0];
}

export interface GetCnStockInfoParams {
  symbol: string;
}

export async function getCnStockInfo(params: GetCnStockInfoParams): Promise<string> {
  const { symbol } = params;
  const code = stripSuffix(symbol);
  const args = ["cn-stock-info", code];
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching stock info: ${error.message}`;
  }
}
