"""Hooks never raise; the status line keeps the claude pid current. Run: python3 -m unittest discover -s tests"""
import json, os, subprocess, sys, tempfile, unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import statusline as S


def dead_pid():
    p = subprocess.Popen([sys.executable, "-c", "pass"]); p.wait()
    return p.pid


def env_for(d):
    env = {k: v for k, v in os.environ.items() if k not in ("JEDI_NO_HOOKS", "CLAUDE_SESSION_NAME")}
    env["JEDI_DIR"] = d
    return env


class TestHooksNeverRaise(unittest.TestCase):
    """A hook traceback surfaces as "hook error" in every Claude session, so any failure must be silent."""
    def run_hook(self, op, stdin):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "state.json"), "w") as f: json.dump({"sessions": {}, "agents": {}}, f)
            p = subprocess.run([sys.executable, os.path.join(ROOT, "bin", "jedi"), op], env=env_for(d),
                               input=stdin, capture_output=True, text=True, timeout=10)
            log = os.path.join(d, "hook-errors.log")
            if not os.path.exists(log): return p, ""
            with open(log) as f: return p, f.read()

    def assertSilent(self, op, stdin):
        p, log = self.run_hook(op, stdin)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout, "")
        self.assertNotIn("Traceback", p.stderr, p.stderr)
        return log

    def test_motivate_crash_is_swallowed_and_logged(self):
        log = self.assertSilent("motivate", "[]")          # valid JSON, not an object: h.get raises
        self.assertIn("jedi motivate", log)
        self.assertIn("AttributeError", log)

    def test_judge_crash_is_swallowed_and_logged(self):
        log = self.assertSilent("judge", "[]")
        self.assertIn("jedi judge", log)

    def test_ordinary_silence_writes_no_log(self):
        self.assertEqual(self.assertSilent("motivate", json.dumps({"session_id": "nobody"})), "")


class TestPidAlive(unittest.TestCase):
    def test_cases(self):
        self.assertTrue(S.pid_alive(os.getpid()))
        self.assertFalse(S.pid_alive(dead_pid()))
        for pid in (None, 0, ""):
            self.assertFalse(S.pid_alive(pid))


class TestSessionPid(unittest.TestCase):
    """Regression: the pid was written once, so after `claude --resume` the session kept the dead one."""
    FAKE_CLAUDE = 4242

    def tick(self, stored_pid):
        with tempfile.TemporaryDirectory() as d:
            state = {"sessions": {"s1": {"cost": 0.0, "lines": 0, "kyber": 0, "last_prompt": None, "pid": stored_pid}}, "agents": {}}
            with open(os.path.join(d, "state.json"), "w") as f: json.dump(state, f)
            code = (f"import sys; sys.path.insert(0, {os.path.join(ROOT, 'scripts')!r}); import statusline as S; "
                    f"S.claude_pid = lambda: {self.FAKE_CLAUDE}; S.iterm = lambda *a, **k: None; S.main()")
            p = subprocess.run([sys.executable, "-c", code], env=env_for(d), input=json.dumps({"session_id": "s1"}),
                               capture_output=True, text=True, timeout=10)
            self.assertEqual(p.returncode, 0, p.stderr)
            with open(os.path.join(d, "state.json")) as f: return json.load(f)["sessions"]["s1"]["pid"]

    def test_dead_pid_is_replaced(self):
        self.assertEqual(self.tick(dead_pid()), self.FAKE_CLAUDE)

    def test_missing_pid_is_filled(self):
        self.assertEqual(self.tick(None), self.FAKE_CLAUDE)

    def test_live_pid_is_kept(self):
        self.assertEqual(self.tick(os.getpid()), os.getpid())


if __name__ == "__main__":
    unittest.main()
