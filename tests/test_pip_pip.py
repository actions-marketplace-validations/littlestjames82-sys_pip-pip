"""Tests for pip-pip, built on synthetic git repos with scripted habits.

The repos are constructed with exact commit counts, hours, weekdays and
message quality, so the expected metrics are known answers, not guesses.
"""
import io
import json
import os
import shutil
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


def weekday_at(days_ago, weekday, hour, minute=0):
    """Pin a commit to a specific weekday (0=Mon) near days_ago, so fixtures
    that count weekday-sensitive metrics stay true on any run date."""
    d = date.today() - timedelta(days=days_ago)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return datetime.combine(d, time(hour, minute), tzinfo=UTC)


def review_of(repo, **kw):
    commits = pip_pip.collect_commits(repo, 10000)
    stats, file_totals, paths_by_sha = pip_pip.collect_numstat(repo, {c.sha for c in commits})
    for c in commits:
        if c.sha in stats:
            c.added, c.deleted, c.files = stats[c.sha]
            c.paths = tuple(paths_by_sha.get(c.sha, ()))
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
        commit(cls.repo, weekday_at(300, 2, 23, 30), "stuff", append={"app.py": "print('more')\n"})
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


class OrgRunTest(unittest.TestCase):
    """_run_org end to end with the GitHub listing faked to a local repo.

    Regression: v1.1.0 crashed with NameError (tempfile never imported at
    module level) the first time the flow got past the API call.
    """

    def test_org_run_reviews_local_repos(self):
        import types
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        repo = os.path.join(tmp, "demo-src")
        make_repo(repo)
        commit(repo, datetime(2026, 1, 5, 10, 0, tzinfo=timezone.utc), "feat: one",
               files={"a.py": "x = 1\n"})
        commit(repo, datetime(2026, 1, 6, 10, 0, tzinfo=timezone.utc), "fix: two",
               files={"a.py": "x = 2\n"})
        orig = pip_pip.fetch_org_repos
        pip_pip.fetch_org_repos = lambda org, limit, include_forks: [("demo", repo)]
        args = types.SimpleNamespace(org="demo-org", org_limit=5, include_forks=False,
                                     persona=None, max_commits=10000, json=False,
                                     csv=None, shallow=None)
        try:
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = pip_pip._run_org(args)
        finally:
            pip_pip.fetch_org_repos = orig
        self.assertEqual(code, 0)
        out = buf.getvalue()
        self.assertIn("demo", out)
        self.assertIn("Dev Example", out)


class WrappedKitTest(unittest.TestCase):
    def _review(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        repo = os.path.join(tmp, "demo")
        make_repo(repo)
        commit(repo, datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc),
               "feat: spring thing", files={"a.py": "x = 1\n"})
        commit(repo, datetime(2026, 3, 6, 23, 0, tzinfo=timezone.utc),
               "fix: late fix", files={"a.py": "x = 2\n"})
        commits = pip_pip.collect_commits(repo, 10000)
        stats, file_totals, paths_by_sha = pip_pip.collect_numstat(
            repo, {c.sha for c in commits})
        for c in commits:
            if c.sha in stats:
                c.added, c.deleted, c.files = stats[c.sha]
            c.paths = tuple(paths_by_sha.get(c.sha, ()))
        markers = pip_pip.collect_markers(repo)
        return pip_pip.analyze(repo, commits, markers, None,
                               datetime(2026, 12, 1, tzinfo=timezone.utc).date())

    def test_posts_short_fits_x_and_carry_the_facts(self):
        text = pip_pip.render_wrapped_posts(self._review(), 2026)
        short = text.split("\n")[1]
        self.assertLessEqual(len(short), 280)
        self.assertIn("pip install on-a-pip", short)
        self.assertIn("2026", short)
        self.assertIn("Not for employment", text)

    def test_kit_writes_card_and_posts(self):
        import contextlib
        from unittest import mock
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, True)
        repo = os.path.join(tmp, "demo")
        make_repo(repo)
        commit(repo, datetime(2026, 3, 5, 10, 0, tzinfo=timezone.utc),
               "feat: spring thing", files={"a.py": "x = 1\n"})
        kit = os.path.join(tmp, "kit")
        argv = ["on-a-pip", repo, "--year", "2026", "--wrapped-kit", kit,
                "--author", "Dev Example"]
        buf = io.StringIO()
        with mock.patch.object(sys, "argv", argv):
            with contextlib.redirect_stdout(buf):
                code = pip_pip.main()
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(os.path.join(kit, "wrapped-2026.svg")))
        posts = open(os.path.join(kit, "post.txt")).read()
        self.assertIn("SHORT", posts)
        self.assertIn("STANDARD", posts)


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
        stats, file_totals, paths_by_sha = pip_pip.collect_numstat(self.repo, {c.sha for c in commits})
        for c in commits:
            if c.sha in stats:
                c.added, c.deleted, c.files = stats[c.sha]
                c.paths = tuple(paths_by_sha.get(c.sha, ()))
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
        stats, file_totals, paths_by_sha = pip_pip.collect_numstat(repo, {c.sha for c in commits})
        for c in commits:
            if c.sha in stats:
                c.added, c.deleted, c.files = stats[c.sha]
                c.paths = tuple(paths_by_sha.get(c.sha, ()))
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


class IsoParseTest(unittest.TestCase):
    def test_z_suffix_and_offsets(self):
        # Modern git emits 'Z' for UTC in %aI; Python < 3.11 fromisoformat
        # rejects it, which silently dropped every UTC commit. Regression test.
        self.assertEqual(pip_pip._parse_iso("2026-01-23T23:30:00Z").hour, 23)
        self.assertEqual(pip_pip._parse_iso("2026-01-23T23:30:00+00:00").hour, 23)
        self.assertEqual(pip_pip._parse_iso("2026-01-23T23:30:00-05:00").utcoffset(),
                         timedelta(hours=-5))


class V6FeaturesTest(unittest.TestCase):
    def _two_author_repo(self, tmp):
        repo = os.path.join(tmp, "versus")
        make_repo(repo)
        commit(repo, at(30, 23, 30), "stuff", files={"a.py": "x\n"})
        commit(repo, at(29, 1, 0), "wip", append={"a.py": "y\n"})
        commit(repo, at(28, 9), "asdf", append={"a.py": "z\n"})
        for i, subject in enumerate([
                "add export feature with tests and docs",
                "fix session timeout with a regression test",
                "document the deployment process for the team"]):
            commit(repo, at(20 - i * 3, 11), subject,
                   body="Reasoning recorded for the next reader.",
                   author="Tidy Example <tidy@example.com>",
                   files={"t.py": f"# {i}\n"} if i == 0 else None,
                   append={"t.py": f"# m{i}\n"} if i > 0 else None)
        return repo

    def test_head_to_head(self):
        tmp = tempfile.mkdtemp()
        repo = self._two_author_repo(tmp)
        commits = pip_pip.collect_commits(repo, 10000)
        stats, file_totals, paths_by_sha = pip_pip.collect_numstat(repo, {c.sha for c in commits})
        for c in commits:
            if c.sha in stats:
                c.added, c.deleted, c.files = stats[c.sha]
                c.paths = tuple(paths_by_sha.get(c.sha, ()))
        markers = pip_pip.collect_markers(repo)
        dev = pip_pip.analyze(repo, commits, markers, "Dev Example", date.today(),
                              file_totals=file_totals)
        tidy = pip_pip.analyze(repo, commits, markers, "Tidy", date.today(),
                               file_totals=file_totals)
        text = pip_pip.render_vs(dev, tidy)
        self.assertIn("HEAD TO HEAD", text)
        self.assertIn("Tidy Example wins decisively", text)
        md = pip_pip.render_vs_markdown(dev, tidy)
        self.assertIn("**Overall**", md)
        self.assertIn("Tidy Example", md)

    def test_scan_finds_each_repo(self):
        tmp = tempfile.mkdtemp()
        root = os.path.join(tmp, "fleet")
        os.makedirs(root)
        for name, author in (("alpha", None), ("beta", "Tidy Example <tidy@example.com>")):
            repo = os.path.join(root, name)
            make_repo(repo)
            commit(repo, at(9, 10), "a documented change for the scan fixture",
                   author=author, files={"a.py": "x\n"})
            commit(repo, at(4, 10), "a second explained improvement on record",
                   author=author, append={"a.py": "y\n"})
        os.makedirs(os.path.join(root, "not-a-repo"))
        results = pip_pip.scan_repos(root)
        self.assertEqual(sorted(name for name, _ in results), ["alpha", "beta"])
        text = pip_pip.render_scan(results, "fleet")
        self.assertIn("PIP SCAN", text)

    def test_mailmap_merges_identities(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "mapped")
        make_repo(repo)
        mailmap = "Canon Name <canon@example.com> <alt@example.com>\n"
        commit(repo, at(40, 10), "first canonical commit with explanation",
               author="Canon Name <canon@example.com>",
               files={".mailmap": mailmap, "a.py": "x\n"})
        commit(repo, at(30, 10), "second canonical commit with explanation",
               author="Canon Name <canon@example.com>", append={"a.py": "y\n"})
        commit(repo, at(20, 10), "an alt identity commit with explanation",
               author="Alt Name <alt@example.com>", append={"a.py": "z\n"})
        commit(repo, at(10, 10), "another alt identity commit on record",
               author="Alt Name <alt@example.com>", append={"a.py": "w\n"})
        review = review_of(repo)
        self.assertEqual(review.author, "Canon Name")
        self.assertEqual(review.total_commits, 4)


class V7FeaturesTest(unittest.TestCase):
    def test_hall_of_fame(self):
        MessyDevTest.setUpClass()
        review = MessyDevTest.review
        self.assertEqual(review.highlights["longest_subject"],
                         "implement user settings page with validation and tests")
        # "wip" and "fix" tie at 3 chars; ties resolve to the earliest commit.
        self.assertEqual(review.highlights["shortest_subject"], "wip")

    def test_catchphrase(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "catchy")
        make_repo(repo)
        for i, noun in enumerate(["parser", "loader", "writer"]):
            commit(repo, at(20 - i * 5, 10), f"refactor the {noun} module",
                   files={"m.py": f"# {noun}\n"} if i == 0 else None,
                   append={"m.py": f"# more {noun}\n"} if i > 0 else None)
        review = review_of(repo)
        self.assertEqual(review.highlights["top_word"], "refactor")
        self.assertEqual(review.highlights["top_word_count"], 3)

    def test_svg_has_month_bars(self):
        MessyDevTest.setUpClass()
        svg = pip_pip.render_svg(MessyDevTest.review)
        self.assertIn("Commits per month", svg)

    def _quiet_main(self, argv):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            return pip_pip.main(argv)

    def test_year_mode_filters(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "years")
        make_repo(repo)
        commit(repo, at(500, 12), "an old explained change from long ago", files={"a.py": "x\n"})
        commit(repo, at(10, 12), "a recent explained change for the team", append={"a.py": "y\n"})
        old_year = (date.today() - timedelta(days=500)).year
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = pip_pip.main([repo, "--year", str(old_year), "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(buf.getvalue())
        self.assertEqual(data["total_commits"], 1)

    def test_wrapped_renders(self):
        ProfessionalDevTest.setUpClass()
        review = review_of(ProfessionalDevTest.repo)
        text = pip_pip.render_wrapped(review, 2026)
        self.assertIn("YOUR 2026 IN COMMITS", text)
        svg = pip_pip.render_wrapped_svg(review, 2026)
        self.assertIn("YOUR 2026 IN COMMITS", svg)

    def test_fail_below_gate(self):
        MessyDevTest.setUpClass()
        repo = MessyDevTest.repo
        self.assertEqual(MessyDevTest.review.overall_letter, "C")
        self.assertEqual(self._quiet_main([repo, "--fail-below", "B"]), 3)
        self.assertEqual(self._quiet_main([repo, "--fail-below", "D"]), 0)

    def test_outdir_writes_everything(self):
        tmp = tempfile.mkdtemp()
        ProfessionalDevTest.setUpClass()
        repo = ProfessionalDevTest.repo
        outdir = os.path.join(tmp, "artifacts")
        self.assertEqual(self._quiet_main([repo, "--outdir", outdir]), 0)
        for fname in ("review.md", "report-card.html", "report-card.svg",
                      "badge.svg", "reference.md", "review.json"):
            self.assertTrue(os.path.exists(os.path.join(outdir, fname)), fname)


class V8FeaturesTest(unittest.TestCase):
    def _quiet_main(self, argv):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = pip_pip.main(argv)
        return rc, buf.getvalue()

    def test_lone_wolf(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "wolf")
        make_repo(repo)
        for i in range(20):
            commit(repo, at(60 - i * 2, 10), f"explained improvement number {i} for the record",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        titles = [t for t, _ in review_of(repo).awards]
        self.assertIn("Lone Wolf", titles)

    def test_rubber_duck(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "duck")
        make_repo(repo)
        body = "Reasoning: " + ("this matters because the reader deserves the full story. " * 5)
        for i in range(5):
            commit(repo, at(30 - i * 3, 10), f"a considered change number {i} with context",
                   body=body, files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        titles = [t for t, _ in review_of(repo).awards]
        self.assertIn("Rubber Duck", titles)

    def test_archaeologist(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "dig")
        make_repo(repo)
        commit(repo, at(800, 10), "create the ancient module with explanation",
               files={"old.py": "# ancient\n"})
        commit(repo, at(400, 10), "meanwhile a newer feature lands elsewhere",
               files={"new.py": "x\n"})
        commit(repo, at(10, 10), "revive the ancient module for a modern need",
               append={"old.py": "# revived\n"})
        titles = [t for t, _ in review_of(repo).awards]
        self.assertIn("The Archaeologist", titles)

    def test_merge_goblin(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "goblin")
        make_repo(repo)

        def env(days_ago):
            when = datetime.now(timezone.utc) - timedelta(days=days_ago)
            stamp = when.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            return dict(GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp,
                        GIT_AUTHOR_NAME="Dev Example", GIT_AUTHOR_EMAIL="dev@example.com",
                        GIT_COMMITTER_NAME="Dev Example", GIT_COMMITTER_EMAIL="dev@example.com")

        def git(*args, days_ago=90):
            _run(repo, *args, env_extra=env(days_ago))

        with open(os.path.join(repo, "a.py"), "w") as f:
            f.write("x\n")
        git("add", "-A")
        git("commit", "-q", "-m", "base commit with an explanation")
        main_branch = subprocess.run(["git", "-C", repo, "branch", "--show-current"],
                                     capture_output=True, text=True).stdout.strip() or "main"
        day = 88
        for cycle in range(2):
            git("checkout", "-q", "-b", f"feat{cycle}", days_ago=day)
            with open(os.path.join(repo, f"f{cycle}.py"), "w") as fh:
                fh.write("y\n")
            git("add", "-A", days_ago=day)
            git("commit", "-q", "-m", f"branch work cycle {cycle} explained", days_ago=day)
            git("checkout", "-q", main_branch, days_ago=day - 1)
            with open(os.path.join(repo, "a.py"), "a") as fh:
                fh.write(f"# main {cycle}\n")
            git("add", "-A", days_ago=day - 1)
            git("commit", "-q", "-m", f"main work cycle {cycle} explained", days_ago=day - 1)
            git("merge", "-q", "--no-ff", f"feat{cycle}", "-m", f"Merge branch feat{cycle}",
                days_ago=day - 2)
            day -= 10
        with open(os.path.join(repo, "a.py"), "a") as fh:
            fh.write("# tail\n")
        git("add", "-A", days_ago=60)
        git("commit", "-q", "-m", "a final explained change for the count", days_ago=60)
        review = review_of(repo)
        self.assertEqual(review.total_commits, 8)
        titles = [t for t, _ in review.awards]
        self.assertIn("Merge Goblin", titles)

    def test_coach_plan(self):
        MessyDevTest.setUpClass()
        review = MessyDevTest.review
        plan = pip_pip.coach_plan(review)
        self.assertEqual(len(plan), 4)
        weakest = {c.name for c in sorted(review.categories, key=lambda c: c.score)[:3]}
        self.assertTrue(all(cat in weakest for _w, cat, _d, _c in plan))
        text = pip_pip.render_coach(review)
        self.assertIn("DEVELOPMENT PLAN", text)
        self.assertIn("Week 1", text)

    def test_history_round_trip(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "hist")
        make_repo(repo)
        commit(repo, at(9, 10), "a documented change for history", files={"a.py": "x\n"})
        commit(repo, at(4, 10), "a second explained improvement on record", append={"a.py": "y\n"})
        rc1, _ = self._quiet_main([repo])
        rc2, _ = self._quiet_main([repo])
        self.assertEqual((rc1, rc2), (0, 0))
        entries = pip_pip.load_history(repo)
        self.assertEqual(len(entries), 2)
        rc3, out = self._quiet_main([repo, "--history"])
        self.assertEqual(rc3, 0)
        self.assertIn("REVIEW HISTORY", out)

    def test_blame_filters_to_file(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "blamey")
        make_repo(repo)
        commit(repo, at(20, 10), "start a with an explanation", files={"a.py": "x\n"})
        commit(repo, at(15, 10), "start b with an explanation", files={"b.py": "x\n"})
        commit(repo, at(10, 10), "extend a further with context", append={"a.py": "y\n"})
        commit(repo, at(5, 10), "extend b further with context", append={"b.py": "y\n"})
        rc, out = self._quiet_main([repo, "--blame", "b.py", "--json"])
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["total_commits"], 2)
        self.assertIn("b.py", data["repo"])

    def test_pip_toml_config_and_cli_override(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "cfg")
        make_repo(repo)
        with open(os.path.join(repo, ".pip.toml"), "w") as f:
            f.write('persona = "brutal"\n')
        commit(repo, at(9, 10), "a documented change for config", files={"a.py": "x\n"})
        commit(repo, at(4, 10), "a second explained improvement on record", append={"a.py": "y\n"})
        rc, out = self._quiet_main([repo, "--json"])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)["persona"], "brutal")
        rc, out = self._quiet_main([repo, "--json", "--persona", "corporate"])
        self.assertEqual(json.loads(out)["persona"], "corporate")


class V9FeaturesTest(unittest.TestCase):
    def test_builtin_pirate_persona(self):
        ProfessionalDevTest.setUpClass()
        review = review_of(ProfessionalDevTest.repo, persona="pirate")
        md = pip_pip.render_markdown(review)
        self.assertIn("Pirate Captain", md)

    def test_persona_file_pack(self):
        tmp = tempfile.mkdtemp()
        pack = os.path.join(tmp, "coach.json")
        with open(pack, "w") as f:
            json.dump({"name": "Drill Sergeant", "label": "Drill Sergeant",
                       "verdicts": {"A": "ACCEPTABLE. BARELY. DO IT AGAIN."}}, f)
        key = pip_pip.load_persona_file(pack)
        self.assertEqual(key, "drill-sergeant")
        ProfessionalDevTest.setUpClass()
        review = review_of(ProfessionalDevTest.repo, persona=key)
        self.assertEqual(review.overall_letter, "A")
        self.assertIn("ACCEPTABLE. BARELY.", pip_pip.verdict_for(review))
        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w") as f:
            f.write("{not json")
        with self.assertRaises(pip_pip.PipError):
            pip_pip.load_persona_file(bad)

    def test_pair_stats_shared_days(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "pairs")
        make_repo(repo)
        commit(repo, at(10, 10), "alpha works day one with explanation", files={"a.py": "x\n"})
        commit(repo, at(9, 10), "alpha works day two with explanation", append={"a.py": "y\n"})
        commit(repo, at(10, 12), "beta joins on day one with explanation",
               author="Beta Dev <beta@example.com>", files={"b.py": "x\n"})
        commit(repo, at(8, 10), "beta works day three with explanation",
               author="Beta Dev <beta@example.com>", append={"b.py": "y\n"})
        commits = pip_pip.collect_commits(repo, 1000)
        pairs = pip_pip.pair_stats(commits)
        self.assertEqual(len(pairs), 1)
        a, b, shared = pairs[0]
        self.assertEqual({a, b}, {"Dev Example", "Beta Dev"})
        self.assertEqual(shared, 1)

    def test_fetch_org_repos_filters(self):
        import io
        import urllib.error
        payload = json.dumps([
            {"name": "one", "clone_url": "https://x/one.git", "fork": False, "archived": False},
            {"name": "forked", "clone_url": "https://x/f.git", "fork": True, "archived": False},
            {"name": "old", "clone_url": "https://x/o.git", "fork": False, "archived": True},
            {"name": "two", "clone_url": "https://x/two.git", "fork": False, "archived": False},
            {"name": "three", "clone_url": "https://x/three.git", "fork": False, "archived": False},
        ]).encode()

        def opener(req):
            return io.BytesIO(payload)

        repos = pip_pip.fetch_org_repos("someone", limit=2, _opener=opener)
        self.assertEqual(repos, [("one", "https://x/one.git"), ("two", "https://x/two.git")])
        repos = pip_pip.fetch_org_repos("someone", limit=10, include_forks=True, _opener=opener)
        self.assertIn(("forked", "https://x/f.git"), repos)
        self.assertNotIn(("old", "https://x/o.git"), repos)

        def not_found(req):
            raise urllib.error.HTTPError("https://api.github.com", 404, "Not Found", None, None)

        with self.assertRaises(pip_pip.PipError):
            pip_pip.fetch_org_repos("ghost", _opener=not_found)

    def test_render_org_board(self):
        MessyDevTest.setUpClass()
        ProfessionalDevTest.setUpClass()
        rows = [("messy", MessyDevTest.review),
                ("tidy", review_of(ProfessionalDevTest.repo))]
        rows.sort(key=lambda kv: -kv[1].overall_score)
        text = pip_pip.render_org(rows, "someone")
        self.assertIn("PIP ORG BOARD", text)
        self.assertIn("Org MVP", text)


class V10FeaturesTest(unittest.TestCase):
    def test_bots_excluded_by_default(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "bots")
        make_repo(repo)
        for i in range(10):
            commit(repo, at(40 - i * 2, 10), "chore(deps): bump the thing from 1 to 2",
                   author="dependabot[bot] <dependabot[bot]@users.noreply.github.com>",
                   files={"deps.txt": "x\n"} if i == 0 else None,
                   append={"deps.txt": f"# {i}\n"} if i > 0 else None)
        for i in range(6):
            commit(repo, at(30 - i * 2, 11), f"a human improvement number {i} with explanation",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        review = review_of(repo)
        self.assertEqual(review.author, "Dev Example")
        board = pip_pip.leaderboard(repo, pip_pip.collect_commits(repo, 1000),
                                    pip_pip.collect_markers(repo), date.today())
        self.assertEqual([r.author for r in board], ["Dev Example"])
        board_with_bots = pip_pip.leaderboard(
            repo, pip_pip.collect_commits(repo, 1000), pip_pip.collect_markers(repo),
            date.today(), include_bots=True)
        self.assertEqual(len(board_with_bots), 2)

    def test_coauthor_gets_credit(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "coauth")
        make_repo(repo)
        for i in range(3):
            commit(repo, at(20 - i * 3, 10), f"paired work number {i} with explanation",
                   body="Co-authored-by: Beta Dev <beta@example.com>",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        commit(repo, at(5, 10), "beta solo change with explanation",
               author="Beta Dev <beta@example.com>", append={"a.py": "solo\n"})
        groups = {name: len(cs) for name, cs, _k in pip_pip._author_groups(
            pip_pip.collect_commits(repo, 1000))}
        self.assertEqual(groups["Beta Dev"], 4)
        self.assertEqual(groups["Dev Example"], 3)

    def test_timezone_override_changes_night_verdict(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "tz")
        make_repo(repo)
        for i in range(10):
            when = (datetime.now(timezone.utc) - timedelta(days=30 - i * 2)).replace(
                hour=23, minute=30, second=0, microsecond=0)
            commit(repo, when, f"late work number {i} with a full explanation",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        plain = review_of(repo)
        self.assertEqual(plain.highlights["night_commits"], 10)
        shifted = review_of(repo, tz=pip_pip.parse_tz("UTC+12"))
        self.assertEqual(shifted.highlights["night_commits"], 0)
        self.assertEqual(pip_pip.parse_tz("UTC+05:30").utcoffset(None),
                         timedelta(hours=5, minutes=30))
        with self.assertRaises(pip_pip.PipError):
            pip_pip.parse_tz("Mars/Olympus")

    def test_generated_files_excluded_from_churn(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "gen")
        make_repo(repo)
        lock = "".join(f"lock line {i}\n" for i in range(500))
        commit(repo, at(9, 10), "add the app and its lockfile with explanation",
               files={"app.py": "x\n" * 10, "package-lock.json": lock})
        review = review_of(repo)
        self.assertEqual(int(review.highlights["added"]), 10)
        commits = pip_pip.collect_commits(repo, 100)
        _s, totals, _p = pip_pip.collect_numstat(repo, {c.sha for c in commits},
                                                 exclude_generated=False)
        self.assertEqual(totals["package-lock.json"][0], 500)

    def test_branch_and_path_filters(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "filters")
        make_repo(repo)
        commit(repo, at(20, 10), "base work on a with explanation", files={"a.py": "x\n"})
        commit(repo, at(18, 10), "base work on b with explanation", files={"b.py": "x\n"})
        main_branch = subprocess.run(["git", "-C", repo, "branch", "--show-current"],
                                     capture_output=True, text=True).stdout.strip() or "main"
        _run(repo, "checkout", "-q", "-b", "feature")
        commit(repo, at(10, 10), "feature work on b with explanation", append={"b.py": "y\n"})
        commit(repo, at(9, 10), "more feature work on b explained", append={"b.py": "z\n"})
        _run(repo, "checkout", "-q", main_branch)
        self.assertEqual(len(pip_pip.collect_commits(repo, 100)), 2)
        self.assertEqual(len(pip_pip.collect_commits(repo, 100, branch="feature")), 4)
        self.assertEqual(len(pip_pip.collect_commits(repo, 100, branch=main_branch)), 2)
        self.assertEqual(len(pip_pip.collect_commits(repo, 100, branch="feature", path="b.py")), 3)
        with self.assertRaises(pip_pip.PipError):
            pip_pip.collect_commits(repo, 100, branch="no-such-branch")

    def test_squash_confidence_note(self):
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "squashy")
        make_repo(repo)
        for i in range(5):
            suffix = f" (#{100 + i})" if i < 3 else ""
            commit(repo, at(20 - i * 2, 10), f"a change number {i} with explanation{suffix}",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        review = review_of(repo)
        self.assertAlmostEqual(review.highlights["squash_ratio"], 0.6)
        self.assertIn("Authorship note", pip_pip.render_markdown(review))

    def test_clone_label_handles_windows_paths(self):
        self.assertEqual(pip_pip.clone_label(r"file://C:\Users\dev\AppData\origin"), "origin")
        self.assertEqual(pip_pip.clone_label("file:///home/dev/origin"), "origin")
        self.assertEqual(pip_pip.clone_label("https://github.com/psf/requests.git"), "requests")

    def test_share_card_and_csv(self):
        ProfessionalDevTest.setUpClass()
        review = review_of(ProfessionalDevTest.repo)
        svg = pip_pip.render_share_svg(review)
        self.assertIn('width="1200" height="630"', svg)
        self.assertIn("Not for employment decisions", svg)
        csv_text = pip_pip.boards_to_csv([("repo", review)], with_repo=True)
        self.assertIn("author,grade,score", csv_text.replace("repo,", "", 1) if False else csv_text)
        self.assertIn(review.author, csv_text)
        md = pip_pip.render_markdown(review)
        self.assertIn("Not for employment decisions", md)


class BotPatternTest(unittest.TestCase):
    def test_dash_bot_names_are_bots_but_surnames_are_not(self):
        self.assertTrue(pip_pip._is_bot("vue-bot", "vue-bot@users.noreply.github.com"))
        self.assertTrue(pip_pip._is_bot("ci-bot", "ci@example.com"))
        self.assertTrue(pip_pip._is_bot("my_bot", "b@example.com"))
        self.assertFalse(pip_pip._is_bot("Talbot", "talbot@example.com"))
        self.assertFalse(pip_pip._is_bot("Abbot", "abbot@example.com"))
        self.assertFalse(pip_pip._is_bot("Sam Dev", "sam@example.com"))


class V11FixTest(unittest.TestCase):
    def test_leaderboard_never_duplicates_a_shared_name(self):
        # Two identities share the display name "Sam Dev": one keyed by
        # email, one name-keyed (empty email). The board must show both,
        # with their own commit counts, never the big group twice.
        tmp = tempfile.mkdtemp()
        repo = os.path.join(tmp, "sam")
        make_repo(repo)
        for i in range(8):
            commit(repo, at(30 - i * 2, 10), f"sam email work number {i} with explanation",
                   author="Sam Dev <sam@example.com>",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        for i in range(5):
            commit(repo, at(29 - i * 2, 11), f"sam noemail work number {i} with explanation",
                   author="Sam Dev <>",
                   files={"b.py": "x\n"} if i == 0 else None,
                   append={"b.py": f"# {i}\n"} if i > 0 else None)
        board = pip_pip.leaderboard(repo, pip_pip.collect_commits(repo, 1000),
                                    pip_pip.collect_markers(repo), date.today())
        counts = sorted(r.total_commits for r in board if r.author == "Sam Dev")
        self.assertEqual(counts, [5, 8])


class AuthorshipTest(unittest.TestCase):
    """The authorship check: how much of a history is the reviewed
    author's own work. Fixtures are scripted so every number is a known
    answer, including the rebranded-fork pattern that prompted the check:
    a long upstream history under other names, one late commit by the
    reviewed author."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.repo = os.path.join(cls.tmp, "inherited")
        make_repo(cls.repo)
        upstream = ([("Timothy Carambat", "timothy@example.com")] * 20
                    + [("timothycarambat", "tc@example.net")] * 12
                    + [("Marcello Fitton", "marcello@example.com")] * 8)
        for i, (name, email) in enumerate(upstream):
            commit(cls.repo, at(400 - i, 10), f"upstream feature work number {i}",
                   author=f"{name} <{email}>",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        commit(cls.repo, at(5, 10), "Update README.md",
               author="Steven Leake <steven@example.com>",
               append={"a.py": "# readme\n"})
        cls.review = cls._filtered(cls.repo, "Steven Leake")

    @staticmethod
    def _filtered(repo, author_filter, **kw):
        commits = pip_pip.collect_commits(repo, 10000)
        markers = pip_pip.collect_markers(repo)
        return pip_pip.analyze(repo, commits, markers, author_filter,
                               date.today(), **kw)

    def test_inherited_history_numbers(self):
        a = self.review.authorship
        self.assertIsNotNone(a)
        self.assertEqual(a.history_commits, 41)
        self.assertEqual(a.author_commits, 1)
        self.assertAlmostEqual(a.author_share, 1 / 41)
        self.assertEqual(a.inherited, 40)
        self.assertEqual(a.inherited_before, 40)
        self.assertEqual(a.author_first, date.today() - timedelta(days=5))
        self.assertEqual(a.history_start, date.today() - timedelta(days=400))

    def test_name_variants_merge_in_histogram(self):
        a = self.review.authorship
        # "Timothy Carambat" (20) and "timothycarambat" (12) are one author.
        self.assertEqual(a.other_authors, 2)
        self.assertEqual(a.top_others[0], ("Timothy Carambat", 32))
        self.assertEqual(a.top_others[1], ("Marcello Fitton", 8))

    def test_inherited_history_is_flagged(self):
        self.assertTrue(self.review.authorship.mostly_inherited)

    def test_flag_is_additive_not_a_score(self):
        # The check describes the record; the five categories and the
        # overall remain exactly their mean, untouched by the flag.
        scores = [c.score for c in self.review.categories]
        self.assertEqual(len(scores), 5)
        self.assertAlmostEqual(self.review.overall_score, sum(scores) / 5)

    def test_authorship_reaches_the_surfaces(self):
        self.assertIn("AUTHORSHIP", pip_pip.render_terminal(self.review))
        self.assertIn("mostly inherited", pip_pip.render_terminal(self.review))
        self.assertIn("## Authorship", pip_pip.render_markdown(self.review))
        self.assertIn("Authorship:", pip_pip.render_html(self.review))
        data = pip_pip.review_to_json(self.review)
        self.assertEqual(data["authorship"]["author_commits"], 1)
        self.assertTrue(data["authorship"]["mostly_inherited"])

    def test_single_author_full_share_no_flag(self):
        repo = os.path.join(self.tmp, "solo")
        make_repo(repo)
        for i in range(25):
            commit(repo, at(100 - i * 3, 10), f"solo feature work number {i}",
                   author="Solo Dev <solo@example.com>",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        a = review_of(repo).authorship
        self.assertEqual(a.history_commits, 25)
        self.assertEqual(a.author_share, 1.0)
        self.assertEqual(a.other_authors, 0)
        self.assertEqual(a.top_others, [])
        self.assertEqual(a.inherited_before, 0)
        self.assertFalse(a.mostly_inherited)

    def test_reviewed_author_name_variants_combine(self):
        repo = os.path.join(self.tmp, "variants")
        make_repo(repo)
        plan = ([("Timothy Carambat", "timothy@example.com")] * 12
                + [("timothycarambat", "tc@example.net")] * 8
                + [("Other Dev", "other@example.com")] * 5)
        for i, (name, email) in enumerate(plan):
            commit(repo, at(200 - i * 4, 10), f"variant history work number {i}",
                   author=f"{name} <{email}>",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        a = review_of(repo).authorship
        # The grader's top identity holds 12; the check sees one person: 20.
        self.assertEqual(a.author_commits, 20)
        self.assertAlmostEqual(a.author_share, 20 / 25)
        self.assertEqual(a.other_authors, 1)
        self.assertFalse(a.mostly_inherited)

    def test_small_history_never_flags(self):
        repo = os.path.join(self.tmp, "small")
        make_repo(repo)
        for i in range(9):
            commit(repo, at(100 - i * 5, 10), f"early upstream work number {i}",
                   author="Upstream Dev <up@example.com>",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        commit(repo, at(5, 10), "late readme update",
               author="Late Dev <late@example.com>", append={"a.py": "# r\n"})
        a = self._filtered(repo, "Late Dev").authorship
        self.assertEqual(a.history_commits, 10)
        self.assertAlmostEqual(a.author_share, 0.10)
        self.assertEqual(a.inherited_before, 9)
        self.assertFalse(a.mostly_inherited)  # under the 20-commit floor

    def test_late_pileup_does_not_flag(self):
        # The reviewed author was here first; the crowd arrived after.
        # Small share, but nothing predates them, so no flag.
        repo = os.path.join(self.tmp, "pileup")
        make_repo(repo)
        commit(repo, at(400, 10), "founding commit with real explanation",
               author="Founder Dev <founder@example.com>", files={"a.py": "x\n"})
        commit(repo, at(390, 10), "second founding commit with explanation",
               author="Founder Dev <founder@example.com>", append={"a.py": "# 2\n"})
        for i in range(28):
            commit(repo, at(60 - i, 10), f"crowd contribution number {i}",
                   author="Crowd Dev <crowd@example.com>",
                   append={"a.py": f"# c{i}\n"})
        a = self._filtered(repo, "Founder Dev").authorship
        self.assertEqual(a.history_commits, 30)
        self.assertAlmostEqual(a.author_share, 2 / 30)
        self.assertEqual(a.inherited_before, 0)
        self.assertFalse(a.mostly_inherited)

    def test_interleaved_minor_contributor_no_flag(self):
        repo = os.path.join(self.tmp, "interleaved")
        make_repo(repo)
        for i in range(10):
            commit(repo, at(100 - i, 10), f"early team work number {i}",
                   author="Team Dev <team@example.com>",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# t{i}\n"} if i > 0 else None)
        for i in range(20):
            who = ("Minor Dev <minor@example.com>" if i % 7 == 0
                   else "Team Dev <team@example.com>")
            commit(repo, at(89 - i, 10), f"shared project work number {i}",
                   author=who, append={"a.py": f"# s{i}\n"})
        a = self._filtered(repo, "Minor Dev").authorship
        self.assertEqual(a.author_commits, 3)
        self.assertEqual(a.inherited_before, 10)  # under half of 30
        self.assertFalse(a.mostly_inherited)

    def test_merge_commits_count_for_their_author(self):
        repo = os.path.join(self.tmp, "merges")
        make_repo(repo)
        for i in range(10):
            commit(repo, at(60 - i, 10), f"main line work number {i}",
                   author="Merge Dev <merge@example.com>",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# m{i}\n"} if i > 0 else None)
        _run(repo, "checkout", "-q", "-b", "feat")
        for i in range(3):
            commit(repo, at(50 - i, 11), f"branch work number {i}",
                   author="Other Dev <other@example.com>",
                   files={"b.py": "y\n"} if i == 0 else None,
                   append={"b.py": f"# b{i}\n"} if i > 0 else None)
        _run(repo, "checkout", "-q", "-")  # back to the default branch
        commit(repo, at(47, 10), "one more main line change",
               author="Merge Dev <merge@example.com>", append={"a.py": "# pre\n"})
        when = at(46, 10).isoformat()
        _run(repo, "merge", "-q", "--no-ff", "-m", "Merge branch feat", "feat",
             env_extra={"GIT_AUTHOR_NAME": "Merge Dev",
                        "GIT_AUTHOR_EMAIL": "merge@example.com",
                        "GIT_COMMITTER_NAME": "Merge Dev",
                        "GIT_COMMITTER_EMAIL": "merge@example.com",
                        "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when})
        commits = pip_pip.collect_commits(repo, 10000)
        self.assertTrue(any(c.parents >= 2 for c in commits))  # fixture has a merge
        a = review_of(repo).authorship
        self.assertEqual(a.history_commits, 15)
        self.assertEqual(a.author_commits, 12)  # 11 regular + the merge itself
        self.assertFalse(a.mostly_inherited)

    def test_coauthor_only_identity_reports_zero(self):
        repo = os.path.join(self.tmp, "coauthor")
        make_repo(repo)
        for i in range(5):
            commit(repo, at(50 - i * 5, 10), f"paired work number {i}",
                   body="Done together.\n\nCo-authored-by: Ghost Writer <ghost@example.com>",
                   author="Main Dev <main@example.com>",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# {i}\n"} if i > 0 else None)
        a = self._filtered(repo, "Ghost Writer").authorship
        self.assertEqual(a.history_commits, 5)
        self.assertEqual(a.author_commits, 0)
        self.assertIsNone(a.author_first)
        self.assertFalse(a.mostly_inherited)

    def test_bots_excluded_unless_review_includes_them(self):
        repo = os.path.join(self.tmp, "bots")
        make_repo(repo)
        for i in range(20):
            commit(repo, at(100 - i * 2, 10), f"human work number {i}",
                   author="Human Dev <human@example.com>",
                   files={"a.py": "x\n"} if i == 0 else None,
                   append={"a.py": f"# h{i}\n"} if i > 0 else None)
        for i in range(10):
            commit(repo, at(59 - i * 2, 10), f"dependency update number {i}",
                   author="dependabot[bot] <dependabot@example.com>",
                   append={"a.py": f"# d{i}\n"})
        a = review_of(repo).authorship
        self.assertEqual(a.history_commits, 20)
        self.assertEqual(a.author_share, 1.0)
        a2 = review_of(repo, include_bots=True).authorship
        self.assertEqual(a2.history_commits, 30)
        self.assertEqual(a2.other_authors, 1)
