#!/usr/bin/env python3
"""jedi-statusline — a Star Wars-gamified Claude Code status line.

Reads Claude Code's statusline JSON on stdin, keeps persistent XP in
~/.claude/jedi-statusline/state.json and renders a three-line animated status bar:
lightsaber ignition, Force rank, XP bar, kyber crystals for turns,
hyperdrive heat (context), credits, branch, holocron quote.
"""
import json, os, sys, time, random, subprocess

STATE = os.path.expanduser("~/.claude/jedi-statusline/state.json")

def c(n, s): return f"\033[38;5;{n}m{s}\033[0m"
def b(s):    return f"\033[1m{s}\033[0m"
BLUE, GREEN, RED, GOLD, DIM, PURPLE, CREAM, CYAN = 39, 82, 196, 220, 244, 135, 230, 51

RANKS = [
    ("Youngling",      "sensitive to the Force",  0,      BLUE),
    ("Padawan",        "learner",                 300,    BLUE),
    ("Padawan ◆",      "Trial of Skill passed",   400,    BLUE),
    ("Padawan ◆◆",     "Trial of Courage passed", 500,    BLUE),
    ("Padawan ◆◆◆",    "Trial of the Flesh passed", 600,  BLUE),
    ("Padawan ◆◆◆◆",   "Trial of Spirit passed",  700,    BLUE),
    ("Padawan ◆◆◆◆◆",  "Trial of Insight passed", 800,    BLUE),
    ("Jedi Knight",    "guardian of peace",       1_000,  GREEN),
    ("Jedi Master",    "seat on the Council",     2_500,  GREEN),
    ("Jedi Guardian",  "blade of the Order",      6_000,  CYAN),
    ("Grand Master",   "the Order's wisdom",      14_000, PURPLE),
    ("Force Ghost",    "one with the Force",      30_000, CYAN),
    ("The Chosen One", "balance",                 60_000, GOLD),
]

QUOTES = [
    "Do. Or do not. There is no try. — Yoda",
    "The Force will be with you. Always. — Obi-Wan",
    "Never tell me the odds. — Han Solo",
    "In my experience there is no such thing as luck. — Obi-Wan",
    "Fear is the path to the dark side. — Yoda",
    "I find your lack of faith disturbing. — Vader",
    "Your focus determines your reality. — Qui-Gon",
    "Great, kid. Don't get cocky. — Han Solo",
    "The greatest teacher, failure is. — Yoda",
    "This is the way. — Din Djarin",
    "I've got a bad feeling about this. — everyone",
    "It's a trap! — Admiral Ackbar",
]

SABER  = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█", "▉", "▊", "▋", "▌", "▍", "▎"]   # blade pulsing
HILT   = "╞"

def load():
    try:
        with open(STATE) as f: return json.load(f)
    except Exception:
        return {"xp": 0, "frame": 0, "sessions": {}, "levelup_at": 0, "quote_i": 0, "quote_t": 0}

def save(st):
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f: json.dump(st, f)
    os.replace(tmp, STATE)

# Ranks are granted by the Council, not earned by XP.
# kai-* is always Jedi Knight; everyone else is a Padawan unless Kai promotes them
# (via `python3 jedi promote <agent> "<Rank>"`, stored in promotions.json).
PROMOS = os.path.expanduser("~/.claude/jedi-statusline/promotions.json")
DEFAULT_RANK = 1   # Padawan
PADAWAN, KNIGHT = 1, 7

def load_promos():
    try:
        with open(PROMOS) as f: return json.load(f)
    except Exception:
        return {}

def rank_index(v):
    if isinstance(v, int): return max(0, min(len(RANKS) - 1, v))
    names = [r[0] for r in RANKS]
    return names.index(v) if v in names else DEFAULT_RANK

def pinned_level(name):
    """Rank for an agent: _pinned (never changes) > promotions > default Padawan."""
    n = (name or "").lower()
    promos = load_promos()
    for k, v in (promos.get("_pinned") or {}).items():
        if n == k.lower() or n.startswith(k.lower()): return rank_index(v)
    for k, v in promos.items():
        if k.startswith("_"): continue
        if n == k.lower() or n.startswith(k.lower()): return rank_index(v)
    return DEFAULT_RANK

def pin_is_fixed(name):
    n = (name or "").lower()
    return any(n == k.lower() or n.startswith(k.lower()) for k in (load_promos().get("_pinned") or {}))

def level_for(xp):
    lvl = 0
    for i, r in enumerate(RANKS):
        if xp >= r[2]: lvl = i
    return lvl

def bar(frac, width, on, off, col):
    n = max(0, min(width, round(frac * width)))
    return c(col, on * n) + c(DIM, off * (width - n))

def git_branch(cwd, st, now):
    cache = st.setdefault("git", {})
    ent = cache.get(cwd)
    if ent and now - ent["t"] < 30:
        return ent["b"]
    try:
        br = subprocess.run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True, timeout=0.3).stdout.strip()
    except Exception:
        br = ent["b"] if ent else ""
    cache[cwd] = {"b": br, "t": now}
    return br

import base64

RGB = {BLUE: (60, 140, 255), GREEN: (80, 220, 90), CYAN: (60, 230, 230),
       PURPLE: (170, 110, 255), GOLD: (255, 200, 40)}

def iterm(st, now, title, epithet, xp, name, col, promoted):
    """Write iTerm2 escapes straight to the pane's tty (bypasses Claude's renderer)."""
    key = (title, name, xp // 50, promoted)          # throttle: only on meaningful change
    if st.get("iterm_last") == list(key): return
    try:
        fd = os.open("/dev/tty", os.O_WRONLY | os.O_NOCTTY)
    except Exception:
        return
    try:
        badge = f"⚔ {title}" + (f"\n{name}" if name else "") + f"\n{xp:,} XP"
        if promoted: badge = "★ PROMOTED ★\n" + badge
        b64 = base64.b64encode(badge.encode()).decode()
        r, g, bl = RGB.get(col, (200, 200, 200))
        seq = (f"\033]1337;SetBadgeFormat={b64}\007"
               f"\033]6;1;bg;red;brightness;{r}\007"
               f"\033]6;1;bg;green;brightness;{g}\007"
               f"\033]6;1;bg;blue;brightness;{bl}\007"
               f"\033]1;⚔ {title}" + (f" · {name}" if name else "") + "\007")
        os.write(fd, seq.encode())
        st["iterm_last"] = list(key)
    except Exception:
        pass
    finally:
        os.close(fd)

def main():
    try: d = json.load(sys.stdin)
    except Exception: d = {}
    st = load(); now = time.time()

    sid   = d.get("session_id", "?")
    cost  = (d.get("cost") or {}).get("total_cost_usd") or 0.0
    la    = (d.get("cost") or {}).get("total_lines_added") or 0
    lr    = (d.get("cost") or {}).get("total_lines_removed") or 0
    used  = (d.get("context_window") or {}).get("used_percentage")
    model = (d.get("model") or {}).get("display_name", "?")
    name  = d.get("session_name") or (d.get("agent") or {}).get("name") or ""
    cwd   = (d.get("workspace") or {}).get("current_dir") or d.get("cwd") or os.getcwd()
    effort = (d.get("effort") or {}).get("level")
    prompt_id = d.get("prompt_id")

    s = st["sessions"].setdefault(sid, {"cost": 0.0, "lines": 0, "kyber": 0, "last_prompt": None, "t": now})
    dcost  = max(0.0, cost - s["cost"]);      s["cost"]  = cost
    dlines = max(0, (la + lr) - s["lines"]);  s["lines"] = la + lr
    gained = int(dcost * 100) + dlines
    if prompt_id and prompt_id != s["last_prompt"]:
        s["last_prompt"] = prompt_id; s["kyber"] += 1; gained += 5
    s["t"] = now
    st["sessions"] = {k: v for k, v in st["sessions"].items() if now - v.get("t", now) < 3 * 86400}

    agent_key = name or sid
    ag = st.setdefault("agents", {}).setdefault(agent_key, {"xp": 0, "levelup_at": 0, "t": now})
    ag["t"] = now
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    ag["xp"] += gained
    pin = pinned_level(agent_key)
    lvl = pin
    if ag.get("rank") is None: ag["rank"] = lvl
    elif lvl > ag["rank"]: ag["levelup_at"] = now
    ag["rank"] = lvl
    st["xp"] = st.get("xp", 0) + gained          # galaxy-wide total, kept for fun
    st["frame"] = (st.get("frame", 0) + 1) % len(SABER)
    if now - st.get("quote_t", 0) > 600:
        st["quote_i"] = random.randrange(len(QUOTES)); st["quote_t"] = now
    save(st)

    title, epithet, need, col = RANKS[lvl]
    nxt = RANKS[lvl + 1][2] if lvl + 1 < len(RANKS) else None
    frac = 1.0 if nxt is None else (ag["xp"] - need) / (nxt - need)
    nxt = None
    frac = 1.0 if lvl >= KNIGHT else max(0.0, (lvl - PADAWAN) / (KNIGHT - PADAWAN))

    # lightsaber: hilt + pulsing blade in rank colour
    saber = c(DIM, HILT) + c(col, SABER[st["frame"]] + "━" * 3)
    if now - ag.get("levelup_at", 0) < 20:
        head = c(GOLD, b(f"★ Promoted → {title}")) + c(DIM, f" · {epithet}")
    else:
        head = c(col, b(title)) + c(DIM, f" · {epithet}")
    xp_txt = f"{ag['xp']:,} XP" + (f" → {nxt:,}" if nxt else (" · sworn Knight" if pin_is_fixed(agent_key) else
               (f" · {lvl - PADAWAN}/5 trials" if PADAWAN <= lvl < KNIGHT else " · by the Council")))
    line1 = f"{saber} {head}  {bar(frac, 12, '▰', '▱', GOLD)} {c(CREAM, xp_txt)}"

    # kyber crystals: turns this session, 12 per cycle
    k = s["kyber"]; in_cycle = k % 12; rounds = k // 12
    crystals = "".join("◆" if i < in_cycle else "◇" for i in range(12))
    kyber = c(CYAN, crystals) + c(DIM, f" {k} turns") + (c(CYAN, f" ×{rounds}") if rounds else "")

    # hyperdrive heat = context usage
    if used is None:
        heat = c(DIM, "hyperdrive cold")
    else:
        hc = GREEN if used < 50 else (GOLD if used < 80 else RED)
        label = "hyperdrive" if used < 80 else "⚠ overheating"
        heat = bar(used / 100, 10, "▮", "▯", hc) + c(hc, f" {used:.0f}% {label}")

    branch = git_branch(cwd, st, now)
    tail = [c(BLUE, model)]
    if effort: tail.append(c(DIM, effort))
    if branch: tail.append(c(GREEN, f" {branch}"))
    if name:   tail.append(c(PURPLE, name))
    tail.append(c(GOLD, f"₡{cost * 100:,.0f}"))     # galactic credits = cents
    line2 = f"  {kyber}  {heat}  " + c(DIM, "│ ") + c(DIM, " · ").join(tail)
    line3 = c(DIM, "  ❝ " + QUOTES[st["quote_i"]] + " ❞")
    promoted = now - ag.get("levelup_at", 0) < 20
    iterm(st, now, title, epithet, ag["xp"], name, col, promoted)
    st["last"] = [line1, line2, line3]
    save(st)
    print(line1); print(line2); print(line3)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        try:
            for ln in load().get("last", []): print(ln)
        except Exception:
            print("╞▌━━━ status line rebooting…")
