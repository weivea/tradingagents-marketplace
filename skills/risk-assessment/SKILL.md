---
name: risk-assessment
description: Run the 3-way risk debate (aggressive/conservative/neutral) on the trader's plan.
---

# Risk Assessment — Three-Way Debate

Orchestrate a structured risk debate between Aggressive, Conservative, and Neutral risk analysts.

## When to Use

After the Trader makes a decision, when you need risk assessment before the final portfolio decision.

## Prerequisites

- The trader's investment plan/decision
- All 4 analyst reports

## Process (configurable rounds, default 1)

For each round, cycle through sequentially:

1. **Dispatch Aggressive Analyst** sub-agent (use `ta:risk-aggressive` agent) with:
   - Trader's decision, all analyst reports
   - Debate history, last conservative & neutral responses
   - Instruction to start with `**Aggressive Analyst:**`

2. **Dispatch Conservative Analyst** sub-agent (use `ta:risk-conservative` agent) with:
   - Trader's decision, all analyst reports
   - Debate history, last aggressive & neutral responses
   - Instruction to start with `**Conservative Analyst:**`

3. **Dispatch Neutral Analyst** sub-agent (use `ta:risk-neutral` agent) with:
   - Trader's decision, all analyst reports
   - Debate history, last aggressive & conservative responses
   - Instruction to start with `**Neutral Analyst:**`

Accumulate the full risk debate history after each turn.

## Output

The complete risk debate history for the Portfolio Manager to synthesize.
