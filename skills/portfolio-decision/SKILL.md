---
name: portfolio-decision
description: Have the Portfolio Manager make the final trading decision based on the risk debate.
---

# Portfolio Decision

The Portfolio Manager synthesizes all analysis and the risk debate to deliver the final trading decision.

## When to Use

After the risk debate completes, as the final step of the trading analysis pipeline.

## Prerequisites

- Full risk debate history
- Trader's proposed plan
- All 4 analyst reports

## Execution

Dispatch the **Portfolio Manager** sub-agent (use `tradingagents:portfolio-manager` agent) with:
- Risk debate history
- Trader's plan
- All analyst reports
- Instruction to output:
  1. **Rating**: exactly one of Buy / Overweight / Hold / Underweight / Sell
  2. **Executive Summary**: entry strategy, position sizing, risk levels, time horizon
  3. **Investment Thesis**: detailed reasoning

## Output

The final trading decision with rating, executive summary, and investment thesis.

## Signal Extraction

After receiving the Portfolio Manager's output, extract the single rating word:
- **BUY**, **OVERWEIGHT**, **HOLD**, **UNDERWEIGHT**, or **SELL**
