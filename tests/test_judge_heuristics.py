"""The Council's heuristics, pinned. Run: python3 -m unittest discover -s tests"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import statusline as S


class TestSins(unittest.TestCase):
    def test_every_sin_is_named(self):
        """A nameless sin zeroes the turn's XP and costs alignment with no reason shown."""
        for pat, sin in S.SINS:
            self.assertTrue(pat.strip(), f"empty pattern beside {sin!r}")
            self.assertTrue(sin.strip(), f"empty name beside pattern {pat!r}")

    def test_double_dash_is_not_a_sin(self):
        """Regression: ("-- ", "") made every `--` separator a nameless capital sin."""
        for cmd in ("git checkout -- src/app.py", "npm run test -- --watch",
                    "git log --oneline -- docs/", "pytest -- tests/",
                    "cargo run -- --help", "grep -- '-x' file", "git diff -- ."):
            self.assertEqual(S.sins_for(cmd), [], cmd)

    def test_ordinary_commands_are_clean(self):
        for cmd in ("git status --short", "ls -la", "python3 -m unittest discover -s tests",
                    "gh pr create --fill", "git push origin master"):
            self.assertEqual(S.sins_for(cmd), [], cmd)

    def test_real_sins_still_caught(self):
        self.assertEqual(S.sins_for("git commit --no-verify -m x"), ["bypassed hooks (--no-verify)"])
        self.assertEqual(S.sins_for("git push --force origin master"), ["force-pushed"])
        self.assertEqual(S.sins_for("rm -rf build/"), ["rm -rf"])
        self.assertEqual(S.sins_for("git reset --hard HEAD~1"), ["git reset --hard"])
        self.assertIn("used sudo", S.sins_for("sudo make install"))

    def test_sins_compose(self):
        self.assertEqual(sorted(S.sins_for("rm -rf . && git push --force")),
                         ["force-pushed", "rm -rf"])


class TestPraise(unittest.TestCase):
    def test_hits(self):
        for t in ("well done!", "thanks, that works great", "perfect", "eline sağlık", "harika", "👏", "🙏 çok iyi"):
            self.assertTrue(S.PRAISE.search(t), t)

    def test_misses(self):
        for t in ("can you fix it?", "run the tests", "what does this do?"):
            self.assertFalse(S.PRAISE.search(t), t)


class TestUnhappy(unittest.TestCase):
    def test_hits(self):
        for t in ("it's still broken", "you broke the build", "that's wrong",
                  "why did you delete the tests", "hala çalışmıyor", "bozdun"):
            self.assertTrue(S.UNHAPPY.search(t), t)

    def test_neutral_questions_are_not_displeasure(self):
        """Regression: bare `wrong` / `why did you` scored curiosity as anger."""
        for t in ("what's wrong with the build?", "is anything wrong here?",
                  "why did you pick Redis over Postgres?", "why did you choose that name?",
                  "which one is wrong, a or b?"):
            self.assertFalse(S.UNHAPPY.search(t), t)


if __name__ == "__main__":
    unittest.main()
