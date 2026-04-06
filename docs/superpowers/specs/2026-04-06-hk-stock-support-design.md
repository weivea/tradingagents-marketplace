# 港股基础支持设计

**日期**: 2026-04-06
**范围**: 基础可用级别 — 让港股分析能跑通完整的多 Agent 流水线
**方案**: 最小 MCP 工具 + 完整 Agent 规则注入

## 背景

当前系统支持美股（`ta` MCP 服务器，Yahoo Finance）和 A 股（`cn` MCP 服务器，AKShare + Yahoo Finance）。港股完全不支持：没有市场检测、没有港股工具、没有市场规则注入。如果用户分析港股 ticker，系统会将其当作美股处理，导致错误的市场规则和不完整的数据。

## 现状分析

**Yahoo Finance（`ta` 服务器）对港股的支持**：
- `get_stock_data(0700.HK)` ✅ — OHLCV 日线数据
- `get_indicators(0700.HK, ...)` ✅ — 技术指标（SMA、MACD、RSI 等）
- `get_fundamentals(0700.HK)` ✅ — 基本面数据
- `get_balance_sheet/cashflow/income(0700.HK)` ✅ — 财务报表
- `get_news(0700.HK, ...)` ⚠️ — 有新闻但精准度较低（泛亚洲新闻为主）
- `get_insider_transactions(0700.HK)` ❓ — 未测试，可能无数据

**AKShare 港股接口测试结果**（54 个函数，大部分可用）：
- 公司资料 ✅ — `stock_hk_company_profile_em()`, `stock_hk_security_profile_em()`
- 财务快照 ✅ — `stock_hk_financial_indicator_em()`
- 港股通持仓 ✅ — `stock_hsgt_individual_em()`
- 人气排名 ✅ — `stock_hk_hot_rank_em()`, `stock_hk_hot_rank_detail_em()`
- 港股新闻 ❌ — AKShare 没有对应函数

## 设计

### 1. 市场检测（`skills/trading-analysis/SKILL.md`）

在现有 A 股检测逻辑之后增加港股检测：

**港股识别规则**：
- ticker 以 `.HK` 结尾（如 `0700.HK`、`9988.HK`）
- 用户输入 4-5 位纯数字且带前导零（如 `00700`、`09988`）
- 用户提到港股公司名（如"腾讯"、"阿里巴巴-W"、"美团-W"）

**Ticker 格式转换**：
- Yahoo Finance 工具使用 `0700.HK` 格式（4 位数 + `.HK`）
- AKShare 港股工具使用 `00700` 格式（5 位数，前导零填充）

### 2. `cn` MCP 服务器新增港股工具

在 `plugins/cn_mcp/` 中新增 3 个工具，遵循现有 A 股工具的代码模式。

#### 2.1 `get_hk_stock_info(symbol: string)`

**功能**：获取港股公司基础信息 + 财务快照

**AKShare 函数**：
- `stock_hk_company_profile_em(symbol)` — 公司名称、英文名、行业、员工数、公司介绍
- `stock_hk_security_profile_em(symbol)` — 上市日期、发行价、每手股数、是否沪港通/深港通标的
- `stock_hk_financial_indicator_em(symbol)` — EPS、总市值、营收、净利润、PE/PB/ROE/ROA

**输入**：`symbol` — 港股代码（如 `"00700"`）
**输出**：`{"text": "markdown...", "data": {...}}` — 与 A 股 `get_cn_stock_info` 输出格式一致

**新增文件**：
- `plugins/cn_mcp/python/hk_stock_info.py` — Python 数据获取
- `plugins/cn_mcp/src/tools/hk-stock-info.ts` — TypeScript MCP 工具注册

#### 2.2 `get_hk_stock_connect(symbol: string)`

**功能**：获取港股通（南向资金）对该股的持仓变化

**AKShare 函数**：
- `stock_hsgt_individual_em(symbol)` — 持股日期、收盘价、持股数量、持股市值、持股占比

**输入**：`symbol` — 港股代码（如 `"00700"`）
**输出**：最近 30 个交易日的持仓变化趋势，包含：
- 持仓量变化方向（增持/减持/持平）
- 持股占比变化
- 持股市值变化
- 趋势总结（如"近 30 天南向资金持续增持，持股占比从 X% 升至 Y%"）

**新增文件**：
- `plugins/cn_mcp/python/hk_stock_connect.py`
- `plugins/cn_mcp/src/tools/hk-stock-connect.ts`

#### 2.3 `get_hk_hot_rank(symbol?: string)`

**功能**：获取港股人气/热度排名

**AKShare 函数**：
- 无 symbol：`stock_hk_hot_rank_em()` — Top 100 热门港股排名
- 有 symbol：`stock_hk_hot_rank_detail_em(symbol)` — 该股历史排名变化（近 120 天）

**输入**：`symbol`（可选）— 港股代码
**输出**：
- 无 symbol：Top 20 热门港股列表（代码、名称、排名、最新价、涨跌幅）
- 有 symbol：该股近期排名趋势

**新增文件**：
- `plugins/cn_mcp/python/hk_hot_rank.py`
- `plugins/cn_mcp/src/tools/hk-hot-rank.ts`

#### 2.4 TypeScript 注册

在 `plugins/cn_mcp/src/index.ts` 中注册 3 个新工具，遵循现有模式（导入 tool 定义 + 注册到 server）。

### 3. Agent 层港股规则注入

修改 `skills/trading-analysis/SKILL.md` 中各 agent 的港股特定规则。

#### 3.1 工具路由规则（港股检测后注入）

```
当 ticker 为港股（.HK 后缀）时：

行情 & 技术面（ta 服务器）：
- get_stock_data(XXXX.HK, ...) — 日线 OHLCV
- get_indicators(XXXX.HK, indicator, date) — 技术指标

基本面（ta 服务器）：
- get_fundamentals(XXXX.HK) — 基本面概览
- get_balance_sheet(XXXX.HK) — 资产负债表
- get_cashflow(XXXX.HK) — 现金流量表
- get_income_statement(XXXX.HK) — 利润表

新闻（ta 服务器）：
- get_news(XXXX.HK, start, end) — 英文新闻（精准度有限）
- get_global_news(date) — 全球宏观新闻

港股特有数据（cn 服务器）：
- get_hk_stock_info(XXXXX) — 公司资料 + 财务快照
- get_hk_stock_connect(XXXXX) — 港股通持仓变化
- get_hk_hot_rank(XXXXX) — 人气排名

注意：不使用 A 股专用工具（get_cn_news、get_cn_dragon_tiger、get_cn_shareholder_changes）
```

#### 3.2 Market Analyst 港股规则

```
港股（HKEX）市场规则：
- 交易时段：早盘 9:30-12:00，午盘 13:00-16:00（HKT，UTC+8）
- 收市竞价时段：16:00-16:10
- 无涨跌停限制（与 A 股 ±10% 不同，港股可以单日涨跌幅不受限）
- T+2 结算制度
- 以 HKD 计价
- 每手股数因股票而异（不像 A 股统一 100 股/手）
- 港股支持卖空交易
- 注意大型科技股可能同时在美国有 ADR 上市（如阿里 BABA/9988.HK）
```

#### 3.3 Fundamentals Analyst 港股规则

```
港股财务分析规则：
- 港股采用 IFRS 国际会计准则（非美国 GAAP 或中国 GAAP）
- 财报通常以 HKD 或 USD 计价（注意标明货币单位）
- 关注是否为"同股不同权"公司（带 -W 标记，如腾讯、美团、小米）
- 区分 H 股（内地注册港股上市）、红筹股（海外注册但主要业务在内地）、本地公司
- 使用 get_hk_stock_info 获取港股特有财务指标（EPS、PE/PB/ROE 等）
- 部分港股公司收入以人民币为主但以 HKD 报告，需注意汇率影响
```

#### 3.4 Sentiment Analyst 港股规则

```
港股情绪分析规则：
- 使用 get_hk_hot_rank 获取人气排名（东方财富数据）
- 使用 get_hk_stock_connect 获取港股通持仓变化：
  - 南向资金持续增持 = 内地资金看好信号
  - 南向资金持续减持 = 内地资金看空信号
  - 持股占比变化是更重要的指标（绝对值受股价影响）
- 港股新闻数据来自 Yahoo Finance，以英文为主，精准度有限
- 港股市场受美股和 A 股双重影响，关注两个市场的联动
```

#### 3.5 News Analyst 港股规则

```
港股新闻分析规则：
- 使用 get_news(ticker) 获取英文新闻（Yahoo Finance，精准度一般）
- 使用 get_hk_stock_connect 获取港股通资金流向（替代 A 股龙虎榜 / 美股 insider transactions）
- get_hk_stock_info 中包含是否为港股通标的信息
- 不使用 A 股专用工具：get_cn_dragon_tiger、get_cn_shareholder_changes、get_cn_news
- 关注港股独有风险因素：中美关系、监管政策变化、退市风险等
```

### 4. 报告生成

- 港股分析报告同样生成中英双语版本（`*_en.md` + `*_zh.md`）
- 报告头部标注市场为 "HKEX / 港交所"
- 货币单位使用 HKD（如适用标注 "以 HKD 计价"）
- 如有 ADR 双重上市，在报告中注明

## 涉及文件

### 新增文件（6 个）
| 文件 | 说明 |
|------|------|
| `plugins/cn_mcp/python/hk_stock_info.py` | 港股公司资料 Python 模块 |
| `plugins/cn_mcp/python/hk_stock_connect.py` | 港股通持仓 Python 模块 |
| `plugins/cn_mcp/python/hk_hot_rank.py` | 港股人气排名 Python 模块 |
| `plugins/cn_mcp/src/tools/hk-stock-info.ts` | 港股公司资料 MCP 工具 |
| `plugins/cn_mcp/src/tools/hk-stock-connect.ts` | 港股通持仓 MCP 工具 |
| `plugins/cn_mcp/src/tools/hk-hot-rank.ts` | 港股人气排名 MCP 工具 |

### 修改文件（最多 7 个）
| 文件 | 修改内容 |
|------|---------|
| `plugins/cn_mcp/src/index.ts` | 注册 3 个新港股工具 |
| `plugins/cn_mcp/python/__init__.py` | 导出新模块（如需要） |
| `skills/trading-analysis/SKILL.md` | 添加港股市场检测 + 工具路由 + 各 agent 港股规则 |
| `agents/market-analyst.md` | 添加港股市场规则（如该文件有独立规则） |
| `agents/fundamentals-analyst.md` | 添加港股财务规则（如该文件有独立规则） |
| `agents/sentiment-analyst.md` | 添加港股情绪分析规则（如该文件有独立规则） |
| `agents/news-analyst.md` | 添加港股新闻分析规则（如该文件有独立规则） |

注：agent 规则可能集中在 `SKILL.md` 中而非分散在各 agent 文件中，具体取决于现有 A 股规则的放置位置。实现时以实际代码结构为准。

## 已知局限

1. **港股新闻精准度有限**：Yahoo Finance 对 `.HK` ticker 返回的新闻以泛亚洲内容为主，不如 A 股的 AKShare `stock_news_em` 精准。后续可考虑接入东方财富港股频道。
2. **分钟线数据不可用**：AKShare 的 `stock_hk_hist_min_em()` 存在连接错误，无法获取港股分钟线。
3. **港股股东数据缺失**：AKShare 没有港股的前十大股东接口，无法提供类似 A 股 `get_cn_shareholder_changes` 的功能。
4. **`get_insider_transactions` 未验证**：Yahoo Finance 的 insider transactions 工具对港股可能无数据（HKEX 的披露体系与 SEC 不同）。

## 测试计划

1. 验证 `cn` MCP 服务器 3 个新工具可正常返回数据（用腾讯 00700 测试）
2. 验证 `ta` 服务器现有工具对 `.HK` ticker 的兼容性（price、indicators、fundamentals）
3. 端到端测试：对腾讯（0700.HK）运行完整的 trading-analysis 流水线
4. 对比测试：确保新增港股支持不影响现有美股和 A 股分析流程
