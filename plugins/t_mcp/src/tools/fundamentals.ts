import YahooFinance from "yahoo-finance2";
const yahooFinance = new YahooFinance();

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
        `- **Shares Outstanding**: ${formatCount(stats.sharesOutstanding)}`
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
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 2);

    const statements = await yahooFinance.fundamentalsTimeSeries(ticker, {
      period1: startDate.toISOString().split("T")[0],
      period2: endDate.toISOString().split("T")[0],
      type: freq === "quarterly" ? "quarterly" : "annual",
      module: "balance-sheet",
    });

    if (!statements || statements.length === 0) {
      return `No balance sheet data found for ${ticker}.`;
    }

    const rows = statements.map((s: any) => {
      const date = s.date ? new Date(s.date).toISOString().split("T")[0] : "N/A";
      return `### ${date}\n` +
        `- Total Assets: ${formatNum(s.totalAssets)}\n` +
        `- Total Liabilities: ${formatNum(s.totalLiabilitiesNetMinorityInterest)}\n` +
        `- Stockholders Equity: ${formatNum(s.stockholdersEquity)}\n` +
        `- Cash & Equivalents: ${formatNum(s.cashAndCashEquivalents)}\n` +
        `- Short Term Investments: ${formatNum(s.otherShortTermInvestments)}\n` +
        `- Receivables: ${formatNum(s.receivables)}\n` +
        `- Inventory: ${formatNum(s.inventory)}\n` +
        `- Current Assets: ${formatNum(s.currentAssets)}\n` +
        `- Current Liabilities: ${formatNum(s.currentLiabilities)}\n` +
        `- Long Term Debt: ${formatNum(s.longTermDebt)}\n` +
        `- Total Debt: ${formatNum(s.totalDebt)}\n` +
        `- Net Debt: ${formatNum(s.netDebt)}\n` +
        `- Working Capital: ${formatNum(s.workingCapital)}`;
    });

    return `# Balance Sheet for ${ticker} (${freq})\n\n${rows.join("\n\n")}`;
  } catch (error: any) {
    return `Error fetching balance sheet for ${ticker}: ${error.message}`;
  }
}

export async function getCashflow(params: FinancialStatementParams): Promise<string> {
  const { ticker, freq = "quarterly" } = params;
  try {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 2);

    const statements = await yahooFinance.fundamentalsTimeSeries(ticker, {
      period1: startDate.toISOString().split("T")[0],
      period2: endDate.toISOString().split("T")[0],
      type: freq === "quarterly" ? "quarterly" : "annual",
      module: "cash-flow",
    });

    if (!statements || statements.length === 0) {
      return `No cashflow data found for ${ticker}.`;
    }

    const rows = statements.map((s: any) => {
      const date = s.date ? new Date(s.date).toISOString().split("T")[0] : "N/A";
      return `### ${date}\n` +
        `- Operating Cash Flow: ${formatNum(s.operatingCashFlow)}\n` +
        `- Capital Expenditures: ${formatNum(s.capitalExpenditure)}\n` +
        `- Free Cash Flow: ${formatNum(s.freeCashFlow)}\n` +
        `- Investing Cash Flow: ${formatNum(s.investingCashFlow)}\n` +
        `- Financing Cash Flow: ${formatNum(s.financingCashFlow)}\n` +
        `- Dividends Paid: ${formatNum(s.cashDividendsPaid)}\n` +
        `- Stock Repurchases: ${formatNum(s.repurchaseOfCapitalStock)}\n` +
        `- Depreciation & Amortization: ${formatNum(s.depreciationAndAmortization)}`;
    });

    return `# Cash Flow Statement for ${ticker} (${freq})\n\n${rows.join("\n\n")}`;
  } catch (error: any) {
    return `Error fetching cashflow for ${ticker}: ${error.message}`;
  }
}

export async function getIncomeStatement(params: FinancialStatementParams): Promise<string> {
  const { ticker, freq = "quarterly" } = params;
  try {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 2);

    const statements = await yahooFinance.fundamentalsTimeSeries(ticker, {
      period1: startDate.toISOString().split("T")[0],
      period2: endDate.toISOString().split("T")[0],
      type: freq === "quarterly" ? "quarterly" : "annual",
      module: "financials",
    });

    if (!statements || statements.length === 0) {
      return `No income statement data found for ${ticker}.`;
    }

    const rows = statements.map((s: any) => {
      const date = s.date ? new Date(s.date).toISOString().split("T")[0] : "N/A";
      return `### ${date}\n` +
        `- Total Revenue: ${formatNum(s.totalRevenue)}\n` +
        `- Cost of Revenue: ${formatNum(s.costOfRevenue)}\n` +
        `- Gross Profit: ${formatNum(s.grossProfit)}\n` +
        `- Operating Expense: ${formatNum(s.operatingExpense)}\n` +
        `- Operating Income: ${formatNum(s.operatingIncome)}\n` +
        `- Net Income: ${formatNum(s.netIncome)}\n` +
        `- EBITDA: ${formatNum(s.EBITDA)}\n` +
        `- EBIT: ${formatNum(s.EBIT)}\n` +
        `- Diluted EPS: ${s.dilutedEPS ?? "N/A"}\n` +
        `- R&D Expense: ${formatNum(s.researchAndDevelopment)}\n` +
        `- SG&A Expense: ${formatNum(s.sellingGeneralAndAdministration)}`;
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

function formatCount(val: number | null | undefined): string {
  if (val == null) return "N/A";
  if (Math.abs(val) >= 1e9) return `${(val / 1e9).toFixed(2)}B`;
  if (Math.abs(val) >= 1e6) return `${(val / 1e6).toFixed(2)}M`;
  if (Math.abs(val) >= 1e3) return `${(val / 1e3).toFixed(2)}K`;
  return val.toLocaleString();
}

function formatPct(val: number | null | undefined): string {
  if (val == null) return "N/A";
  return `${(val * 100).toFixed(2)}%`;
}
