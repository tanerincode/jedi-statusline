---
name: council
description: Manage Jedi ranks of Claude Code sessions/agents — roster, advance one Trial, promote, demote, reset, pin. Use when the user says things like "promote ss-surgent", "who is on the roster", "knight this agent", "/jedi-statusline:council".
---

# /jedi-statusline:council

Ranks are granted by the Council, never earned by XP. Every agent starts as a Padawan and must pass the five Jedi Trials (Skill → Courage → Flesh → Spirit → Insight) to be knighted. Use the bundled tool:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/jedi roster
${CLAUDE_PLUGIN_ROOT}/bin/jedi advance <agent>          # passes the next Trial / climbs one rank
${CLAUDE_PLUGIN_ROOT}/bin/jedi demote  <agent>          # one step down
${CLAUDE_PLUGIN_ROOT}/bin/jedi reset   <agent>          # plain Padawan
${CLAUDE_PLUGIN_ROOT}/bin/jedi promote <agent> "<Rank>" # Council override, jumps straight to a rank
${CLAUDE_PLUGIN_ROOT}/bin/jedi pin     <agent> "<Rank>" # never changes (your orchestrator)
```

`<agent>` is the session name shown by `/rename` (prefix match). Ranks: Youngling, Padawan, Padawan ◆ … ◆◆◆◆◆, Jedi Knight, Jedi Master, Jedi Guardian, Grand Master, Force Ghost, The Chosen One.

Prefer `advance` (one step at a time) unless the user explicitly asks to jump. Print the tool's output back to the user verbatim — it is the ceremony.
