import yahooFinance from "yahoo-finance2";

export interface StockDataParams {
  symbol: string;
  start_date: string;
  end_date: string;
}

export async function getStockData(params: StockDataParams): Promise<string> {
  const { symbol, start_date, end_date } = params;

  try {
    const result = await yahooFinance.historical(symbol, {
      period1: start_date,
      period2: end_date,
    });

    if (!result || result.length === 0) {
      return `No stock data found for ${symbol} between ${start_date} and ${end_date}.`;
    }

    const header = "Date,Open,High,Low,Close,Volume,Adj Close";
    const rows = result.map(
      (r) =>
        `${r.date.toISOString().split("T")[0]},${r.open?.toFixed(2) ?? "N/A"},${r.high?.toFixed(2) ?? "N/A"},${r.low?.toFixed(2) ?? "N/A"},${r.close?.toFixed(2) ?? "N/A"},${r.volume ?? 0},${r.adjClose?.toFixed(2) ?? r.close?.toFixed(2) ?? "N/A"}`
    );

    return `Stock data for ${symbol} (${start_date} to ${end_date}):\n${header}\n${rows.join("\n")}`;
  } catch (error: any) {
    return `Error fetching stock data for ${symbol}: ${error.message}`;
  }
}
