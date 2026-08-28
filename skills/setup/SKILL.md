---
name: setup
description: Install the jedi-statusline status line, Star Wars spinner verbs and tips into the user's ~/.claude/settings.json (with a backup). Use when the user runs /jedi-statusline:setup or asks to enable the Star Wars status line.
---

# /jedi-statusline:setup

Plugins cannot set `statusLine` or `spinnerVerbs` themselves, so this skill writes them to the user's settings with their consent.

1. Tell the user exactly what will change in `~/.claude/settings.json`: the `statusLine`, `spinnerVerbs` and `spinnerTipsOverride` keys. Ask for a yes before writing.
2. Back up: `cp ~/.claude/settings.json ~/.claude/settings.json.pre-jedi-statusline`
3. Merge with jq (do not overwrite other keys):

```bash
jq --arg cmd "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/statusline.py" '
  .statusLine = {"type":"command","command":$cmd,"padding":1,"refreshInterval":1}
  | .spinnerVerbs = {"mode":"replace","verbs":["Meditating","Channeling the Force","Consulting the holocron","Calculating the jump to hyperspace","Force-sensing","Negotiating with the Hutts","Aligning the kyber crystal","Scanning the Death Star plans","Deflecting blaster fire","Reading the Jedi archives","Levitating","Recalibrating the deflector shields","Mind-tricking","Bypassing the compressor","Dueling","Pondering the prophecy","Balancing the Force","Sensing a disturbance","Powering up the Falcon"]}
  | .spinnerTipsOverride = ["Do. Or do not. There is no try.","These are not the droids you are looking for.","Never tell me the odds.","Stay on target.","Patience, young Padawan.","The Force is strong with this one.","Punch it, Chewie."]
' ~/.claude/settings.json > ~/.claude/settings.json.tmp && mv ~/.claude/settings.json.tmp ~/.claude/settings.json
```

4. Optionally pin the user's orchestrator: `${CLAUDE_PLUGIN_ROOT}/bin/jedi pin <session-name> "Jedi Knight"`.
5. Explain: the status line appears on the next refresh; ranks are granted with `/jedi-statusline:council`; XP lives in `~/.claude/jedi-statusline/state.json`. Requires `python3` and `jq`. iTerm2 users also get a badge, tab colour and pane title.
