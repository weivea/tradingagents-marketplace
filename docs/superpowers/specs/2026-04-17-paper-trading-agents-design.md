# Paper Trading Agents — Design Spec

**Date:** 2026-04-17
**Status:** Draft, pending user review

## Goal

在 `/plugins` 下新增 **4 个 plugin**，构建一个"三位个性不同的模拟炒股选手 + 共享模拟交易 MCP"的闭环：

- 三位独立 agent（激进 / 中性 / 保守），每人一个 plugin
- 一个全新的 `paper_trading_mcp` 提供模拟交易能力（多账户、多币种、限价 / 止损单、手续费、A 股 T+1）
- 三位选手每日用 `cn_mcp` / `t_mcp` 调研 + `paper_trading_mcp` 下单
- 下午 5 点三人聚在一起讨论今日心得，产出一份 markdown 纪要
- **触发方式：纯手动 slash command**（无 cron、无 daemon、无 hooks 自动调度）

## Non-Goals

- 不做真实券商对接、不做真实资金交易
- 讨论结果 **不** 反馈到第二天的交易决策（讨论是氛围组）
- 不做自动调度；用户自己每天发命令
- 不复用或替换现有 `risk-aggressive` / `risk-conservative` / `risk-neutral` agent（那些用于 research-stage 风险辩论，职责不同）

## Plugin Layout

```
plugins/
├── paper_trading_mcp/             # MCP server + 讨论编排命令
│   ├── .claude-plugin/plugin.json
│   ├── src/                        # TS MCP wrapper（对齐 cn_mcp 架构）
│   ├── python/                     # 撮合引擎 + SQLite
│   ├── commands/run-discussion.md  # /paper-trading:run-discussion
│   ├── package.json
│   ├── pyproject.toml
│   └── README.md
├── trader_aggressive/
│   ├── .claude-plugin/plugin.json
│   ├── agents/trader-aggressive.md
│   ├── commands/trade-day.md       # /trader-aggressive:trade-day
│   ├── commands/join-discussion.md # /trader-aggressive:join-discussion（被 run-discussion 调）
│   └── README.md
├── trader_conservative/            # 同构
└── trader_neutral/                 # 同构
```

## Component 1 — `paper_trading_mcp`

### 职责

唯一的账户 / 订单 / 持仓真相来源。三位 agent 的所有资金流动都通过它完成。

### 技术栈

- Node MCP server（TypeScript，`@modelcontextprotocol/sdk`），架构对齐现有 `cn_mcp`
- Python 业务层（撮合引擎、费率规则、T+1 结算）
- SQLite 持久化：`~/.paper_trading/paper.db`
- 文件产物：`~/.paper_trading/journals/` 和 `~/.paper_trading/discussions/`

### 账户模型（多账户、多币种）

三位选手各一个账户，`account_id` ∈ {`aggressive`, `conservative`, `neutral`}。

**初始资金（固定统一）**：
- ¥1,000,000（人民币，A 股）
- HK$1,000,000（港币，港股）
- $100,000（美元，美股）

账户首次被访问时自动创建并注资。

### 市场与规则

`market` 字段 ∈ {`CN`, `HK`, `US`}，决定费率和结算规则：

| 市场 | 结算 | 手续费（默认，可通过 plugin config 覆盖） |
|---|---|---|
| CN（A 股） | **T+1**（买入当日 available_qty=0，次交易日解锁）；印花税卖出 0.05% | 佣金 0.025%（最低 ¥5） |
| HK（港股） | T+0 | 佣金 0.08%（最低 HK$5）+ 印花税 0.1%（双边） |
| US（美股） | T+0 | $0.005/股（最低 $1） |

所有费率写在 Python 层 `fees.py` 一个常量字典里，首版不做实时汇率换算。

### Schema（SQLite）

```sql
accounts (
  account_id     TEXT PRIMARY KEY,
  cash_cny       REAL NOT NULL,
  cash_hkd       REAL NOT NULL,
  cash_usd       REAL NOT NULL,
  created_at     TEXT
)

positions (
  id             INTEGER PRIMARY KEY,
  account_id     TEXT,
  symbol         TEXT,
  market         TEXT,            -- CN | HK | US
  qty            REAL,
  available_qty  REAL,            -- T+1 锁定后的可卖数量
  avg_cost       REAL,
  currency       TEXT,
  UNIQUE(account_id, symbol, market)
)

orders (
  id             INTEGER PRIMARY KEY,
  account_id     TEXT,
  symbol         TEXT,
  market         TEXT,
  side           TEXT,            -- buy | sell
  order_type     TEXT,            -- market | limit | stop
  qty            REAL,
  price          REAL,            -- 限价/止损的触发价，市价单为 null
  ref_price      REAL,            -- agent 调用时传入的参考价（撮合用）
  status         TEXT,            -- pending | filled | cancelled | rejected
  filled_price   REAL,
  filled_qty     REAL,
  fee            REAL,
  submitted_at   TEXT,
  filled_at      TEXT,
  settle_date    TEXT             -- T+1 解锁日期
)

trade_log (
  id             INTEGER PRIMARY KEY,
  ts             TEXT,
  account_id     TEXT,
  event          TEXT,            -- submit | fill | cancel | reject | settle
  payload_json   TEXT
)
```

`pending_orders` 不建独立表，靠 `orders WHERE status='pending'` 视图过滤。

### MCP Tools

| tool | 参数 | 行为 |
|---|---|---|
| `place_order` | account_id, symbol, market, side, qty, order_type, price?, ref_price | 市价单立即按 `ref_price` 撮合；limit/stop 存入 pending |
| `cancel_order` | account_id, order_id | 取消一笔 pending |
| `get_portfolio` | account_id, price_map? | 现金 + 持仓；若传 price_map 计算浮动市值 |
| `get_positions` | account_id | 仅持仓清单 |
| `get_cash` | account_id | 三币种现金 |
| `get_pending_orders` | account_id | 所有未成交挂单 |
| `get_order_history` | account_id, start_date?, end_date? | 历史成交 |
| `get_pnl` | account_id, date? | 当日/累计已实现 + 浮动盈亏 |
| `tick_pending_orders` | account_id, price_map | agent 在 trade-day 开头调一次：用最新价 sweep 所有挂单触发撮合；然后结算 T+1（把昨日买入释放为 available）|
| `append_journal` | account_id, date, markdown | 追加今日交易日记 |
| `read_journal` | account_id, date | 读取指定日期 journal（讨论时用）|
| `append_discussion` | date, speaker, markdown | 讨论纪要 append 一段发言 |
| `read_discussion` | date | 读当日讨论纪要（给后一位 agent 回应用）|
| `init_discussion` | date, pnl_summary | 讨论开始时建文件、写 header + 三人今日 PnL |

### 撮合逻辑

- **市价单**：立即用 `ref_price` 成交，扣费，更新 positions / cash；A 股记录 `settle_date` = 次交易日
- **限价单**：保存到 orders 表为 pending；下次 `tick_pending_orders(price_map)` 被调用时，若 price_map 中该 symbol 的最新价满足方向条件（buy: price ≤ limit；sell: price ≥ limit）则撮合成交
- **止损单**：同上，触发条件反向（sell-stop: price ≤ stop；buy-stop: price ≥ stop）
- **所有成交同时写入 `trade_log`**

### 错误处理

MCP tool 不抛异常，返回结构化结果：

```json
{ "ok": false, "error_code": "INSUFFICIENT_CASH" | "T1_LOCKED" | "MISSING_REF_PRICE" | "INVALID_MARKET" | ..., "message": "..." }
```

Agent 自己判断并把失败写入 journal（"今天本来想买 XX，但被 T+1 挡住了"）。

### Slash Command

`/paper-trading:run-discussion` — 编排 17:00 讨论（详见 Component 3）

## Component 2 — 三位 Trader Agent Plugin

### 共同结构

```
plugins/trader_<style>/
├── .claude-plugin/plugin.json
├── agents/trader-<style>.md         # 人设
├── commands/trade-day.md            # /trader-<style>:trade-day
├── commands/join-discussion.md      # /trader-<style>:join-discussion
└── README.md
```

三个 plugin 代码/目录同构，**唯一差异是 agent prompt 的人设与约束**。

### 人设差异

| 维度 | Aggressive | Neutral | Conservative |
|---|---|---|---|
| 单票仓位上限 | 40% | 20% | 10% |
| 总仓位上限 | 100% | 80% | 50% |
| 偏好订单类型 | market（追热点） | market + limit 平衡 | 以 limit 低吸为主 |
| 止损线 | -8% | -5% | -3% |
| 数据偏好 | 龙虎榜、港股热度、sentiment、技术面 | 基本面 + 技术面 + 新闻 全面 | 基本面、现金流、宏观新闻、balance sheet |
| 发言风格 | 激情、口号、敢 all-in | 冷静、数据说话 | 谨慎、反复强调风险 |
| 常用 cn_mcp 工具 | `get_cn_dragon_tiger`, `get_hk_hot_rank`, `get_cn_global_news` | `get_cn_stock_info`, `get_cn_news`, `get_cn_shareholder_changes` | `get_hk_stock_connect`, `get_cn_shareholder_changes` |
| 常用 t_mcp 工具 | `get_indicators(rsi/macd)`, `get_news` | `get_fundamentals`, `get_indicators`, `get_news` | `get_balance_sheet`, `get_cashflow`, `get_income_statement` |

人设边界作为 **硬约束** 写入 agent prompt；下单前 agent 必须自检"是否违反仓位上限"。

### `/trade-day` Workflow

由用户手动触发（早盘 / 午盘 / 美股盘各跑一次）。Agent 行为：

1. 调用 `tick_pending_orders(account_id, price_map)`（price_map 先通过轻量行情查询构造；首版允许传空 map，让引擎只做 T+1 结算）
2. 调用 `get_portfolio` + `get_pending_orders` 查看当前状态
3. 判断当前时间适合交易哪个市场（A 股 09:30-15:00、港股 09:30-16:00、美股 21:30-04:00），选中一个市场
4. 按人设偏好用 `cn_mcp` / `t_mcp` 调研 watchlist 外 / 自选标的
5. 决策并调用 `place_order`（市价单必须传 `ref_price`）
6. 调用 `append_journal` 写入今日决策 + 理由（markdown 格式）

### `/join-discussion` Workflow

由 `/paper-trading:run-discussion` 间接调用，不直接面向用户。Agent 行为：

1. 读自己今日 `read_journal(account_id, today)`
2. 读讨论文件当前内容 `read_discussion(today)`（看前面人说了什么）
3. 按人设语气发言；若前面有人点名自己，要回应
4. 调用 `append_discussion(today, style, markdown)` 追加一段

## Component 3 — 讨论编排

### `/paper-trading:run-discussion`

纯手动触发的 slash command（放在 `paper_trading_mcp` plugin 的 `commands/run-discussion.md`）。

流程（在一个 Claude session 内顺序执行，无并发）：

1. 调用 `get_pnl` × 3 拿到三人今日战绩
2. 调用 `init_discussion(today, pnl_summary)` 建文件、写 header
3. **第 1 轮（开场陈述）**：依次唤起 `trader-aggressive:join-discussion` → `trader-neutral:join-discussion` → `trader-conservative:join-discussion`
4. **第 2 轮（互相回应）**：同样顺序再走一遍
5. **收官总结**：由 `trader-neutral` 单独写一段今日总结

产出文件示例：

```markdown
# 2026-04-17 交易心得讨论

**今日战绩** · 激进 +2.3% · 中性 +0.5% · 保守 -0.1%

---
**第一轮**

**激进选手：** 哥们今天追了两只龙虎榜股 ...

**中性选手：** 数据来看 ...

**保守选手：** 我坚持低吸 ...

---
**第二轮**

**激进选手：** 保守你那点仓位能挣几个钱 ...

...

---
**今日总结（中性）：** ...
```

### 错误处理

- 某位 agent 调用失败 → 在纪要追加一行 `（XX 选手今日缺席）` 并继续
- 整个命令可重复执行（幂等性：`init_discussion` 若文件已存在则报错，用户可带 `--force` 重建）

## 使用流程（用户视角）

纯手动，无自动调度：

```
早上 09:35   /trader-aggressive:trade-day
             /trader-neutral:trade-day
             /trader-conservative:trade-day

午后 14:30   （同上，三位各跑一次，agent 自己决定换港股还是补仓 A 股）

晚上 21:45   （同上，美股档）

下午 17:00   /paper-trading:run-discussion
             ↑ 一键生成当日讨论纪要
```

README 会给出推荐节奏，用户也可以自由选择只跑其中一部分。

## 测试策略

### `paper_trading_mcp`（pytest）

- 撮合：市价/限价/止损 成交正确性
- 手续费：三个市场各走一遍
- T+1：A 股买入当日不可卖、次交易日 `tick_pending_orders` 后可卖
- 多币种：买 A 股扣 CNY、买港股扣 HKD、买美股扣 USD
- 余额不足 / T1 锁定 / 缺 ref_price 的错误码正确

### 三位 agent（prompt snapshot）

- 给定 portfolio + 行情快照，断言：
  - 激进单票仓位 > 20%、总仓接近满仓、偏爱 market 单
  - 保守单票仓位 ≤ 10%、留大量现金、多 limit 单
  - 中性居中
- 止损线生效：持仓跌到止损线下，trade-day 必产出卖出订单

### 讨论编排

- mock 三位 agent 的 `join-discussion` 输出，验证纪要文件 header、三人 PnL、两轮发言、收官总结的顺序和格式
- 某位 agent 失败时"缺席"提示正确出现

## 开放问题 / 未来扩展

- 实时行情 price_map 由 agent 现场构造，首版没有统一行情源 —— 若后续需要更精确的 `tick_pending_orders`，可增加轻量行情服务
- 若讨论结果要反馈到第二天的交易（问题 5 方案 3/4），未来扩展时需要在 journal 中增加 "next_day_watchlist" 段落并让 trade-day 读取
- 手续费/资金规模如需差异化（问题 6 方案 3），可通过 plugin config 覆盖 `accounts` 初始化值
