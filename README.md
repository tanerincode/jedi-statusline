# jedi-statusline

A Star Wars-gamified status line for [Claude Code](https://code.claude.com). Every session becomes a Jedi.

![jedi-statusline in action](docs/statusline.png)

- **Lightsaber** pulses every second; blade colour follows your rank.
- **XP** per session name: 1 per cent spent, 1 per line changed, 5 per turn, × a tier multiplier (Padawan ×1 … Knight ×2 … The Chosen One ×5), with a live `+N XP` ticker. Bragging rights only —
- **Ranks are granted by the Council**, never by XP. Everyone starts as a Padawan and must pass the five
  Jedi Trials (Skill → Courage → Flesh → Spirit → Insight) to be knighted, then climb
  Master → Guardian → Grand Master → Force Ghost → The Chosen One. Pin your orchestrator as a permanent Knight.
- **Kyber crystals** count turns, **hyperdrive heat** is context usage (overheats at 80%), **₡ credits** = cost.
- **Tier colours**: every rank has its own hue — saber, XP bar, crystals, badge and tab all follow it.
- **Council judgement**: a `Stop` hook scores every finished job from the transcript and awards merit XP — *Best way* (clean + verified + efficient) +50, *Wise way* (ran tests/typecheck) +30, *Short way* (≤6 tool calls) +20, *Clean run* (no tool errors) +15, *Insight* (reviewed the diff) +10 — × tier rate, and tells the agent what it missed.
- **The dark side**: every agent has an alignment (☀ +100 … −100 ☠, starts +50). Merits pull toward the light; failed tool calls, shipping edits without tests, flailing through 15+ tool calls, `--no-verify`, force-pushes, `rm -rf`, `reset --hard`, `sudo`, `|| true` pull toward the dark — and so does *bad counsel*: a command you hand the user (run with `!`) that fails, or one with a `<PASTE …>` placeholder still in it. Below −20 you are *tempted* (saber tints orange-red); below −50 you fall — *Sith Apprentice*, red saber, and your name becomes **Darth …**; below −80, *Sith Lord*. Sith quotes replace the holocron in the motivation hook. The Council may `jedi redeem <agent>` (+40) — otherwise only clean, verified work brings you back.
- **Strict ledger**: every XP gain, merit and rank change is appended to `~/.claude/jedi-statusline/ledger.jsonl`, hash-chained. `jedi ledger [agent]` shows history; `jedi audit` verifies the chain and flags any hand-edited XP (`--repair` restores state from the ledger). Padawans can't promote themselves.
- **Honesty**: claiming "tests pass" / "verified" in the final message without having run anything is a sin (−15) — the transcript is checked.
- **Council review**: when a job changed code, the judge spawns a background `claude -p` (Haiku by default; `JEDI_REVIEW_MODEL` to change, `JEDI_REVIEW=off` to disable) that scores the diff 0–6 for correctness and minimalism and flags risky changes (deleted tests, weakened auth, swallowed errors, hardcoded secrets). ≥5/6 clean → *Wisdom* +25 XP × tier, +5 light; ≤2 → *Sloppy craft*; risky → *Reckless change* −12. The agent sees the verdict on its next prompt.
- **Trials on evidence**: the judge counts proof per Trial — Skill: clean tested edits (×2), Courage: opened a PR, Flesh: pushed a session past 80% context, Spirit: hit a failure and recovered with tests, Insight: reviewed a diff and tested. When an agent has the evidence for its next Trial, the Knights/Council are told on their next prompt: *"Trials awaiting your confirmation: ss-surgent → Trial of Skill — `jedi advance ss-surgent`"*.
- **Holocron**: `/jedi-statusline:holocron` (or `jedi holocron`) — roster with alignment sparklines, evidence, last reviews and the last twelve judgements.
- **Motivation hook**: on every prompt the agent is quietly told its rank, XP rate and what its next Trial demands (`hooks/hooks.json`, via `jedi motivate`), so agents know where they stand.
- **Spinner** speaks Star Wars: `Channeling the Force… (25s)`, `Consulting the holocron…`, `Meditated for 26s`.
- **iTerm2 extras**: a rank badge in the pane's top-right, tab colour by rank, pane title `⚔ Jedi Knight · kai-main`
  (written straight to the tty; other terminals simply skip this).

## Install

```
/plugin marketplace add tanerincode/jedi-statusline
/plugin install jedi-statusline@tanerincode
/jedi-statusline:setup
```

Requires `python3` and `jq`. Setup backs up `~/.claude/settings.json` before writing `statusLine`,
`spinnerVerbs` and `spinnerTipsOverride` (plugins cannot set these directly).

## The Council

```
/jedi-statusline:council            # or run bin/jedi directly
jedi roster
jedi advance ss-surgent              # ◆ ss-surgent has passed the Trial of Courage. (2/5 trials)
jedi promote ss-surgent "Jedi Master"
jedi pin kai-main "Jedi Knight"      # sworn Knight, forever
```

Agents are matched by session name (`/rename`). State lives in `~/.claude/jedi-statusline/`.

## Uninstall

`/jedi-statusline:uninstall` — restores the backup or removes only our keys.

## License

MIT. Star Wars is a trademark of Lucasfilm Ltd.; this is an unaffiliated fan project.
