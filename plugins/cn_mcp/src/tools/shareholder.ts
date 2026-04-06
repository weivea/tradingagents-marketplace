import { callPython } from "./call-python.js";

/** Strip .SS / .SZ suffix from symbol for the Python side. */
function stripSuffix(symbol: string): string {
  return symbol.split(".")[0];
}

export interface GetCnShareholderChangesParams {
  symbol: string;
  date: string;
}

export async function getCnShareholderChanges(params: GetCnShareholderChangesParams): Promise<string> {
  const { symbol, date } = params;
  const code = stripSuffix(symbol);
  const args = ["cn-shareholder", code, "--date", date];
  try {
    const raw = await callPython(args);
    const result = JSON.parse(raw);
    return result.text ?? raw;
  } catch (error: any) {
    return `Error fetching shareholder changes: ${error.message}`;
  }
}
