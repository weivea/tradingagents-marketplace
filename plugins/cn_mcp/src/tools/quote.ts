import { callPython } from "./call-python.js";

function strip(symbol: string): string {
  return symbol.split(".")[0];
}

export async function getCnStockQuote(params: { symbol: string }): Promise<string> {
  try {
    const raw = await callPython(["cn-stock-quote", strip(params.symbol)]);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching CN quote: ${error.message}`;
  }
}

export async function getHkStockQuote(params: { symbol: string }): Promise<string> {
  try {
    const raw = await callPython(["hk-stock-quote", strip(params.symbol)]);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching HK quote: ${error.message}`;
  }
}
