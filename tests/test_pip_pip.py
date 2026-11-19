"""Tests for pip-pip, built on synthetic git repos with scripted habits.

The repos are constructed with exact commit counts, hours, weekdays and
message quality, so the expected metrics are known answers, not guesses.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date, datetime, time, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pip_pip  # noqa: E402

UTC = timezone.utc


def _run(repo, *args, env_extra=None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    subprocess.run(["git", "-C", repo] + list(args), check=True,
                   capture_output=True, text=True, env=env)


def make_repo(path):
    os.makedirs(path)
    _run(path, "init", "-q")
    _run(path, "config", "user.name", "Dev Example")
    _run(path, "config", "user.email", "dev@example.com")
    _run(path, "config", "commit.gpgsign", "false")


def commit(repo, when, subject, body="", files=None, append=None, author=None):
    if files:
        for name, content in files.items():
            fp = os.path.join(repo, name)
            os.makedirs(os.path.dirname(fp), exist_ok=True) if os.path.dirname(name) else None
            with open(fp, "w") as f:
                f.write(content)
    if append:
        for name, content in append.items():
            with open(os.path.join(repo, name), "a") as f:
                f.write(content)
    _run(repo, "add", "-A")
    iso = when.isoformat()
    env = {"GIT_AUTHOR_DATE": iso, "GIT_COMMITTER_DATE": iso}
    if author:
        env["GIT_AUTHOR_NAME"] = author
    args = ["commit", "-q", "-m", subject]
    if body:
        args += ["-m", body]
    _run(repo, *args, env_extra=env)


def at(days_ago, hour, minute=0):
    d = date.today() - timedelta(days=days_ago)
    return datetime.combine(d, time(hour, minute), tzinfo=UTC)


def friday_at(days_ago, hour):
    d = date.today() - timedelta(days=days_ago)
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return datetime.combine(d, time(hour, 30), tzinfo=UTC)


def review_of(repo):
    commits = pip_pip.collect_commits(repo, 10000)
    stats = pip_pip.collect_numstat(repo, {c.sha for c in commits})
    for c in commits:
        if c.sha in stats:
            c.added, c.deleted, c.files = stats[c.sha]
    markers = pip_pip.collect_markers(repo)
    return pip_pip.analyze(repo, commits, markers, None, date.today())


class MessyDevTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.repo = os.path.join(cls.tmp, "messy")
        make_repo(cls.repo)
        commit(cls.repo, at(400, 10), "initial commit with project scaffold and readme",
               files={"app.py": "# TODO: refactor this someday\nprint('v1')\n"})
        commit(cls.repo, at(300, 23, 30), "stuff", append={"app.py": "print('more')\n"})
        commit(cls.repo, at(299, 1, 15), "wip", append={"app.py": "print('even more')\n"})
        commit(cls.repo, friday_at(200, 17), "fix", append={"app.py": "print('friday')\n"})
        commit(cls.repo, at(198, 11), 'Revert "fix"', append={"app.py": "print('undo')\n"})
        commit(cls.repo, at(100, 14), "add temporary workaround for api response parsing",
               append={"app.py": "# temporary fix until the real API lands\nprint('parse')\n"})
        commit(cls.repo, at(50, 9), "asdf", append={"app.py": "print('x')\n"})
        commit(cls.repo, at(10, 15), "implement user settings page with validation and tests",
               body="Adds the settings form, server validation, and tests.",
               append={"app.py": "print('settings')\n"})
        cls.review = review_of(cls.repo)

    def test_known_counts(self):
        h = self.review.highlights
        self.assertEqual(self.review.total_commits, 8)
        self.assertEqual(h["vague"], 5)
        self.assertEqual(h["night_commits"], 2)
        self.assertEqual(h["friday_late"], 1)
        self.assertEqual(h["reverts"], 1)
        self.assertEqual(h["fixes"], 1)

    def test_todo_and_temp_ages(self):
        h = self.review.highlights
        self.assertGreaterEqual(h["todos"], 1)
        self.assertGreaterEqual(h["oldest_todo_days"], 390)
        self.assertGreaterEqual(h["temps"], 1)
        self.assertGreaterEqual(h["oldest_temp_days"], 95)

    def test_communication_is_poor(self):
        comm = next(c for c in self.review.categories if c.name == "Communication")
        self.assertLess(comm.score, 45)
        self.assertIn(comm.letter, ("D", "F"))

    def test_outputs_render(self):
        md = pip_pip.render_markdown(self.review)
        self.assertIn("PERFORMANCE IMPROVEMENT PLAN", md)
        self.assertIn("30-day improvement plan", md)
        card = pip_pip.render_html(self.review)
        self.assertIn("Performance Improvement Plan", card)
        data = pip_pip.review_to_json(self.review)
        self.assertEqual(data["total_commits"], 8)


class ProfessionalDevTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.repo = os.path.join(cls.tmp, "pro")
        make_repo(cls.repo)
        topics = [
            "add rate limiting to the public api endpoints",
            "refactor invoice totals into a dedicated module",
            "document the deployment rollback procedure",
            "add integration tests for the checkout flow",
            "remove the deprecated v1 search endpoint",
            "improve error messages for failed payments",
        ]
        for i, subject in enumerate(topics):
            commit(cls.repo, at(60 - i * 9, 11), subject,
                   body="Explains what changed and why, for the next reader." if i % 2 == 0 else "",
                   files={f"mod{i}.py": f"# module {i}\nVALUE = {i}\n"} if i == 0 else None,
                   append={"mod0.py": f"# line {i}\n"} if i > 0 else None)
        cls.review = review_of(cls.repo)

    def test_communication_is_strong(self):
        comm = next(c for c in self.review.categories if c.name == "Communication")
        self.assertEqual(comm.letter, "A")
        self.assertEqual(self.review.highlights["vague"], 0)

    def test_reliability_is_strong(self):
        rel = next(c for c in self.review.categories if c.name == "Reliability")
        self.assertEqual(rel.letter, "A")
        self.assertEqual(self.review.highlights["night_commits"], 0)

    def test_overall(self):
        self.assertIn(self.review.overall_letter, ("A", "B"))


class CliTest(unittest.TestCase):
    def test_not_a_repo(self):
        with tempfile.TemporaryDirectory() as d:
            proc = subprocess.run(
                [sys.executable, os.path.join(os.path.dirname(__file__), "..", "pip_pip.py"), d],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("not a git repository", proc.stderr)


if __name__ == "__main__":
    unittest.main()
