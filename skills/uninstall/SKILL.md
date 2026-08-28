---
name: uninstall
description: Remove the jedi-statusline status line and spinner settings from ~/.claude/settings.json, restoring the backup made by setup. Use when the user runs /jedi-statusline:uninstall or asks to turn the Star Wars theme off.
---

# /jedi-statusline:uninstall

1. If `~/.claude/settings.json.pre-jedi-statusline` exists, offer to restore it wholesale. Otherwise remove only our keys:

```bash
jq 'del(.statusLine, .spinnerVerbs, .spinnerTipsOverride)' ~/.claude/settings.json > ~/.claude/settings.json.tmp && mv ~/.claude/settings.json.tmp ~/.claude/settings.json
```

2. Ask before deleting XP history in `~/.claude/jedi-statusline/` — the user may want to keep the roster.
3. iTerm2: badge/tab colour reset on the next new tab; or run `printf '\e]1337;SetBadgeFormat=\a\e]6;1;bg;*;default\a'`.
