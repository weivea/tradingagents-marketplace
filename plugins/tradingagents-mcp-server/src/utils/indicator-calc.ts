import { SMA, EMA, MACD, RSI, BollingerBands, ATR } from "technicalindicators";

export interface OHLCVRow {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export function computeIndicator(data: OHLCVRow[], indicatorName: string): string {
  const closes = data.map((d) => d.close);
  const highs = data.map((d) => d.high);
  const lows = data.map((d) => d.low);
  const volumes = data.map((d) => d.volume);

  let result: string;

  switch (indicatorName) {
    case "close_50_sma": {
      const values = SMA.calculate({ period: 50, values: closes });
      result = formatSeries(data, values, data.length - values.length, "SMA_50");
      break;
    }
    case "close_200_sma": {
      const values = SMA.calculate({ period: 200, values: closes });
      result = formatSeries(data, values, data.length - values.length, "SMA_200");
      break;
    }
    case "close_10_ema": {
      const values = EMA.calculate({ period: 10, values: closes });
      result = formatSeries(data, values, data.length - values.length, "EMA_10");
      break;
    }
    case "macd":
    case "macds":
    case "macdh": {
      const macdResult = MACD.calculate({
        values: closes,
        fastPeriod: 12,
        slowPeriod: 26,
        signalPeriod: 9,
        SimpleMAOscillator: false,
        SimpleMASignal: false,
      });
      const offset = data.length - macdResult.length;
      const header = "Date,MACD,Signal,Histogram";
      const rows = macdResult.map(
        (m, i) =>
          `${data[i + offset].date},${m.MACD?.toFixed(4) ?? "N/A"},${m.signal?.toFixed(4) ?? "N/A"},${m.histogram?.toFixed(4) ?? "N/A"}`
      );
      result = `${header}\n${rows.join("\n")}`;
      break;
    }
    case "rsi": {
      const values = RSI.calculate({ period: 14, values: closes });
      result = formatSeries(data, values, data.length - values.length, "RSI");
      break;
    }
    case "boll":
    case "boll_ub":
    case "boll_lb": {
      const bollResult = BollingerBands.calculate({
        period: 20,
        values: closes,
        stdDev: 2,
      });
      const offset = data.length - bollResult.length;
      const header = "Date,Middle,Upper,Lower";
      const rows = bollResult.map(
        (b, i) =>
          `${data[i + offset].date},${b.middle.toFixed(4)},${b.upper.toFixed(4)},${b.lower.toFixed(4)}`
      );
      result = `${header}\n${rows.join("\n")}`;
      break;
    }
    case "atr": {
      const values = ATR.calculate({
        period: 14,
        high: highs,
        low: lows,
        close: closes,
      });
      result = formatSeries(data, values, data.length - values.length, "ATR");
      break;
    }
    case "vwma": {
      const period = 20;
      const values: number[] = [];
      for (let i = period - 1; i < closes.length; i++) {
        let sumPV = 0;
        let sumV = 0;
        for (let j = i - period + 1; j <= i; j++) {
          sumPV += closes[j] * volumes[j];
          sumV += volumes[j];
        }
        values.push(sumV === 0 ? 0 : sumPV / sumV);
      }
      result = formatSeries(data, values, data.length - values.length, "VWMA");
      break;
    }
    default:
      return `Unknown indicator: ${indicatorName}. Supported: close_50_sma, close_200_sma, close_10_ema, macd, macds, macdh, rsi, boll, boll_ub, boll_lb, atr, vwma`;
  }

  return `${indicatorName} for the given period:\n${result}`;
}

function formatSeries(data: OHLCVRow[], values: number[], offset: number, label: string): string {
  const header = `Date,${label}`;
  const rows = values.map(
    (v, i) => `${data[i + offset].date},${v.toFixed(4)}`
  );
  return `${header}\n${rows.join("\n")}`;
}
