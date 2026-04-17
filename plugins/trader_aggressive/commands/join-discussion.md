---
description: Have the aggressive trader contribute one turn to today's discussion (invoked by /paper-trading:run-discussion, not directly by users).
---

Invoke the `trader-aggressive` agent using the Agent tool with `subagent_type="trader-aggressive"` and a prompt that passes TODAY's date and instructs the agent to execute its `/trader-aggressive:join-discussion` workflow (one turn, in character, with a `next_speaker` directive).
