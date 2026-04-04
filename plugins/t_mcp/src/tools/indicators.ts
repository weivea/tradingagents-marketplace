import YahooFinance from "yahoo-finance2";
const yahooFinance = new YahooFinance();
import { computeIndicator, OHLCVRow } from "../utils/indicator-calc.js";

export interface IndicatorParams {
  symbol: string;
  indicator: string;
  curr_date: string;
  look_back_days?: number;
}

export async function getIndicators(params: IndicatorParams): Promise<string> {
  const { symbol, indicator, curr_date, look_back_days = 365 } = params;

  try {
    const endDate = new Date(curr_date);
    const startDate = new Date(curr_date);
    startDate.setDate(startDate.getDate() - look_back_days);

    const result = await yahooFinance.historical(symbol, {
      period1: startDate.toISOString().split("T")[0],
      period2: endDate.toISOString().split("T")[0],
    });

    if (!result || result.length === 0) {
      return `No data found for ${symbol} to compute ${indicator}.`;
    }

    const ohlcv: OHLCVRow[] = result.map((r) => ({
      date: r.date.toISOString().split("T")[0],
      open: r.open ?? 0,
      high: r.high ?? 0,
      low: r.low ?? 0,
      close: r.close ?? 0,
      volume: r.volume ?? 0,
    }));

    return computeIndicator(ohlcv, indicator);
  } catch (error: any) {
    return `Error computing ${indicator} for ${symbol}: ${error.message}`;
  }
}
