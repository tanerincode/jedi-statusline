"""The motivate hook (UserPromptSubmit / SessionStart) must never crash. Run: python3 -m unittest discover -s tests"""
import json, os, subprocess, sys, tempfile, unittest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import statusline as S

FIVE_OF_FIVE = S.KNIGHT - 1        # Padawan ◆◆◆◆◆: every Trial passed, not yet knighted


class TestTrialIndex(unittest.TestCase):
    def test_every_level(self):
        for lvl in range(len(S.RANKS)):
            i = S.trial_index(lvl)
            if S.PADAWAN <= lvl < FIVE_OF_FIVE:
                self.assertEqual(i, lvl - S.PADAWAN, S.RANKS[lvl][0])
                self.assertLess(i, len(S.TRIALS))
            else:
                self.assertIsNone(i, S.RANKS[lvl][0])

    def test_band_is_one_wider_than_the_trials(self):
        """The shape that caused the crash: six Padawan levels, five Trials."""
        self.assertEqual(S.KNIGHT - S.PADAWAN, len(S.TRIALS) + 1)


def motivate(agents, promos, session_agent):
    with tempfile.TemporaryDirectory() as d:
        state = {"sessions": {"s1": {"agent": session_agent}}, "agents": {n: {"xp": 0} for n in agents}}
        for name, data in (("state.json", state), ("promotions.json", promos)):
            with open(os.path.join(d, name), "w") as f: json.dump(data, f)
        env = {k: v for k, v in os.environ.items() if k not in ("JEDI_NO_HOOKS", "CLAUDE_SESSION_NAME")}
        env["JEDI_DIR"] = d
        p = subprocess.run([sys.executable, os.path.join(ROOT, "bin", "jedi"), "motivate"], env=env,
                           input=json.dumps({"session_id": "s1", "hook_event_name": "UserPromptSubmit"}),
                           capture_output=True, text=True, timeout=10)
        return p


class TestMotivate(unittest.TestCase):
    def assertRan(self, p):
        self.assertNotIn("Traceback", p.stderr, p.stderr)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)["hookSpecificOutput"]["additionalContext"]

    def test_another_agent_at_five_of_five_does_not_crash_everyone(self):
        """Regression: one agent at Padawan ◆◆◆◆◆ crashed the hook for every session."""
        ctx = self.assertRan(motivate(["me", "veteran"], {"veteran": FIVE_OF_FIVE}, "me"))
        self.assertIn("Trial of Skill", ctx)

    def test_the_five_of_five_agent_itself(self):
        ctx = self.assertRan(motivate(["veteran"], {"veteran": FIVE_OF_FIVE}, "veteran"))
        self.assertIn("All five Trials passed", ctx)
        self.assertIn("5/5 trials", ctx)

    def test_the_council_is_told_who_awaits_knighthood(self):
        ctx = self.assertRan(motivate(["council", "veteran"], {"council": S.KNIGHT, "veteran": FIVE_OF_FIVE}, "council"))
        self.assertIn("veteran → Knighthood", ctx)

    def test_every_rank_runs(self):
        for lvl in range(len(S.RANKS)):
            with self.subTest(rank=S.RANKS[lvl][0]):
                self.assertRan(motivate(["a"], {"a": lvl}, "a"))


if __name__ == "__main__":
    unittest.main()
