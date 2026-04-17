---
description: Run the aggressive trader's daily trading cycle (settle T+1, check stop-losses, scan for new ideas, place orders, write journal).
---

Invoke the `trader-aggressive` agent using the Agent tool with `subagent_type="trader-aggressive"` and this prompt:

> "Run your `/trader-aggressive:trade-day` workflow as described in your agent prompt. Today's date is TODAY (fill in YYYY-MM-DD). Follow all 7 steps, end with a 1-sentence summary."

After the agent returns, relay its summary to the user.
