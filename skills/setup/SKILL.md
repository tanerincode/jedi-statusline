---
name: setup
description: Install the jedi-statusline status line and Star Wars spinner into the user's ~/.claude/settings.json (backup kept), and choose whether Council reviews (claude -p, small cost) are on. Use when the user runs /jedi-statusline:setup or asks to enable the Star Wars status line.
---

# /jedi-statusline:setup

Plugins cannot set `statusLine` or `spinnerVerbs` themselves, so this writes them to the user's settings with consent.

1. Tell the user what will change in `~/.claude/settings.json` (`statusLine`, `spinnerVerbs`, `spinnerTipsOverride`; a backup is kept at `settings.json.pre-jedi-statusline`) and ask two questions:
   - **Council reviews?** Each code-changing job is reviewed in the background by `claude -p` (Haiku by default) — about $0.01 per job. Default OFF. Only turn on with an explicit yes.
   - **Pin an orchestrator?** e.g. their main session name as a permanent Jedi Knight (optional).
2. Run (pick the flags from the answers):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/bin/jedi setup --reviews off
python3 ${CLAUDE_PLUGIN_ROOT}/bin/jedi setup --reviews on --pin kai-main "Jedi Knight"
```

3. Relay the tool's output. Note: hooks (judgement, motivation) attach to sessions started from now on; already-running sessions must be restarted. Requires `python3`. iTerm2 users also get a badge, tab colour and pane title; other terminals just get the status line.
