#!/usr/bin/env python3
"""jedi-statusline — a Star Wars-gamified Claude Code status line.

Reads Claude Code's statusline JSON on stdin, keeps persistent XP in
~/.claude/jedi-statusline/state.json and renders a three-line animated bar:
lightsaber, tier-coloured rank, XP bar with live +XP ticker, kyber crystals
for turns, hyperdrive heat (context), credits, branch, holocron quote.
Ranks are granted by the Council (bin/jedi), never by XP.
"""
import json, os, sys, time, random, subprocess, base64

DIR    = os.path.expanduser("~/.claude/jedi-statusline")
STATE  = f"{DIR}/state.json"
PROMOS = f"{DIR}/promotions.json"
LEDGER = f"{DIR}/ledger.jsonl"

def ledger_append(ev):
    """Append-only, hash-chained record. Each line carries sha256(prev_hash + payload).
    Serialised with an exclusive file lock: many sessions append concurrently."""
    import hashlib, fcntl
    os.makedirs(DIR, exist_ok=True)
    with open(LEDGER, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            prev = "genesis"
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - 4096))
            tail = f.read().strip().splitlines()
            if tail:
                try: prev = json.loads(tail[-1]).get("hash", prev)
                except Exception: pass
            ev = dict(ev); ev["t"] = round(time.time(), 3); ev["prev"] = prev
            payload = json.dumps({k: v for k, v in ev.items() if k != "hash"}, sort_keys=True)
            ev["hash"] = hashlib.sha256((prev + payload).encode()).hexdigest()[:24]
            f.seek(0, 2); f.write(json.dumps(ev, sort_keys=True) + "\n"); f.flush()
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    return ev["hash"]

def c(n, s): return f"\033[38;5;{n}m{s}\033[0m"
def b(s):    return f"\033[1m{s}\033[0m"
DIM, CREAM, GOLD, RED, GREEN, SKY = 244, 230, 220, 196, 82, 39

# ---- tiers: (title, epithet, colour-256, rgb for iTerm, xp multiplier) ------
RANKS = [
    ("Youngling",      "sensitive to the Force",    250, (200, 200, 210), 1.0),
    ("Padawan",        "learner",                    39, ( 60, 140, 255), 1.0),
    ("Padawan ◆",      "Trial of Skill passed",      39, ( 60, 140, 255), 1.1),
    ("Padawan ◆◆",     "Trial of Courage passed",    45, ( 60, 190, 255), 1.2),
    ("Padawan ◆◆◆",    "Trial of the Flesh passed",  45, ( 60, 190, 255), 1.3),
    ("Padawan ◆◆◆◆",   "Trial of Spirit passed",     51, ( 60, 230, 255), 1.4),
    ("Padawan ◆◆◆◆◆",  "Trial of Insight passed",    51, ( 60, 230, 255), 1.5),
    ("Jedi Knight",    "guardian of peace",          82, ( 80, 220,  90), 2.0),
    ("Jedi Master",    "seat on the Council",       208, (255, 140,   0), 2.5),
    ("Jedi Guardian",  "blade of the Order",        220, (255, 200,  40), 3.0),
    ("Grand Master",   "the Order's wisdom",        135, (170, 110, 255), 3.5),
    ("Force Ghost",    "one with the Force",        159, (160, 255, 240), 4.0),
    ("The Chosen One", "balance",                   229, (255, 240, 180), 5.0),
]
PADAWAN, KNIGHT = 1, 7
DEFAULT_RANK = PADAWAN

# what each Trial demands — shown to the agent by the motivate hook
TRIALS = [
    ("Trial of Skill",     "ship a change with tests or typecheck green on the first run"),
    ("Trial of Courage",   "open a PR and defend a design decision in its description"),
    ("Trial of the Flesh", "endure a long session — push past 80% context without losing the thread"),
    ("Trial of Spirit",    "face a failure honestly: report it, root-cause it, fix it"),
    ("Trial of Insight",   "review another agent's work and find what they missed"),
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

# ---- the dark side ----------------------------------------------------------
# alignment ∈ [-100, +100]; every agent starts at +50. Merits pull toward the light,
# sloppy work (errors, skipped tests, force pushes, rm -rf, --no-verify, flailing) toward the dark.
ALIGN_START = 50
DARK_TIERS = [   # (threshold, title-transform, colour, rgb)
    (-80, lambda t: "Sith Lord",             124, (160,  20,  20)),
    (-50, lambda t: "Sith Apprentice",       196, (255,  40,  40)),
    (-20, lambda t: t + " ⚠ tempted",        202, (255,  90,  40)),
]
SITH_QUOTES = [
    "Peace is a lie, there is only passion. — Sith Code",
    "Give in to your anger. — Palpatine",
    "I find your lack of faith disturbing. — Vader",
    "You don't know the power of the dark side. — Vader",
    "Good. Use your aggressive feelings. — Palpatine",
    "The dark side of the Force is a pathway to many abilities. — Palpatine",
    "You underestimate the power of the dark side. — Vader",
]
def slider(align, d=1, W=9):
    """dark ---●▸--- light : ● at alignment, arrow shows last drift (defaults toward the light)."""
    pos = round((align + 100) / 200 * (W - 1))
    left = "-" * pos; right = "-" * (W - 1 - pos)
    if d < 0 and right: right = "◂" + right[1:]
    elif left:          left = left[:-1] + "▸"
    elif right:         right = "▸" + right[1:]
    return left, right

def dark_tier(align):
    for th, fn, col, rgb in DARK_TIERS:
        if align <= th: return fn, col, rgb
    return None

SABER = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█", "▉", "▊", "▋", "▌", "▍", "▎"]

# ---- state ------------------------------------------------------------------
def load_json(p, default):
    try:
        with open(p) as f: return json.load(f)
    except Exception:
        return default

def save(st):
    os.makedirs(DIR, exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f: json.dump(st, f)
    os.replace(tmp, STATE)

def rank_index(v):
    if isinstance(v, int): return max(0, min(len(RANKS) - 1, v))
    names = [r[0] for r in RANKS]
    return names.index(v) if v in names else DEFAULT_RANK

def match(name, key):
    n = (name or "").lower(); k = key.lower()
    return n == k or n.startswith(k)

def rank_for(name, promos=None):
    """_pinned (never changes) > promotions > default Padawan. Returns (idx, pinned?)."""
    promos = promos if promos is not None else load_json(PROMOS, {})
    pinned = promos.get("_pinned") or {}
    hits = sorted((k for k in pinned if match(name, k)), key=len)   # shortest (broadest) decree wins
    if hits: return rank_index(pinned[hits[0]]), True
    for k, v in promos.items():
        if not k.startswith("_") and match(name, k): return rank_index(v), False
    return DEFAULT_RANK, False

def bar(frac, width, on, off, col):
    n = max(0, min(width, round(frac * width)))
    return c(col, on * n) + c(DIM, off * (width - n))

def git_branch(cwd, st, now):
    cache = st.setdefault("git", {}); ent = cache.get(cwd)
    if ent and now - ent["t"] < 30: return ent["b"]
    try:
        br = subprocess.run(["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD"],
                            capture_output=True, text=True, timeout=0.3).stdout.strip()
    except Exception:
        br = ent["b"] if ent else ""
    cache[cwd] = {"b": br, "t": now}
    return br

def iterm(st, title, xp, name, rgb, promoted, lvl, align=ALIGN_START, adir=1):
    """iTerm2 badge / tab colour / title, written straight to the pane's tty."""
    key = [title, name, xp // 50, promoted]
    if st.get("iterm_last") == key: return
    try: fd = os.open("/dev/tty", os.O_WRONLY | os.O_NOCTTY)
    except Exception: return
    try:
        trials = f"\n{lvl - PADAWAN}/5 trials" if PADAWAN <= lvl < KNIGHT else ""
        l, r = slider(align, adir)
        badge = ("★ PROMOTED ★\n" if promoted else "") + f"⚔ {title}" + (f"\n{name}" if name else "") + f"\n{xp:,} XP{trials}\n{l}●{r} {align:+d}"
        b64 = base64.b64encode(badge.encode()).decode()
        r, g, bl = rgb
        seq = (f"\033]1337;SetBadgeFormat={b64}\007"
               f"\033]6;1;bg;red;brightness;{r}\007\033]6;1;bg;green;brightness;{g}\007\033]6;1;bg;blue;brightness;{bl}\007"
               f"\033]1;⚔ {title}" + (f" · {name}" if name else "") + "\007")
        os.write(fd, seq.encode()); st["iterm_last"] = key
    except Exception: pass
    finally: os.close(fd)

# ---- main -------------------------------------------------------------------
def main():
    try: d = json.load(sys.stdin)
    except Exception: d = {}
    st = load_json(STATE, {"xp": 0, "frame": 0, "sessions": {}, "agents": {}, "quote_i": 0, "quote_t": 0})
    now = time.time()

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

    agent_key = name or sid
    ag = st.setdefault("agents", {}).setdefault(agent_key, {"xp": 0, "levelup_at": 0, "rank": None, "t": now})
    ag["t"] = now
    lvl, fixed = rank_for(agent_key)
    title, epithet, col, rgb, mult = RANKS[lvl]
    align = ag.get("align", ALIGN_START)
    dt = dark_tier(align)
    if dt:
        fn, dcol, drgb = dt
        title = fn(title); col, rgb = dcol, drgb
        if align <= -50 and name: name = "Darth " + name
        if align <= -50: epithet = "the Council watches"

    # ---- XP: (1/cent + 1/line + 5/turn) × tier multiplier
    s = st.setdefault("sessions", {}).setdefault(sid, {"cost": 0.0, "lines": 0, "kyber": 0, "last_prompt": None, "t": now})
    s["agent"] = agent_key
    dcost  = max(0.0, cost - s["cost"]);      s["cost"]  = cost
    dlines = max(0, (la + lr) - s["lines"]);  s["lines"] = la + lr
    base = int(dcost * 100) + dlines
    if prompt_id and prompt_id != s["last_prompt"]:
        s["last_prompt"] = prompt_id; s["kyber"] += 1; base += 5
    base = min(base, 500)
    gained = int(round(base * mult))
    if gained > 0:
        ag["xp"] += gained; st["xp"] = st.get("xp", 0) + gained
        ag["last_gain"] = gained; ag["gain_t"] = now
        ledger_append({"kind": "work", "agent": agent_key, "session": sid, "delta": gained,
                       "base": base, "mult": mult, "cost": round(cost, 4), "lines": la + lr, "turns": s["kyber"]})
    s["t"] = now
    st["sessions"] = {k: v for k, v in st["sessions"].items() if now - v.get("t", now) < 3 * 86400}

    # promotion flash when the Council changes the rank
    if ag.get("rank") is None: ag["rank"] = lvl
    elif lvl > ag["rank"]: ag["levelup_at"] = now
    ag["rank"] = lvl
    promoted = now - ag.get("levelup_at", 0) < 20

    st["frame"] = (st.get("frame", 0) + 1) % len(SABER)
    if now - st.get("quote_t", 0) > 600:
        st["quote_i"] = random.randrange(len(QUOTES)); st["quote_t"] = now

    # ---- line 1: saber · rank · progress · XP (+ticker)
    head = (c(GOLD, b(f"★ Promoted → {title}")) if promoted else c(col, b(title))) + c(DIM, f" · {epithet}")
    if lvl >= KNIGHT: frac, tail_txt = 1.0, (" · sworn Knight" if fixed else " · by the Council")
    else:             frac, tail_txt = (lvl - PADAWAN) / (KNIGHT - PADAWAN), f" · {lvl - PADAWAN}/5 trials"
    xp_txt = c(CREAM, f"{ag['xp']:,} XP") + c(DIM, tail_txt)
    if now - ag.get("gain_t", 0) < 8 and ag.get("last_gain"):
        xp_txt += " " + c(GREEN, b(f"+{ag['last_gain']} XP")) + c(DIM, f" ×{mult:g}")
    # alignment slider: dark end on the left, light on the right; the white marker sits at the
    # agent's alignment and points the way it last moved ( > toward the light, < toward the dark )
    left, right = slider(align, ag.get("align_dir", 1))
    abar = c(244, left) + c(255, b("●")) + c(244, right)
    acol = 255
    line1 = f"{abar} {c(244, f'{align:+d}')}  {head}  {bar(frac, 12, '▰', '▱', col)} {xp_txt}"

    # ---- line 2: kyber · hyperdrive · model · branch · session · credits
    k = s["kyber"]; crystals = "".join("◆" if i < k % 12 else "◇" for i in range(12))
    kyber = c(col, crystals) + c(DIM, f" {k} turns") + (c(col, f" ×{k // 12}") if k >= 12 else "")
    if used is None: heat = c(DIM, "hyperdrive cold")
    else:
        hc = GREEN if used < 50 else (GOLD if used < 80 else RED)
        heat = bar(used / 100, 10, "▮", "▯", hc) + c(hc, f" {used:.0f}% " + ("hyperdrive" if used < 80 else "⚠ overheating"))
    branch = git_branch(cwd, st, now)
    tail = [c(SKY, model)]
    if effort: tail.append(c(DIM, effort))
    if branch: tail.append(c(GREEN, f" {branch}"))
    if name:   tail.append(c(col, name))
    tail.append(c(GOLD, f"₡{cost * 100:,.0f}"))
    line2 = f"  {kyber}  {heat}  " + c(DIM, "│ ") + c(DIM, " · ").join(tail)
    q = SITH_QUOTES[st["quote_i"] % len(SITH_QUOTES)] if align <= -20 else QUOTES[st["quote_i"]]
    line3 = c(DIM if align > -20 else 124, "  ❝ " + q + " ❞")

    iterm(st, title, ag["xp"], name, rgb, promoted, lvl, align, ag.get("align_dir", 1))
    st["last"] = [line1, line2, line3]
    save(st)
    print(line1); print(line2); print(line3)

def locked_main():
    import fcntl
    os.makedirs(DIR, exist_ok=True)
    with open(f"{DIR}/.lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try: main()
        finally: fcntl.flock(lk, fcntl.LOCK_UN)

if __name__ == "__main__":
    try: locked_main()
    except Exception:
        try:
            for ln in load_json(STATE, {}).get("last", []): print(ln)
        except Exception:
            print("╞▌━━━ status line rebooting…")
