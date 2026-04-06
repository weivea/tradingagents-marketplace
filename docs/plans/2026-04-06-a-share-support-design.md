# A 股交易分析支持设计方案

> Date: 2026-04-06
> Status: Approved

## 问题背景

当前系统基于 Yahoo Finance (yahoo-finance2) 提供美股全链路分析。实测表明 Yahoo Finance 对 A 股的**股价/技术指标/财报**数据覆盖良好（用茅台 600519.SS 验证通过），但**新闻/内幕交易/舆情**数据为空或不相关。需要补充 A 股专属数据源，达到与美股分析同等质量。

## 方案选择

| 方案 | 描述 | 结论 |
|------|------|------|
| A. 智能路由 | 新建 cn_mcp，Yahoo 继续提供股价/财报，AKShare 补充新闻/龙虎榜/股东 | ✅ **选中** |
| B. 完全独立 | A 股所有数据都由 cn_mcp 提供 | ❌ 重复造轮子 |
| C. 精简版 | 只补新闻和舆情 | ❌ 不够全面 |

## 一、cn_mcp Python MCP Server

### 定位

新建 `plugins/cn_mcp/`，基于 `uv` + Python MCP SDK + AKShare，专门提供 A 股特色数据。

### 技术栈

- 运行时: `uv run`
- 框架: `mcp` (Python MCP SDK)
- 数据源: `akshare`
- 包管理: `pyproject.toml` + `uv`

### MCP 工具（6 个）

| 工具名 | AKShare 函数 | 对标 t_mcp | 说明 |
|--------|-------------|-----------|------|
| `get_cn_news` | `stock_news_em(symbol)` | 替代 `get_news` | A 股中文新闻（东方财富源） |
| `get_cn_global_news` | `stock_news_em` + 宏观关键词搜索 | 替代 `get_global_news` | 中国宏观经济/政策新闻 |
| `get_cn_dragon_tiger` | `stock_lhb_detail_em(start_date, end_date)` | 替代 `get_insider_transactions` | 龙虎榜明细 |
| `get_cn_dragon_tiger_stats` | `stock_lhb_stock_statistic_em(symbol)` | 无美股对标 | 龙虎榜统计（机构买卖） |
| `get_cn_shareholder_changes` | `stock_gdfx_free_holding_change_em(date)` | 补充 insider | 十大流通股东变动 |
| `get_cn_stock_info` | `stock_individual_info_em(symbol)` | 补充 fundamentals | A 股基础信息 |

### 目录结构

```
plugins/cn_mcp/
├── pyproject.toml
├── src/
│   └── cn_mcp/
│       ├── __init__.py
│       ├── server.py           # MCP server 入口
│       └── tools/
│           ├── news.py         # get_cn_news, get_cn_global_news
│           ├── dragon_tiger.py # 龙虎榜相关
│           ├── shareholder.py  # 股东变动
│           └── stock_info.py   # A 股基础信息
```

### Ticker 格式

AKShare 使用纯 6 位数字（如 `600519`），而系统统一使用 Yahoo 格式（`600519.SS`）。cn_mcp 内部自动转换：

```python
def yahoo_to_akshare(ticker: str) -> str:
    """600519.SS → 600519"""
    return ticker.split(".")[0]
```

## 二、智能路由 — 数据源选择

### Ticker 市场识别

```
输入 ticker
  → 包含 .SS 或 .SZ → A 股
  → 6 位纯数字 → A 股（6开头→.SS，其他→.SZ）
  → 其他 → 美股/国际（走现有逻辑）
```

### 数据源路由规则

| 数据类型 | 美股 | A 股 |
|----------|------|------|
| 股价 OHLCV | t_mcp (Yahoo) | t_mcp (Yahoo) ✅ |
| 技术指标 | t_mcp (本地计算) | t_mcp (本地计算) ✅ |
| 基本面 | t_mcp (Yahoo) | t_mcp (Yahoo) ✅ |
| 财务报表 | t_mcp (Yahoo) | t_mcp (Yahoo) ✅ |
| 公司新闻 | t_mcp (Yahoo) | **cn_mcp (AKShare)** |
| 全球/宏观新闻 | t_mcp (Yahoo) | **cn_mcp (AKShare)** |
| 内幕/龙虎榜 | t_mcp (insider) | **cn_mcp (AKShare)** |
| 股东变动 | — | **cn_mcp (AKShare)** |
| A 股基础信息 | — | **cn_mcp (AKShare)** |

### 路由实现

通过 orchestration skill prompt 实现，不需要代码层面的路由器。在 `ta:trading-analysis` 入口 skill 中加入市场识别和数据源选择指令。

## 三、Agent Prompt 适配

复用所有现有 agent，通过 orchestrator 注入 A 股市场上下文：

### 需要注入的 A 股规则

```markdown
### A 股市场规则
- 涨跌幅限制：主板 ±10%，科创板/创业板 ±20%，ST ±5%
- T+1 交易制度（当日买入不可当日卖出）
- 交易时段：9:15-9:25 集合竞价，9:30-11:30 / 13:00-15:00 连续竞价
- 货币：人民币 (CNY)
- 龙虎榜替代内幕交易作为资金流向参考
- 关注政策面：证监会、央行、国务院政策对 A 股影响大
- 北向资金（沪深港通外资流向）是重要的市场情绪指标
```

### Agent 适配重点

| Agent | 适配内容 |
|-------|---------|
| market-analyst | 涨跌停、T+1、集合竞价规则 |
| news-analyst | 使用 cn_mcp 工具，关注政策面 |
| sentiment-analyst | 东方财富/雪球特征，北向资金情绪 |
| fundamentals-analyst | 人民币单位，中国 GAAP |
| bull/bear researchers | 政策驱动、板块轮动、北向资金 |
| risk analysts | 政策风险、涨跌停锁仓、流动性风险 |

## 四、配置集成

### settings.local.json 新增

```json
{
  "mcpServers": {
    "cn_mcp": {
      "command": "uv",
      "args": ["run", "--directory", "plugins/cn_mcp", "cn-mcp"],
      "env": {}
    }
  }
}
```

## 五、端到端流程

用户执行 `/ta:trading-analysis 600519.SS`：

1. orchestrator 识别 `600519.SS` → A 股
2. 注入 A 股市场上下文到各 agent prompt
3. 并行 dispatch 4 个 analyst：
   - market-analyst → t_mcp: get_stock_data + get_indicators
   - fundamentals-analyst → t_mcp: get_fundamentals + 财报
   - news-analyst → cn_mcp: get_cn_news + get_cn_global_news
   - sentiment-analyst → cn_mcp: get_cn_news + 上下文分析
4. 额外数据：cn_mcp: get_cn_dragon_tiger + get_cn_shareholder_changes
5. bull/bear debate → trader → risk debate → portfolio decision
6. 生成报告 (英文 + 中文)

## 六、测试策略

1. **单元测试**: cn_mcp 每个工具单独测试
2. **集成测试**: 茅台 (600519.SS) + 平安银行 (000001.SZ) 完整 pipeline
3. **对比测试**: 苹果 (AAPL) vs 茅台，对比报告质量

## 七、YAGNI — 明确不做

- ❌ 实时行情
- ❌ 港股/台股支持
- ❌ AKShare 数据缓存
- ❌ Ticker 自动补全 UI
- ❌ 多币种转换

## 八、Yahoo Finance A 股数据验证结果

用茅台 (600519.SS) 实测：

| 工具 | 结果 |
|------|------|
| get_stock_data | ✅ 日线数据完整 |
| get_indicators (RSI) | ✅ 指标计算正确 |
| get_fundamentals | ✅ 营收/利润率/ROE 齐全 |
| get_balance_sheet | ✅ 季度数据完整 |
| get_income_statement | ✅ 季度数据完整 |
| get_news | ⚠️ 返回不相关的英文新闻 |
| get_insider_transactions | ❌ 无数据 |
| get_global_news | ⚠️ 偏美国市场 |
