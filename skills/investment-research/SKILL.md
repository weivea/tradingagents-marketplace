---
name: investment-research
description: Run the bull/bear investment debate and produce an investment plan. Requires analyst reports as input context.
---

# Investment Research — Bull/Bear Debate

Orchestrate a structured debate between Bull and Bear researchers, then have the Research Manager produce an investment plan.

## When to Use

After collecting analyst reports (market, sentiment, news, fundamentals), when you need to run the investment debate phase.

## Prerequisites

You must already have the 4 analyst reports:
- Market report
- Sentiment report
- News report
- Fundamentals report

## Process

### Bull/Bear Debate (configurable rounds, default 1)

For each debate round:

1. **Dispatch Bull Researcher** sub-agent (use `ta:bull-researcher` agent) with:
   - All 4 analyst reports
   - Debate history so far
   - Last bear argument (if any)
   - Instruction to start response with `**Bull Analyst:**`

2. **Dispatch Bear Researcher** sub-agent (use `ta:bear-researcher` agent) with:
   - All 4 analyst reports
   - Debate history so far
   - Last bull argument
   - Instruction to start response with `**Bear Analyst:**`

Accumulate the debate history after each turn.

### Research Manager Decision

After all debate rounds, dispatch the **Research Manager** sub-agent (use `ta:research-manager` agent) with:
- Full debate history
- All 4 analyst reports
- Instruction to commit to Buy/Sell/Hold with rationale and strategic actions

## Output

The Research Manager's investment plan containing recommendation, rationale, and strategic actions.
