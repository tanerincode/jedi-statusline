#!/usr/bin/env python3
"""Render docs/hero.svg and docs/promotion.svg from real status-line output (sandboxed JEDI_DIR)."""
import json, os, re, html, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
os.environ["JEDI_DIR"] = tempfile.mkdtemp()
J = ["python3", "bin/jedi"]; run = lambda *a: subprocess.run(J + list(a), capture_output=True, text=True, check=True)
run("pin", "kai-main", "The Chosen One"); run("promote", "api-agent", "Jedi Knight"); [run("advance", "apnd-surgent") for _ in range(3)]
def sl(name, cost, lines, used):
    d = {"session_id": "s-" + name, "session_name": name, "prompt_id": "p", "cost": {"total_cost_usd": cost, "total_lines_added": lines},
         "context_window": {"used_percentage": used}, "model": {"display_name": "Fable 5"}, "effort": {"level": "high"}, "workspace": {"current_dir": ROOT}}
    return subprocess.run(["python3", "scripts/statusline.py"], input=json.dumps(d), capture_output=True, text=True).stdout.rstrip("\n").split("\n")
A = [("kai-main", 89.55, 0, 16), ("api-agent", 41.2, 120, 62), ("apnd-surgent", 12.4, 40, 34), ("ovba-surgent", 7.1, 15, 84)]
for a in A: sl(*a)
p = os.path.join(os.environ["JEDI_DIR"], "state.json"); d = json.load(open(p))
d["agents"]["kai-main"].update(xp=10890, align=71, align_dir=1, last_gain=None)
d["agents"]["api-agent"].update(xp=14107, align=27, align_dir=-1, last_gain=30)
d["agents"]["apnd-surgent"].update(xp=10539, align=58, align_dir=1, last_gain=125)
d["agents"]["ovba-surgent"].update(xp=1637, align=-63, align_dir=-1, last_gain=None)
for k, v in {"s-kai-main": 21, "s-api-agent": 9, "s-apnd-surgent": 14, "s-ovba-surgent": 31}.items(): d["sessions"][k]["kyber"] = v
json.dump(d, open(p, "w"))
panes = [sl(*a) for a in A]
def xterm(n):
    n = int(n)
    if n < 16: return ["#000", "#c33", "#3c3", "#cc3", "#33c", "#c3c", "#3cc", "#ccc", "#666", "#f66", "#6f6", "#ff6", "#66f", "#f6f", "#6ff", "#fff"][n]
    if n < 232:
        n -= 16; r, g, b = n // 36, (n // 6) % 6, n % 6; f = lambda v: 0 if v == 0 else 55 + v * 40; return "#%02x%02x%02x" % (f(r), f(g), f(b))
    v = 8 + (n - 232) * 10; return "#%02x%02x%02x" % (v, v, v)
CW = 7.2   # px per character at 12px monospace; textLength pins layout across renderers
def plain(line): return re.sub(r"\x1b\[[0-9;]*m", "", line)
def tl(text): return ' textLength="%.0f" lengthAdjust="spacingAndGlyphs"' % (len(text) * CW)
def tspans(line):
    out = []; col = "#c9c9c9"; bold = False
    for m in re.finditer(r"\x1b\[([0-9;]*)m|[^\x1b]+", line):
        t = m.group(0)
        if t.startswith("\x1b"):
            code = m.group(1)
            if code in ("0", ""): col = "#c9c9c9"; bold = False
            elif code == "1": bold = True
            elif code.startswith("38;5;"): col = xterm(code.split(";")[2])
        else: out.append('<tspan fill="%s"%s>%s</tspan>' % (col, ' font-weight="bold"' if bold else '', html.escape(t)))
    return "".join(out)
judge = [("api-agent", "⚔ Council judgement: +30 XP · Clean run · Missed: Good counsel (2 user-run commands failed)", "#c9c9c9"),
         ("api-agent", "☠ The dark side stirs (−23 → alignment +27): bad counsel, handed the user a command with a placeholder still in it.", "#ff5f5f"),
         ("ovba-surgent", "☠ You have FALLEN to the dark side (alignment −63). Your name is spoken as Darth ovba-surgent.", "#ff5f5f"),
         ("apnd-surgent", "☀ The light grows (+21 → alignment +58). Council review 6/6 — Wisdom +25 XP ×1.4", "#87ff5f"),
         ("kai-main", "Trials awaiting your confirmation: apnd-surgent → Trial of Spirit (evidence ×1) — jedi advance apnd-surgent", "#ffd75f")]
W = 1420; FS = 12; lh = 20; y = 32; body = []
body.append('<text x="24" y="%d" fill="#8a8a8a" font-size="12">jedi-statusline — four agents, one Council</text>' % y); y += 24
for (t, *_), lines in zip(A, panes):
    body.append('<rect x="16" y="%d" width="%d" height="%d" rx="6" fill="#111318" stroke="#2a2d35"/>' % (y - 15, W - 32, lh * len(lines) + 14))
    body.append('<text x="%d" y="%d" text-anchor="end" fill="#5a5d66" font-size="11">%s</text>' % (W - 28, y - 3, t))
    for ln in lines: body.append('<text x="30" y="%d" xml:space="preserve"%s>%s</text>' % (y + 6, tl(plain(ln)), tspans(ln))); y += lh
    y += 22
body.append('<text x="24" y="%d" fill="#8a8a8a" font-size="12">what the agents hear after each job</text>' % y); y += 22
for who, msg, col in judge:
    body.append('<text x="30" y="%d" xml:space="preserve"%s><tspan fill="#5a5d66">%-14s</tspan><tspan fill="%s">%s</tspan></text>' % (y, tl("%-14s%s" % (who, msg)), who, col, html.escape(msg))); y += lh
H = y + 12; font = 'JetBrains Mono, SFMono-Regular, Menlo, Consolas, monospace'
open("docs/hero.svg", "w", encoding="utf-8").write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="%s" font-size="%d"><rect width="100%%" height="100%%" fill="#0b0c10"/>%s</svg>' % (W, H, W, H, font, FS, "".join(body)))
before = tspans(panes[2][0]); promo = re.sub(r'fill="#(5fd7ff|5fafff|5fffff)"', 'fill="#ffd75f"', tspans(panes[2][0].replace("Padawan ◆◆◆", "★ Promoted → Jedi Knight")))
open("docs/promotion.svg", "w", encoding="utf-8").write('''<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="62" viewBox="0 0 %d 62" font-family="%s" font-size="%d">
<rect width="100%%" height="100%%" fill="#0b0c10"/><rect x="16" y="9" width="%d" height="44" rx="6" fill="#111318" stroke="#2a2d35"/>
<text x="30" y="29" xml:space="preserve"%s>%s<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.45;0.5;0.95;1" dur="6s" repeatCount="indefinite"/></text>
<text x="30" y="29" xml:space="preserve" opacity="0"%s>%s<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;0.45;0.5;0.95;1" dur="6s" repeatCount="indefinite"/></text>
<text x="30" y="49" xml:space="preserve"%s>%s</text></svg>''' % (W, W, font, FS, W - 32, tl(plain(panes[2][0])), before, tl(plain(panes[2][0])), promo, tl(plain(panes[2][1])), tspans(panes[2][1])))
print("rendered docs/hero.svg (%dx%d) and docs/promotion.svg" % (W, H))
