import yahooFinance from "yahoo-finance2";

export interface FundamentalsParams {
  ticker: string;
  curr_date?: string;
}

export interface FinancialStatementParams {
  ticker: string;
  freq?: "quarterly" | "annual";
  curr_date?: string;
}

export async function getFundamentals(params: FundamentalsParams): Promise<string> {
  const { ticker } = params;
  try {
    const quote = await yahooFinance.quoteSummary(ticker, {
      modules: [
        "assetProfile",
        "financialData",
        "defaultKeyStatistics",
        "earningsTrend",
      ],
    });

    const profile = quote.assetProfile;
    const financial = quote.financialData;
    const stats = quote.defaultKeyStatistics;

    const sections: string[] = [];

    if (profile) {
      sections.push(
        `## Company Profile\n` +
        `- **Sector**: ${profile.sector ?? "N/A"}\n` +
        `- **Industry**: ${profile.industry ?? "N/A"}\n` +
        `- **Employees**: ${profile.fullTimeEmployees ?? "N/A"}\n` +
        `- **Website**: ${profile.website ?? "N/A"}\n` +
        `- **Summary**: ${profile.longBusinessSummary ?? "N/A"}`
      );
    }

    if (financial) {
      sections.push(
        `## Financial Data\n` +
        `- **Revenue**: ${formatNum(financial.totalRevenue)}\n` +
        `- **Revenue Growth**: ${formatPct(financial.revenueGrowth)}\n` +
        `- **Gross Profit**: ${formatNum(financial.grossProfits)}\n` +
        `- **EBITDA**: ${formatNum(financial.ebitda)}\n` +
        `- **Profit Margin**: ${formatPct(financial.profitMargins)}\n` +
        `- **Operating Margin**: ${formatPct(financial.operatingMargins)}\n` +
        `- **ROE**: ${formatPct(financial.returnOnEquity)}\n` +
        `- **ROA**: ${formatPct(financial.returnOnAssets)}\n` +
        `- **Current Price**: ${financial.currentPrice ?? "N/A"}\n` +
        `- **Target Mean Price**: ${financial.targetMeanPrice ?? "N/A"}\n` +
        `- **Recommendation**: ${financial.recommendationKey ?? "N/A"}`
      );
    }

    if (stats) {
      sections.push(
        `## Key Statistics\n` +
        `- **Enterprise Value**: ${formatNum(stats.enterpriseValue)}\n` +
        `- **Trailing EPS**: ${stats.trailingEps ?? "N/A"}\n` +
        `- **Forward EPS**: ${stats.forwardEps ?? "N/A"}\n` +
        `- **PEG Ratio**: ${stats.pegRatio ?? "N/A"}\n` +
        `- **Price to Book**: ${stats.priceToBook ?? "N/A"}\n` +
        `- **Beta**: ${stats.beta ?? "N/A"}\n` +
        `- **Shares Outstanding**: ${formatNum(stats.sharesOutstanding)}`
      );
    }

    return `# Fundamentals Report for ${ticker}\n\n${sections.join("\n\n")}`;
  } catch (error: any) {
    return `Error fetching fundamentals for ${ticker}: ${error.message}`;
  }
}

export async function getBalanceSheet(params: FinancialStatementParams): Promise<string> {
  const { ticker, freq = "quarterly" } = params;
  try {
    const modules: any[] = freq === "quarterly" ? ["balanceSheetHistoryQuarterly"] : ["balanceSheetHistory"];
    const quote = await yahooFinance.quoteSummary(ticker, { modules });
    const statements: any[] | undefined = freq === "quarterly"
      ? quote.balanceSheetHistoryQuarterly?.balanceSheetStatements
      : quote.balanceSheetHistory?.balanceSheetStatements;

    if (!statements || statements.length === 0) {
      return `No balance sheet data found for ${ticker}.`;
    }

    const rows = statements.map((s: any) => {
      return `### ${s.endDate?.toISOString().split("T")[0] ?? "N/A"}\n` +
        `- Total Assets: ${formatNum(s.totalAssets)}\n` +
        `- Total Liabilities: ${formatNum(s.totalLiab)}\n` +
        `- Total Stockholder Equity: ${formatNum(s.totalStockholderEquity)}\n` +
        `- Cash: ${formatNum(s.cash)}\n` +
        `- Short Term Investments: ${formatNum(s.shortTermInvestments)}\n` +
        `- Net Receivables: ${formatNum(s.netReceivables)}\n` +
        `- Long Term Debt: ${formatNum(s.longTermDebt)}`;
    });

    return `# Balance Sheet for ${ticker} (${freq})\n\n${rows.join("\n\n")}`;
  } catch (error: any) {
    return `Error fetching balance sheet for ${ticker}: ${error.message}`;
  }
}

export async function getCashflow(params: FinancialStatementParams): Promise<string> {
  const { ticker, freq = "quarterly" } = params;
  try {
    const modules: any[] = freq === "quarterly" ? ["cashflowStatementHistoryQuarterly"] : ["cashflowStatementHistory"];
    const quote = await yahooFinance.quoteSummary(ticker, { modules });
    const statements: any[] | undefined = freq === "quarterly"
      ? quote.cashflowStatementHistoryQuarterly?.cashflowStatements
      : quote.cashflowStatementHistory?.cashflowStatements;

    if (!statements || statements.length === 0) {
      return `No cashflow data found for ${ticker}.`;
    }

    const rows = statements.map((s: any) => {
      return `### ${s.endDate?.toISOString().split("T")[0] ?? "N/A"}\n` +
        `- Operating Cash Flow: ${formatNum(s.totalCashFromOperatingActivities)}\n` +
        `- Capital Expenditures: ${formatNum(s.capitalExpenditures)}\n` +
        `- Free Cash Flow: ${formatNum((s.totalCashFromOperatingActivities ?? 0) + (s.capitalExpenditures ?? 0))}\n` +
        `- Investing Cash Flow: ${formatNum(s.totalCashflowsFromInvestingActivities)}\n` +
        `- Financing Cash Flow: ${formatNum(s.totalCashFromFinancingActivities)}\n` +
        `- Dividends Paid: ${formatNum(s.dividendsPaid)}`;
    });

    return `# Cash Flow Statement for ${ticker} (${freq})\n\n${rows.join("\n\n")}`;
  } catch (error: any) {
    return `Error fetching cashflow for ${ticker}: ${error.message}`;
  }
}

export async function getIncomeStatement(params: FinancialStatementParams): Promise<string> {
  const { ticker, freq = "quarterly" } = params;
  try {
    const modules: any[] = freq === "quarterly" ? ["incomeStatementHistoryQuarterly"] : ["incomeStatementHistory"];
    const quote = await yahooFinance.quoteSummary(ticker, { modules });
    const statements: any[] | undefined = freq === "quarterly"
      ? quote.incomeStatementHistoryQuarterly?.incomeStatementHistory
      : quote.incomeStatementHistory?.incomeStatementHistory;

    if (!statements || statements.length === 0) {
      return `No income statement data found for ${ticker}.`;
    }

    const rows = statements.map((s: any) => {
      return `### ${s.endDate?.toISOString().split("T")[0] ?? "N/A"}\n` +
        `- Total Revenue: ${formatNum(s.totalRevenue)}\n` +
        `- Cost of Revenue: ${formatNum(s.costOfRevenue)}\n` +
        `- Gross Profit: ${formatNum(s.grossProfit)}\n` +
        `- Operating Income: ${formatNum(s.operatingIncome)}\n` +
        `- Net Income: ${formatNum(s.netIncome)}\n` +
        `- EBIT: ${formatNum(s.ebit)}`;
    });

    return `# Income Statement for ${ticker} (${freq})\n\n${rows.join("\n\n")}`;
  } catch (error: any) {
    return `Error fetching income statement for ${ticker}: ${error.message}`;
  }
}

function formatNum(val: number | null | undefined): string {
  if (val == null) return "N/A";
  if (Math.abs(val) >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (Math.abs(val) >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  if (Math.abs(val) >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
  return `$${val.toLocaleString()}`;
}

function formatPct(val: number | null | undefined): string {
  if (val == null) return "N/A";
  return `${(val * 100).toFixed(2)}%`;
}
