---
name: trading-decision
description: Have the Trader agent make a trading decision based on the research team's investment plan.
---

# Trading Decision

The Trader evaluates the investment plan and all analyst reports to produce a concrete trading proposal.

## When to Use

After the Research Manager produces an investment plan, when you need the Trader's decision.

## Prerequisites

- Investment plan from the Research Manager
- All 4 analyst reports

## Execution

Dispatch the **Trader** sub-agent (use `ta:trader` agent) with:
- Investment plan
- Market, sentiment, news, fundamentals reports
- Instruction to end with `FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**`

## Output

The trader's detailed analysis ending with `FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**`.
