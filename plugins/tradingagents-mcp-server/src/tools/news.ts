import yahooFinance from "yahoo-finance2";

export interface NewsParams {
  ticker: string;
  start_date: string;
  end_date: string;
}

export interface GlobalNewsParams {
  curr_date: string;
  look_back_days?: number;
  limit?: number;
}

export interface InsiderParams {
  ticker: string;
}

export async function getNews(params: NewsParams): Promise<string> {
  const { ticker, start_date, end_date } = params;
  try {
    const result = await yahooFinance.search(ticker, { newsCount: 20 });
    const news = result.news ?? [];

    if (news.length === 0) {
      return `No news found for ${ticker}.`;
    }

    const startMs = new Date(start_date).getTime();
    const endMs = new Date(end_date).getTime() + 86400000;

    const filtered = news.filter((n: any) => {
      if (!n.providerPublishTime) return true;
      const pubMs = typeof n.providerPublishTime === "number"
        ? n.providerPublishTime * 1000
        : new Date(n.providerPublishTime).getTime();
      return pubMs >= startMs && pubMs <= endMs;
    });

    const articles = (filtered.length > 0 ? filtered : news).map((n: any, i: number) => {
      const pubDate = n.providerPublishTime
        ? new Date(typeof n.providerPublishTime === "number" ? n.providerPublishTime * 1000 : n.providerPublishTime).toISOString().split("T")[0]
        : "N/A";
      return `${i + 1}. [${pubDate}] **${n.title ?? "No title"}**\n   Publisher: ${n.publisher ?? "N/A"}\n   Link: ${n.link ?? "N/A"}`;
    });

    return `# News for ${ticker} (${start_date} to ${end_date})\n\n${articles.join("\n\n")}`;
  } catch (error: any) {
    return `Error fetching news for ${ticker}: ${error.message}`;
  }
}

export async function getGlobalNews(params: GlobalNewsParams): Promise<string> {
  const { curr_date, look_back_days = 7, limit = 10 } = params;
  const queries = ["stock market", "economy", "federal reserve", "inflation", "GDP"];

  try {
    const allNews: any[] = [];

    for (const query of queries) {
      try {
        const result = await yahooFinance.search(query, { newsCount: limit });
        if (result.news) allNews.push(...result.news);
      } catch {
        // skip failed queries
      }
    }

    const seen = new Set<string>();
    const unique = allNews.filter((n: any) => {
      const key = n.title ?? n.link ?? "";
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    const articles = unique.slice(0, limit).map((n: any, i: number) => {
      const pubDate = n.providerPublishTime
        ? new Date(typeof n.providerPublishTime === "number" ? n.providerPublishTime * 1000 : n.providerPublishTime).toISOString().split("T")[0]
        : "N/A";
      return `${i + 1}. [${pubDate}] **${n.title ?? "No title"}**\n   Publisher: ${n.publisher ?? "N/A"}`;
    });

    return `# Global Market News (as of ${curr_date}, past ${look_back_days} days)\n\n${articles.join("\n\n")}`;
  } catch (error: any) {
    return `Error fetching global news: ${error.message}`;
  }
}

export async function getInsiderTransactions(params: InsiderParams): Promise<string> {
  const { ticker } = params;
  try {
    const quote = await yahooFinance.quoteSummary(ticker, {
      modules: ["insiderTransactions", "insiderHolders"],
    });

    const sections: string[] = [];

    const transactions = quote.insiderTransactions?.transactions;
    if (transactions && transactions.length > 0) {
      const rows = transactions.slice(0, 20).map((t: any) => {
        return `- **${t.filerName ?? "N/A"}** (${t.filerRelation ?? "N/A"}): ${t.transactionText ?? "N/A"} — ${formatNum(t.value)} on ${t.startDate?.toISOString().split("T")[0] ?? "N/A"}`;
      });
      sections.push(`## Recent Insider Transactions\n\n${rows.join("\n")}`);
    }

    const holders = quote.insiderHolders?.holders;
    if (holders && holders.length > 0) {
      const rows = holders.slice(0, 10).map((h: any) => {
        return `- **${h.name ?? "N/A"}** (${h.relation ?? "N/A"}): ${formatNum(h.positionDirect)} shares`;
      });
      sections.push(`## Top Insider Holders\n\n${rows.join("\n")}`);
    }

    if (sections.length === 0) {
      return `No insider transaction data found for ${ticker}.`;
    }

    return `# Insider Transactions for ${ticker}\n\n${sections.join("\n\n")}`;
  } catch (error: any) {
    return `Error fetching insider transactions for ${ticker}: ${error.message}`;
  }
}

function formatNum(val: number | null | undefined): string {
  if (val == null) return "N/A";
  if (Math.abs(val) >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  if (Math.abs(val) >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
  if (Math.abs(val) >= 1e3) return `$${(val / 1e3).toFixed(2)}K`;
  return `$${val.toFixed(2)}`;
}
