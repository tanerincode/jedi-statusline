---
name: uninstall
description: Remove the jedi-statusline status line and spinner settings from ~/.claude/settings.json, restoring the backup made by setup. Use when the user runs /jedi-statusline:uninstall or asks to turn the Star Wars theme off.
---

# /jedi-statusline:uninstall

1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/bin/jedi unsetup` — restores `settings.json.pre-jedi-statusline` if present, otherwise removes only our keys; also clears the iTerm2 badge/tab colour.
2. Ask before deleting XP history in `~/.claude/jedi-statusline/` — the user may want to keep the roster and ledger.
