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


def commit(repo, when, subject, body="", files=None, append=None, author=None, remove=None):
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
    if remove:
        for name in remove:
            os.remove(os.path.join(repo, name))
    _run(repo, "add", "-A")
    iso = when.isoformat()
    env = {"GIT_AUTHOR_DATE": iso, "GIT_COMMITTER_DATE": iso}
    if author:
        if "<" in author and author.endswith(">"):
            env["GIT_AUTHOR_NAME"] = author.split("<")[0].strip()
            env["GIT_AUTHOR_EMAIL"] = author.split("<")[1][:-1].strip()
        else:
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


def review_of(repo, **kw):
    commits = pip_pip.collect_commits(repo, 10000)
    stats, file_totals = pip_pip.collect_numstat(repo, {c.sha for c in commits})
    for c in commits:
        if c.sha in stats:
            c.added, c.deleted, c.files = stats[c.sha]
    markers = pip_pip.collect_markers(repo)
    return pip_pip.analyze(repo, commits, markers, None, date.today(),
                            file_totals=file_totals, **kw)


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


class V2FeaturesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.repo = os.path.join(cls.tmp, "v2")
        make_repo(cls.repo)
        # Dev Example: messy habits (same shape as MessyDevTest)
        commit(cls.repo, at(400, 10), "initial commit with project scaffold and readme",
               files={"app.py": "# TODO: refactor this someday\nprint('v1')\n"})
        commit(cls.repo, at(300, 23, 30), "stuff", append={"app.py": "print('more')\n"})
        commit(cls.repo, at(299, 1, 15), "wip", append={"app.py": "print('even more')\n"})
        commit(cls.repo, at(50, 9), "asdf", append={"app.py": "print('x')\n"})
        commit(cls.repo, at(280, 23, 45), "hmm", append={"app.py": "print('late')\n"})
        commit(cls.repo, at(270, 10), "tweaks", append={"app.py": "print('t')\n"})
        commit(cls.repo, at(260, 12), "more stuff", append={"app.py": "print('ms')\n"})
        commit(cls.repo, at(250, 14), "checkpoint", append={"app.py": "print('c')\n"})
        commit(cls.repo, at(240, 16), "updates", append={"app.py": "print('u')\n"})
        commit(cls.repo, at(10, 15), "implement user settings page with validation and tests",
               body="Adds the settings form, server validation, and tests.",
               append={"app.py": "print('settings')\n"})
        # Second author: tidy, daytime, explained
        for i, subject in enumerate([
                "add billing export to csv with tests",
                "document the on-call rotation and escalation",
                "refactor session cache into its own module"]):
            commit(cls.repo, at(30 - i * 5, 11), subject,
                   body="Context and reasoning for the next reader.",
                   author="Tidy Example <tidy@example.com>",
                   files={f"tidy{i}.py": f"# tidy {i}\n"} if i == 0 else None,
                   append={"tidy0.py": f"# more {i}\n"} if i > 0 else None)
        cls.review = review_of(cls.repo)

    def test_awards_and_nemesis(self):
        titles = [t for t, _ in self.review.awards]
        self.assertIn("Night Owl", titles)          # 2 of 5 commits at night = 40%
        self.assertIn("Fossil Keeper", titles)      # TODO is 400 days old
        self.assertEqual(self.review.highlights["nemesis_file"], "app.py")
        self.assertGreater(self.review.highlights["nemesis_churn"], 0)

    def test_svg_and_badge(self):
        svg = pip_pip.render_svg(self.review)
        self.assertIn("<svg", svg)
        self.assertIn("PERFORMANCE IMPROVEMENT PLAN", svg)
        self.assertIn(self.review.overall_letter, svg)
        badge = pip_pip.render_badge(self.review)
        self.assertIn("my PIP grade", badge)

    def test_personas_change_the_verdict_not_the_facts(self):
        brutal = review_of(self.repo, persona="brutal")
        self.assertEqual(brutal.categories[0].score, self.review.categories[0].score)
        self.assertNotEqual(pip_pip.verdict_for(brutal), pip_pip.verdict_for(self.review))
        md = pip_pip.render_markdown(brutal)
        self.assertIn("Startup CTO", md)

    def test_scope_commits_known_answer(self):
        commits = pip_pip.collect_commits(self.repo, 10000)
        scoped = pip_pip.scope_commits(commits, 30)
        # anchor is the newest commit (10 days ago); within 30 days of it:
        # the 10-day and 30/25/20-day commits survive, the rest do not.
        self.assertEqual(len(scoped), 4)

    def test_leaderboard_ranks_both_authors(self):
        commits = pip_pip.collect_commits(self.repo, 10000)
        stats, file_totals = pip_pip.collect_numstat(self.repo, {c.sha for c in commits})
        for c in commits:
            if c.sha in stats:
                c.added, c.deleted, c.files = stats[c.sha]
        markers = pip_pip.collect_markers(self.repo)
        board = pip_pip.leaderboard(self.repo, commits, markers, date.today(),
                                    file_totals=file_totals, min_commits=3)
        self.assertEqual(len(board), 2)
        self.assertEqual(board[0].author, "Tidy Example")
        text = pip_pip.render_leaderboard(board, "v2")
        self.assertIn("LEADERBOARD", text)


class CloneTargetTest(unittest.TestCase):
    def test_detection(self):
        self.assertTrue(pip_pip.is_clone_target("https://github.com/psf/requests.git"))
        self.assertTrue(pip_pip.is_clone_target("git@github.com:psf/requests.git"))
        self.assertTrue(pip_pip.is_clone_target("psf/requests"))
        self.assertFalse(pip_pip.is_clone_target("."))
        self.assertFalse(pip_pip.is_clone_target("./some/path"))
        self.assertFalse(pip_pip.is_clone_target("/abs/path"))

    def test_expansion_and_label(self):
        self.assertEqual(pip_pip.expand_clone_url("psf/requests"),
                         "https://github.com/psf/requests.git")
        self.assertEqual(pip_pip.expand_clone_url("https://x.dev/a/b.git"),
                         "https://x.dev/a/b.git")
        self.assertEqual(pip_pip.clone_label("https://github.com/psf/requests.git"), "requests")
        self.assertEqual(pip_pip.clone_label("git@github.com:psf/requests.git"), "requests")

    def test_clone_via_file_url_and_review(self):
        tmp = tempfile.mkdtemp()
        src = os.path.join(tmp, "origin")
        make_repo(src)
        commit(src, at(30, 10), "a perfectly reasonable commit message here",
               files={"a.py": "print(1)\n"})
        commit(src, at(20, 11), "another reasonable commit with detail",
               body="Explains the change for the next reader.",
               append={"a.py": "print(2)\n"})
        dest, root = pip_pip.clone_repo(f"file://{src}")
        try:
            self.assertTrue(os.path.isdir(os.path.join(dest, ".git")))
            review = review_of(dest)
            self.assertEqual(review.total_commits, 2)
            self.assertEqual(review.repo_name, "origin")
        finally:
            import shutil
            shutil.rmtree(root, ignore_errors=True)

    def test_clone_missing_repo_is_a_clean_error(self):
        with self.assertRaises(pip_pip.PipError):
            pip_pip.clone_repo("file:///nonexistent/definitely-not-here.git")


class V4FeaturesTest(unittest.TestCase):
    def test_identity_grouping_by_email(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "ids")
        make_repo(repo)
        for i in range(3):
            commit(repo, at(60 - i * 10, 10), f"solid piece of work number {i} with detail",
                   author="Sam Dev <sam@example.com>",
                   files={"s.py": f"# {i}\n"} if i == 0 else None,
                   append={"s.py": f"# more {i}\n"} if i > 0 else None)
        for i in range(2):
            commit(repo, at(35 - i * 10, 10), f"another explained change {i} for the record",
                   author="Samuel Dev <sam@example.com>",
                   append={"s.py": f"# alt {i}\n"})
        review = review_of(repo)
        self.assertEqual(review.author, "Sam Dev")       # most-used name wins
        self.assertEqual(review.total_commits, 5)        # both names merged

    def test_career_stats_and_awards(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "career")
        make_repo(repo)
        big = "".join(f"line {i}\n" for i in range(1200))
        poly = {f"f.{ext}": "".join(f"x{i}\n" for i in range(30))
                for ext in ("py", "js", "rs", "go", "rb")}
        commit(repo, at(200, 9), "set up the project skeleton and tooling", files=poly)
        commit(repo, at(100, 9), "import the legacy data dump for migration", files={"big.py": big})
        commit(repo, at(99, 9), "remove the legacy data dump after migration", remove=["big.py"])
        # Marathon day: 15 commits on one day, 20 days ago
        for i in range(15):
            commit(repo, at(20, 9, i), f"incremental improvement step {i} to the parser",
                   append={"f.py": f"# step {i}\n"})
        review = review_of(repo)
        titles = [t for t, _ in review.awards]
        self.assertIn("Marathon Day", titles)
        self.assertIn("The Purge", titles)
        self.assertIn("Polyglot", titles)
        self.assertEqual(review.highlights["busiest_day_count"], 15)
        self.assertEqual(review.highlights["max_deleted_single"], 1200)
        langs = [name for name, _ in review.highlights["languages"]]
        self.assertIn("Python", langs)
        self.assertIn("Rust", langs)

    def test_reference_letter(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "refcheck")
        make_repo(repo)
        commit(repo, at(12, 10), "a documented change worthy of a reference",
               files={"a.py": "print(1)\n"})
        commit(repo, at(4, 10), "a second explained improvement for the record",
               append={"a.py": "print(2)\n"})
        review = review_of(repo)
        letter = pip_pip.render_reference(review)
        self.assertIn("Letter of reference", letter)
        self.assertIn(review.author, letter)
        self.assertIn(review.overall_letter, letter)

    def test_since_until_via_main(self):
        import contextlib
        import io
        import json as jsonlib
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "window")
        make_repo(repo)
        commit(repo, at(100, 10), "an old commit from long ago with words", files={"a.py": "x\n"})
        commit(repo, at(10, 10), "a recent commit with a proper message", append={"a.py": "y\n"})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = pip_pip.main([repo, "--since", (date.today() - timedelta(days=30)).isoformat(), "--json"])
        self.assertEqual(rc, 0)
        data = jsonlib.loads(buf.getvalue())
        self.assertEqual(data["total_commits"], 1)


class LeaderboardIdentityTest(unittest.TestCase):
    def test_same_name_different_people_stay_separate(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "twopats")
        make_repo(repo)
        for i in range(3):
            commit(repo, at(50 - i * 5, 10), f"documented change number {i} with context",
                   author="Pat Dev <pat1@example.com>",
                   files={"p.py": f"# {i}\n"} if i == 0 else None,
                   append={"p.py": f"# a{i}\n"} if i > 0 else None)
        for i in range(4):
            commit(repo, at(40 - i * 5, 10), f"explained improvement number {i} for readers",
                   author="Pat Dev <pat2@example.com>",
                   append={"p.py": f"# b{i}\n"})
        commits = pip_pip.collect_commits(repo, 10000)
        stats, file_totals = pip_pip.collect_numstat(repo, {c.sha for c in commits})
        for c in commits:
            if c.sha in stats:
                c.added, c.deleted, c.files = stats[c.sha]
        markers = pip_pip.collect_markers(repo)
        board = pip_pip.leaderboard(repo, commits, markers, date.today(),
                                    file_totals=file_totals, min_commits=3)
        self.assertEqual(len(board), 2)
        self.assertEqual(sorted(r.total_commits for r in board), [3, 4])


class ReadmeModeTest(unittest.TestCase):
    def _repo_with_readme(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "demo")
        make_repo(repo)
        commit(repo, at(15, 10), "a well explained change for the demo repo",
               files={"a.py": "print(1)\n"})
        commit(repo, at(5, 10), "another documented improvement to the demo",
               append={"a.py": "print(2)\n"})
        with open(os.path.join(repo, "README.md"), "w") as f:
            f.write("# Demo\n\nA fine project.\n")
        return repo

    def test_readme_section_written_once_and_refreshed(self):
        repo = self._repo_with_readme()
        review = review_of(repo)
        readme, card, badge = pip_pip.update_readme(repo, review)
        self.assertTrue(os.path.isfile(card))
        self.assertTrue(os.path.isfile(badge))
        with open(card) as f:
            self.assertIn("<svg", f.read())
        with open(readme) as f:
            text = f.read()
        self.assertEqual(text.count(pip_pip.README_START), 1)
        self.assertIn("My PIP review", text)
        self.assertIn("# Demo", text)
        pip_pip.update_readme(repo, review)
        with open(readme) as f:
            text2 = f.read()
        self.assertEqual(text2.count(pip_pip.README_START), 1)
        self.assertEqual(text2.count("My PIP review"), 1)

    def test_readme_missing_is_a_clean_error(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "bare")
        make_repo(repo)
        commit(repo, at(3, 10), "a commit in a repo without a readme file",
               files={"a.py": "x\n"})
        review = review_of(repo)
        with self.assertRaises(pip_pip.PipError):
            pip_pip.update_readme(repo, review)
