#!/usr/bin/env python3
"""PIP - the Performance Improvement Plan for programmers.

Every AI tool reviews your code. PIP reviews *you*.

PIP reads a developer's own git history (locally, read-only, nothing is
uploaded anywhere) and issues a formal, manager-style performance review
with evidence: commit-message quality, late-night and Friday-afternoon
habits, reverts, fix chains, TODOs left to grow old, and "temporary" hacks
that quietly became permanent.

Pure Python standard library. No dependencies, no accounts, no network.

    pip install on-a-pip
    on-a-pip                  # review the top author of the repo in cwd
    on-a-pip ~/some/repo --md review.md --html card.html
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

__version__ = "1.1.1"

# --------------------------------------------------------------------------
# git collection (read-only)
# --------------------------------------------------------------------------

RS = "\x1e"  # record separator
FS = "\x1f"  # field separator


def _git(repo: str, args: list[str], check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", repo] + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if check and proc.returncode != 0:
        raise PipError(f"git {' '.join(args[:2])} failed: {proc.stderr.strip()[:200]}")
    return proc.stdout


class PipError(Exception):
    pass


_SHORTHAND_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def is_clone_target(arg: str) -> bool:
    """True when the positional argument names a remote repo, not a local path:
    a URL (https/git@/ssh/file) or a GitHub shorthand like 'psf/requests'
    that does not exist locally."""
    if arg.startswith(("https://", "http://", "git@", "ssh://", "git://", "file://")):
        return True
    if os.path.isdir(arg):
        return False
    return bool(_SHORTHAND_RE.match(arg)) and not arg.startswith(".")


def expand_clone_url(arg: str) -> str:
    if _SHORTHAND_RE.match(arg) and "://" not in arg and not arg.startswith(("git@", "file:")):
        return f"https://github.com/{arg.removesuffix('.git')}.git"
    return arg


def clone_label(url: str) -> str:
    name = url.rstrip("/").removesuffix(".git")
    # Normalize Windows separators so file://C:\path\repo labels as "repo".
    name = name.replace("\\", "/").split("/")[-1].split(":")[-1]
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name) or "repo"


def clone_repo(url: str, shallow: int | None = None) -> tuple[str, str]:
    """Clone into a fresh temp dir. Returns (repo_path, temp_root)."""
    root = tempfile.mkdtemp(prefix="on-a-pip-")
    dest = os.path.join(root, clone_label(url))
    cmd = ["git", "clone", "--quiet"]
    if shallow:
        cmd += ["--depth", str(shallow)]
    cmd += [url, dest]
    print(f"Cloning {url} ...", file=sys.stderr)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        shutil.rmtree(root, ignore_errors=True)
        raise PipError(
            "could not clone that repository. If it is private or does not exist, "
            "clone it yourself and pass the local folder instead.")
    return dest, root


@dataclass
class Commit:
    sha: str
    author: str
    email: str
    when: datetime          # author date, tz-aware (commit's own offset)
    subject: str
    body: str
    added: int = 0
    deleted: int = 0
    files: int = 0
    parents: int = 1
    paths: tuple = ()


@dataclass
class Marker:
    kind: str               # TODO / FIXME / HACK / TEMP ...
    path: str
    line: int
    text: str
    born: date | None       # date the line was introduced (blame), if known


def _parse_iso(text: str) -> datetime:
    """Parse git's %aI output on any supported Python. Modern git emits a
    'Z' suffix for UTC, which datetime.fromisoformat only accepts from
    Python 3.11; normalize it, and tolerate colon-less offsets too."""
    t = text.strip()
    if t.endswith(("Z", "z")):
        t = t[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(t)
    except ValueError:
        m = re.search(r"([+-]\d{2})(\d{2})$", t)
        if m:
            return datetime.fromisoformat(t[:m.start()] + f"{m.group(1)}:{m.group(2)}")
        raise


def collect_commits(repo: str, max_commits: int, branch: str | None = None,
                    path: str | None = None) -> list[Commit]:
    fmt = FS.join(["%H", "%P", "%aN", "%aE", "%aI", "%s", "%b"]) + RS
    args = ["log", "--use-mailmap", f"--max-count={max_commits}", f"--format={fmt}"]
    if branch:
        ok = _git(repo, ["rev-parse", "--verify", "--quiet", f"{branch}^{{commit}}"],
                  check=False).strip()
        if not ok:
            raise PipError(f"branch '{branch}' was not found in this repository")
        args.append(branch)
    if path:
        args += ["--", path]
    out = _git(repo, args)
    commits: list[Commit] = []
    for rec in out.split(RS):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        parts = rec.split(FS)
        if len(parts) < 7:
            continue
        sha, parents, author, email, iso, subject, body = (
            parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], FS.join(parts[6:]))
        try:
            when = _parse_iso(iso)
        except ValueError:
            continue
        commits.append(Commit(sha=sha, author=author, email=email, when=when,
                              subject=subject.strip(), body=body.strip(),
                              parents=len(parents.split()) if parents.strip() else 0))
    return commits


GENERATED_BASENAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml",
                       "Cargo.lock", "poetry.lock", "Pipfile.lock",
                       "composer.lock", "Gemfile.lock", "go.sum", "bun.lockb",
                       "flake.lock", "packages.lock.json"}
GENERATED_SUFFIXES = (".min.js", ".min.css")


def _is_generated(fname: str) -> bool:
    base = fname.rsplit("/", 1)[-1]
    return base in GENERATED_BASENAMES or base.endswith(GENERATED_SUFFIXES)


def collect_numstat(repo: str, shas: set[str], cap: int = 5000,
                    branch: str | None = None, path: str | None = None,
                    exclude_generated: bool = True):
    """Return (per-commit stats, per-file totals).

    Per-commit: sha -> (added, deleted, files).
    Per-file: path -> (added, deleted, commits_touched).
    Capped for very large histories.
    """
    log_args = ["log", f"--max-count={cap}", "--numstat", "--format=%H"]
    if branch:
        log_args.append(branch)
    if path:
        log_args += ["--", path]
    out = _git(repo, log_args)
    stats: dict[str, tuple[int, int, int]] = {}
    files: dict[str, tuple[int, int, int]] = {}
    paths: dict[str, list[str]] = {}
    current: str | None = None
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"[0-9a-f]{40}", line):
            current = line
            if current in shas:
                stats.setdefault(current, (0, 0, 0))
                paths.setdefault(current, [])
            continue
        if current is None or current not in shas:
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            fname = parts[2]
            if " => " in fname:
                fname = fname.split(" => ")[-1].strip("{}")
            if exclude_generated and _is_generated(fname):
                continue
            a, d = parts[0], parts[1]
            added = int(a) if a.isdigit() else 0
            deleted = int(d) if d.isdigit() else 0
            pa, pd, pf = stats[current]
            stats[current] = (pa + added, pd + deleted, pf + 1)
            paths[current].append(fname)
            fa, fd, fc = files.get(fname, (0, 0, 0))
            files[fname] = (fa + added, fd + deleted, fc + 1)
    return stats, files, paths


MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX|TEMPORARY|TEMP|WORKAROUND)\b[:\s]?(.*)", re.IGNORECASE)
TEMP_RE = re.compile(r"\b(temp|temporary|hack|workaround|for now|quick fix)\b", re.IGNORECASE)


def collect_markers(repo: str, cap: int = 300, blame_cap: int = 80) -> list[Marker]:
    out = _git(repo, ["grep", "-n", "-I", "-i", "-E",
                      r"TODO|FIXME|HACK|XXX|TEMPORARY|WORKAROUND",
                      "--", "."], check=False)
    markers: list[Marker] = []
    for line in out.splitlines():
        # path:line:content
        m = re.match(r"(.+?):(\d+):(.*)$", line)
        if not m:
            continue
        path, lno, content = m.group(1), int(m.group(2)), m.group(3).strip()
        km = MARKER_RE.search(content)
        if not km:
            continue
        kind = km.group(1).upper()
        if kind in ("TEMP",):
            kind = "TEMPORARY"
        markers.append(Marker(kind=kind, path=path, line=lno,
                              text=content[:140], born=None))
        if len(markers) >= cap:
            break
    # Age the oldest-looking markers first: blame a bounded sample.
    for mk in markers[:blame_cap]:
        bout = _git(repo, ["blame", "-L", f"{mk.line},{mk.line}", "--porcelain",
                           "--", mk.path], check=False)
        dm = re.search(r"^author-time (\d+)$", bout, re.MULTILINE)
        if dm:
            mk.born = datetime.fromtimestamp(int(dm.group(1)), tz=timezone.utc).date()
    return markers


# --------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------

VAGUE_WORDS = {
    "stuff", "wip", "fix", "fixes", "fixed", "fixing", "misc", "changes",
    "change", "update", "updates", "updated", "asdf", "tmp", "temp", "test",
    "testing", "work", "working", "more", "minor", "small", "quick", "oops",
    "ugh", "idk", "whatever", "things", "code", "commit", "save", "checkpoint",
    "progress", "done", "final", "finalfix", "realfix", "actualfix", "ok",
    "yes", "no", "a", "aa", "aaa", ".", "..", "...", "lol", "pls", "please",
}
FIX_RE = re.compile(r"^(fix|fixes|fixed|fixup|hotfix|bugfix)\b", re.IGNORECASE)
REVERT_RE = re.compile(r"^revert\b", re.IGNORECASE)
WIP_RE = re.compile(r"\bwip\b|work in progress", re.IGNORECASE)


def _is_vague(subject: str) -> bool:
    s = subject.strip().lower()
    if len(s) < 8:
        return True
    words = re.findall(r"[a-z0-9]+", s)
    if not words:
        return True
    meaningful = [w for w in words if w not in VAGUE_WORDS]
    return len(meaningful) == 0 or (len(words) <= 2 and len(meaningful) <= 1 and len(s) < 16)


def grade_letter(score: float) -> str:
    if score >= 88:
        return "A"
    if score >= 74:
        return "B"
    if score >= 58:
        return "C"
    if score >= 42:
        return "D"
    return "F"


@dataclass
class Category:
    name: str
    score: float
    evidence: list[str] = field(default_factory=list)
    praise: str = ""
    concern: str = ""

    @property
    def letter(self) -> str:
        return grade_letter(self.score)


@dataclass
class Review:
    repo_name: str
    author: str
    review_date: date
    span_start: date
    span_end: date
    total_commits: int
    categories: list[Category]
    highlights: dict[str, object]
    awards: list[tuple[str, str]] = field(default_factory=list)
    persona: str = "corporate"

    @property
    def overall_score(self) -> float:
        return sum(c.score for c in self.categories) / max(1, len(self.categories))

    @property
    def overall_letter(self) -> str:
        return grade_letter(self.overall_score)


VERDICTS = {
    "A": "Exceeds expectations. Management is as surprised as you are.",
    "B": "Meets and often exceeds expectations. Keep doing most of this.",
    "C": "Meets some expectations. There is a conversation to be had.",
    "D": "Partially meets expectations. This plan exists for a reason.",
    "F": "Does not yet meet expectations. The plan below is not optional.",
}

PERSONAS: dict[str, dict[str, object]] = {
    "corporate": {
        "label": "Corporate",
        "verdicts": VERDICTS,
        "plan_intro": "The following actions address the lowest-scoring areas. "
                      "Progress will be assessed by re-running this review, which is to say, "
                      "by the record itself.",
        "signoff": "By continuing to commit, the employee acknowledges receipt of this plan. "
                   "Appeals may be filed by improving the record.",
    },
    "brutal": {
        "label": "Startup CTO",
        "verdicts": {
            "A": "Fine. Genuinely fine. Do not let it go to your head.",
            "B": "Good. Not great. You know the difference, which is the good part.",
            "C": "This is the part where a nicer manager would lie to you.",
            "D": "I have seen interns. I have seen scripts. I have seen this before, from both.",
            "F": "We are not doing a feelings meeting. We are doing this plan.",
        },
        "plan_intro": "No workshops. No journaling. Fix these, in this order, starting today.",
        "signoff": "Acknowledged or not, the record keeps receipts. So do I.",
    },
    "supportive": {
        "label": "Supportive Lead",
        "verdicts": {
            "A": "Wonderful work. Truly. Let us make sure everyone sees it.",
            "B": "Strong, steady work with real bright spots. Proud of this trajectory.",
            "C": "There is a good developer in this record, and some habits worth untangling together.",
            "D": "A rough stretch is not a verdict on you. It is a map of where support goes first.",
            "F": "We start where we are, and where we are is: lots of room, and a plan that fits in 30 days.",
        },
        "plan_intro": "Small, kind, concrete steps, aimed at the areas with the most room to grow. "
                      "None of this requires becoming a different person.",
        "signoff": "Thank you for the work in this record, including the messy parts. Especially those.",
    },
    "passive": {
        "label": "Passive-Aggressive Middle Manager",
        "verdicts": {
            "A": "Great. So we CAN do it. Interesting. Noted for the other 51 weeks.",
            "B": "Lovely. Mostly. We will circle back on the rest, per my last several reviews.",
            "C": "Per my last email, and the one before that, and the one before that.",
            "D": "No rush. It is only the roadmap. And the release. And the team blocked on you.",
            "F": "Wow. Okay. Lots to discuss. I have cleared my calendar. And yours.",
        },
        "plan_intro": "Just a few tiny suggestions. Again. For the third time. With feeling.",
        "signoff": "No need to reply. Your commit history already did.",
    },
    "pirate": {
        "label": "Pirate Captain",
        "verdicts": {
            "A": "A legend's logbook. The crew tells stories about these commits in port.",
            "B": "Fine sailing. The charts be readable and the ship mostly dry.",
            "C": "Ye be takin' on water in places, but the hull holds. Bail and mend.",
            "D": "This logbook reads like a mutiny written in shorthand. We be talkin'.",
            "F": "Even the parrot stopped repeatin' yer commit messages. To the plank of improvement with ye.",
        },
        "plan_intro": "Here be the chart to better waters. Follow it fer thirty days, or feed the fishes yer excuses.",
        "signoff": "Signed in rum and salt water. The sea keeps the record, and so do I.",
    },
    "noir": {
        "label": "Noir Detective",
        "verdicts": {
            "A": "The record was clean. Too clean, I almost said. Then I read it twice. It held up.",
            "B": "A solid record in a city of flimsy ones. A few smudges on the glass, nothing more.",
            "C": "The commits told a story. Half of it was missing, and the other half was in a hurry.",
            "D": "I've seen this file before. Different name, same 2am timestamps, same one-word confessions.",
            "F": "The record didn't just have gaps. It had alibis, and none of them checked out.",
        },
        "plan_intro": "Thirty days. Four leads worth following. Work them in order and don't skip the boring ones; the boring ones are where the truth hides.",
        "signoff": "Case stays open until the record improves. It always improves, or it always closes. Your move.",
    },
}


def fetch_org_repos(user: str, limit: int = 10, include_forks: bool = False,
                    _opener=None) -> list[tuple[str, str]]:
    """Public repos for a GitHub user/org via the API: (name, clone_url),
    most recently pushed first, forks and archived repos skipped by default."""
    import urllib.error
    import urllib.request
    url = f"https://api.github.com/users/{user}/repos?per_page=100&sort=pushed&type=owner"
    req = urllib.request.Request(url, headers={"User-Agent": "on-a-pip",
                                                "Accept": "application/vnd.github+json"})
    opener = _opener or urllib.request.urlopen
    try:
        with opener(req) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise PipError(f"GitHub user '{user}' was not found")
        if e.code == 403:
            raise PipError("the GitHub API rate limit was reached. The org will still be there later.")
        raise PipError(f"the GitHub API returned {e.code} for user '{user}'")
    except (urllib.error.URLError, ValueError) as e:
        raise PipError(f"could not reach the GitHub API: {e}")
    repos: list[tuple[str, str]] = []
    for r in data if isinstance(data, list) else []:
        if r.get("fork") and not include_forks:
            continue
        if r.get("archived"):
            continue
        repos.append((str(r["name"]), str(r["clone_url"])))
        if len(repos) >= limit:
            break
    return repos


def _clone(url: str, dest: str) -> None:
    r = subprocess.run(["git", "clone", "--quiet", url, dest],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise PipError(f"clone failed for {url}")


def render_org(rows: list[tuple[str, Review]], user: str) -> str:
    lines = ["", f"  PIP ORG BOARD  -  github.com/{user}  ({len(rows)} repositories)",
             "  " + "-" * 62,
             f"  {'#':<3} {'Repository':<22} {'Top author':<22} {'Grade':<6} {'Score':<7} Commits"]
    for i, (name, r) in enumerate(rows, 1):
        lines.append(f"  {i:<3} {name[:21]:<22} {r.author[:21]:<22} {r.overall_letter:<6} "
                     f"{r.overall_score:<7.1f} {r.total_commits}")
    lines.append("  " + "-" * 62)
    mvp = rows[0][1]
    prolific = max(rows, key=lambda kv: kv[1].total_commits)[1]
    lines.append(f"  Org MVP: {mvp.author} ({mvp.overall_letter}, {mvp.overall_score:.0f}/100). "
                 f"Most prolific: {prolific.author} ({prolific.total_commits} commits on their top repo).")
    lines.append("")
    return "\n".join(lines)


def _run_org(args) -> int:
    persona = args.persona or "corporate"
    try:
        repos = fetch_org_repos(args.org, limit=args.org_limit,
                                include_forks=args.include_forks)
    except PipError as e:
        print(f"on-a-pip: {e}", file=sys.stderr)
        return 2
    if not repos:
        print(f"on-a-pip: no public repositories found for '{args.org}'", file=sys.stderr)
        return 2
    rows: list[tuple[str, Review]] = []
    tmp_root = tempfile.mkdtemp(prefix="on-a-pip-org-")
    try:
        for name, url in repos:
            dest = os.path.join(tmp_root, name)
            try:
                _clone(url, dest)
                commits = collect_commits(dest, args.max_commits)
                if not commits:
                    continue
                stats, file_totals, paths_by_sha = collect_numstat(
                    dest, {c.sha for c in commits})
                for c in commits:
                    if c.sha in stats:
                        c.added, c.deleted, c.files = stats[c.sha]
                    c.paths = tuple(paths_by_sha.get(c.sha, ()))
                markers = collect_markers(dest)
                review = analyze(dest, commits, markers, None, date.today(),
                                 file_totals=file_totals, persona=persona)
                rows.append((name, review))
            except PipError:
                continue
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    if not rows:
        print(f"on-a-pip: none of {args.org}'s repositories could be reviewed", file=sys.stderr)
        return 2
    rows.sort(key=lambda kv: -kv[1].overall_score)
    if args.json:
        print(json.dumps({"org": args.org,
                          "repos": [{"repo": name, **review_to_json(r)} for name, r in rows]},
                         indent=2, default=str))
    elif args.csv:
        print(boards_to_csv(rows, with_repo=True), end="")
    else:
        print(render_org(rows, args.org))
    return 0


def load_persona_file(path: str) -> str:
    """Load a custom persona pack (JSON) and register it in PERSONAS.

    Format: {"name": "pirate", "label": "Pirate Captain",
             "verdicts": {"A": "...", ...}, "plan_intro": "...", "signoff": "..."}
    Only "name" is required; anything missing falls back to Corporate wording.
    Returns the persona key to use."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError:
        raise PipError(f"persona file not found: {path}")
    except ValueError:
        raise PipError(f"persona file is not valid JSON: {path}")
    if not isinstance(data, dict) or not data.get("name"):
        raise PipError("persona file needs at least a \"name\" field")
    key = re.sub(r"[^a-z0-9-]+", "-", str(data["name"]).lower()).strip("-") or "custom"
    verdicts = dict(VERDICTS)
    provided = data.get("verdicts")
    if isinstance(provided, dict):
        for grade in ("A", "B", "C", "D", "F"):
            if isinstance(provided.get(grade), str) and provided[grade].strip():
                verdicts[grade] = provided[grade]
    base = PERSONAS["corporate"]
    PERSONAS[key] = {
        "label": str(data.get("label") or data["name"]),
        "verdicts": verdicts,
        "plan_intro": str(data.get("plan_intro") or base["plan_intro"]),
        "signoff": str(data.get("signoff") or base["signoff"]),
    }
    return key


def verdict_for(review: "Review") -> str:
    persona = PERSONAS.get(review.persona, PERSONAS["corporate"])
    return persona["verdicts"][review.overall_letter]  # type: ignore[index]


SWEAR_RE = re.compile(r"\b(damn|hell|shit|fuck|fucking|crap|wtf|bullshit)\b", re.IGNORECASE)


def scope_commits(commits: list[Commit], days: int | None) -> list[Commit]:
    """Keep only commits within `days` of the most recent commit (the anchor),
    so old repositories can be reviewed for a recent period."""
    if not days or not commits:
        return commits
    anchor = max(c.when for c in commits)
    cutoff = anchor - timedelta(days=days)
    return [c for c in commits if c.when >= cutoff]


def analyze(repo: str, commits_in: list[Commit], markers: list[Marker],
            author_filter: str | None, today: date,
            file_totals: dict[str, tuple[int, int, int]] | None = None,
            persona: str = "corporate", include_bots: bool = False,
            tz=None, author_key: str | None = None) -> Review:
    # Pick the employee: explicit filter, else the most prolific identity.
    # Identities group by email: one person under two names is one employee.
    if tz is not None:
        from dataclasses import replace as _replace
        commits_in = [_replace(c, when=c.when.astimezone(tz)) for c in commits_in]
    groups = _author_groups(commits_in, include_bots=include_bots)
    if author_key is not None:
        exact = [(a, cs) for a, cs, k in groups if k == author_key]
        if not exact:
            raise PipError("that author identity is no longer in the record")
        author, commits = exact[0]
    elif author_filter:
        f = author_filter.lower()
        matches = [(a, cs) for a, cs, _k in groups
                   if f in a.lower() or any(f in (c.email or "").lower() for c in cs)]
        if not matches:
            raise PipError(f"no commits found for author matching '{author_filter}'")
        author, commits = max(matches, key=lambda kv: len(kv[1]))
    else:
        author, commits, _k = max(groups, key=lambda kv: len(kv[1]))
    commits = sorted(commits, key=lambda c: c.when)
    total = len(commits)
    if total == 0:
        raise PipError("no commits to review")

    subjects = [c.subject for c in commits]
    vague = [s for s in subjects if _is_vague(s)]
    with_body = sum(1 for c in commits if len(c.body) >= 3)
    avg_len = sum(len(s) for s in subjects) / total
    night = [c for c in commits if c.when.hour >= 22 or c.when.hour < 5]
    friday_late = [c for c in commits if c.when.weekday() == 4 and c.when.hour >= 16]
    reverts = [c for c in commits if REVERT_RE.match(c.subject)]
    fixes = [c for c in commits if FIX_RE.match(c.subject)]
    wips = [c for c in commits if WIP_RE.search(c.subject)]
    active_days = sorted({c.when.date() for c in commits})
    span_days = max(1, (active_days[-1] - active_days[0]).days + 1)
    # longest streak / gap
    streak = longest = 1
    gap = longest_gap = 0
    for prev, cur in zip(active_days, active_days[1:]):
        d = (cur - prev).days
        if d == 1:
            streak += 1
        else:
            longest = max(longest, streak)
            streak = 1
            gap = d - 1
            longest_gap = max(longest_gap, gap)
    longest = max(longest, streak)

    # --- Communication -------------------------------------------------
    vague_ratio = len(vague) / total
    body_ratio = with_body / total
    comm_score = 100 - vague_ratio * 110 - (18 if avg_len < 14 else 0) + body_ratio * 10
    comm = Category("Communication", max(0.0, min(100.0, comm_score)))
    comm.evidence.append(
        f"{len(vague)} of {total} commit messages ({vague_ratio:.0%}) say almost nothing "
        f"(average message length: {avg_len:.0f} characters).")
    if vague:
        examples = ", ".join(f'"{v}"' for v in vague[:3])
        comm.evidence.append(f"Entered into the record: {examples}.")
    comm.evidence.append(f"{with_body} of {total} commits ({body_ratio:.0%}) include any explanation beyond the subject line.")
    comm.concern = "Commit messages are the only explanation future maintainers get."
    comm.praise = "When you write a real message, it tends to be a genuinely useful one."

    # --- Reliability ----------------------------------------------------
    night_ratio = len(night) / total
    revert_ratio = len(reverts) / total
    fix_ratio = len(fixes) / total
    rel_score = 100 - night_ratio * 45 - revert_ratio * 160 - fix_ratio * 35
    rel = Category("Reliability", max(0.0, min(100.0, rel_score)))
    rel.evidence.append(
        f"{len(night)} of {total} commits ({night_ratio:.0%}) were made between 10pm and 5am.")
    rel.evidence.append(
        f"{len(friday_late)} commits landed on a Friday at or after 4pm, the industry's most dangerous hour.")
    rel.evidence.append(
        f"{len(reverts)} commits are reverts ({revert_ratio:.0%}) and {len(fixes)} ({fix_ratio:.0%}) begin with the word 'fix'.")
    rel.concern = "Work shipped tired, or shipped twice, costs the team twice."
    rel.praise = "A low revert habit, where present, is the mark of someone who checks before they ship."

    # --- Follow-through ---------------------------------------------------
    todos = [m for m in markers if m.kind in ("TODO", "FIXME", "XXX")]
    aged = [m for m in todos if m.born is not None]
    oldest_todo_days = max(((today - m.born).days for m in aged), default=None)
    ft_score = 100 - min(45, len(todos) * 2.5)
    if oldest_todo_days is not None:
        ft_score -= min(35, oldest_todo_days / 365 * 12)
    ft = Category("Follow-through", max(0.0, min(100.0, ft_score)))
    ft.evidence.append(f"{len(todos)} TODO/FIXME notes are still open in the current code.")
    if oldest_todo_days is not None:
        yrs = oldest_todo_days / 365
        ft.evidence.append(
            f"The oldest surviving TODO has been waiting {oldest_todo_days} days ({yrs:.1f} years). It has seniority now.")
        oldest_mk = max(aged, key=lambda m: (today - m.born).days)
        ft.evidence.append(f"Senior TODO on file: {oldest_mk.path}:{oldest_mk.line} - \"{oldest_mk.text[:90]}\"")
    ft.concern = "A TODO is a promise. Old TODOs are promises in default."
    ft.praise = "Every TODO you do close is one the next person never has to meet."

    # --- Judgment ---------------------------------------------------------
    temps = [m for m in markers if m.kind in ("HACK", "TEMPORARY") or TEMP_RE.search(m.text)]
    aged_temps = [m for m in temps if m.born is not None]
    oldest_temp_days = max(((today - m.born).days for m in aged_temps), default=None)
    jud_score = 92 - min(40, len(temps) * 4) - len(wips) * 1.5
    if oldest_temp_days is not None:
        jud_score -= min(30, oldest_temp_days / 365 * 10)
    jud = Category("Judgment", max(0.0, min(100.0, jud_score)))
    jud.evidence.append(f"{len(temps)} spots in the code are labelled temporary, a hack, or a workaround.")
    if oldest_temp_days is not None:
        jud.evidence.append(
            f"The oldest 'temporary' measure has been in production {oldest_temp_days} days. It is not temporary. It is load-bearing.")
    jud.evidence.append(f"{len(wips)} commits were checked in openly marked as work in progress.")
    jud.concern = "Temporary is the most permanent word in software."
    jud.praise = "Labelling a hack as a hack is honesty many developers skip entirely."

    # --- Consistency --------------------------------------------------------
    activity_ratio = len(active_days) / span_days
    con_score = 45 + activity_ratio * 65 - min(25, longest_gap / 30)
    con = Category("Consistency", max(0.0, min(100.0, con_score)))
    con.evidence.append(
        f"Active on {len(active_days)} of {span_days} days in the review period ({activity_ratio:.0%}).")
    con.evidence.append(f"Longest streak: {longest} days. Longest disappearance: {longest_gap} days.")
    con.evidence.append(f"Average output on an active day: {total / max(1, len(active_days)):.1f} commits.")
    con.concern = "Bursts followed by silence are harder on a project than a steady pace."
    con.praise = "Showing up regularly is most of the job, and it is the part nobody can automate."

    # --- extra colour: weekends, merges, language, nemesis, biggest day ---
    weekend = [c for c in commits if c.when.weekday() >= 5]
    merges = [c for c in commits if c.subject.startswith("Merge ")]
    swears = [c for c in commits if SWEAR_RE.search(c.subject) or SWEAR_RE.search(c.body)]
    sorries = [c for c in commits if "sorry" in (c.subject + " " + c.body).lower()]
    total_added = sum(c.added for c in commits)
    total_deleted = sum(c.deleted for c in commits)
    biggest = max(commits, key=lambda c: c.added + c.deleted) if commits else None
    nemesis = None
    nemesis_churn = 0
    if file_totals:
        author_files = file_totals  # totals are repo-wide; the reviewed author dominates them in practice
        if author_files:
            nemesis, (na, nd, _nc) = max(author_files.items(), key=lambda kv: kv[1][0] + kv[1][1])
            nemesis_churn = na + nd

    # --- career stats -----------------------------------------------------
    from collections import Counter
    day_counts = Counter(c.when.date() for c in commits)
    busiest_day, busiest_count = (None, 0)
    if day_counts:
        busiest_day, busiest_count = max(day_counts.items(), key=lambda kv: kv[1])
    month_counts = Counter(c.when.strftime("%Y-%m") for c in commits)
    months_sorted = sorted(month_counts.items())
    # --- hall of fame: the novel, the haiku, the catchphrase --------------
    longest_subject = max(subjects, key=len) if subjects else ""
    shortest_subject = min(subjects, key=len) if subjects else ""
    STOPWORDS = {"with", "from", "this", "that", "when", "into", "over",
                 "after", "before", "will", "adds", "added", "using", "used"}
    word_counts = Counter(w for w in re.findall(r"[a-z]{4,}", " ".join(subjects).lower())
                          if w not in STOPWORDS)
    top_word, top_word_count = ("", 0)
    if word_counts:
        top_word, top_word_count = word_counts.most_common(1)[0]
    LANG_NAMES = {"py": "Python", "js": "JavaScript", "ts": "TypeScript", "tsx": "TypeScript",
                  "jsx": "JavaScript", "rs": "Rust", "go": "Go", "java": "Java", "c": "C",
                  "h": "C", "cpp": "C++", "rb": "Ruby", "php": "PHP", "html": "HTML",
                  "css": "CSS", "sh": "Shell", "md": "Markdown", "swift": "Swift",
                  "kt": "Kotlin", "lua": "Lua", "sql": "SQL", "yml": "YAML", "yaml": "YAML"}
    lang_churn: dict[str, int] = {}
    if file_totals:
        for path, (fa, fd, _fc) in file_totals.items():
            base = path.rsplit("/", 1)[-1]
            if "." not in base:
                continue
            ext = base.rsplit(".", 1)[-1].lower()
            name = LANG_NAMES.get(ext, ext)
            lang_churn[name] = lang_churn.get(name, 0) + fa + fd
    languages = sorted(lang_churn.items(), key=lambda kv: -kv[1])
    max_deleted_single = max((c.deleted for c in commits), default=0)
    # Phoenix: a 90+ day silence followed by 10+ commits within 30 days.
    phoenix = False
    for prev, cur in zip(active_days, active_days[1:]):
        if (cur - prev).days >= 90:
            comeback = [c for c in commits if cur <= c.when.date() <= cur + timedelta(days=30)]
            if len(comeback) >= 10:
                phoenix = True
                break

    highlights: dict[str, object] = {
        "night_commits": len(night), "friday_late": len(friday_late),
        "reverts": len(reverts), "fixes": len(fixes), "vague": len(vague),
        "todos": len(todos), "oldest_todo_days": oldest_todo_days,
        "temps": len(temps), "oldest_temp_days": oldest_temp_days,
        "active_days": len(active_days), "span_days": span_days,
        "longest_streak": longest, "longest_gap": longest_gap,
        "added": total_added, "deleted": total_deleted,
        "weekend_commits": len(weekend), "merges": len(merges),
        "swears": len(swears), "sorries": len(sorries),
        "nemesis_file": nemesis, "nemesis_churn": nemesis_churn,
        "biggest_commit_lines": (biggest.added + biggest.deleted) if biggest else 0,
        "biggest_commit_subject": biggest.subject if biggest else "",
        "busiest_day": busiest_day.isoformat() if busiest_day else None,
        "busiest_day_count": busiest_count,
        "months": [[m, n] for m, n in months_sorted],
        "languages": [[name, churn] for name, churn in languages[:6]],
        "max_deleted_single": max_deleted_single,
        "longest_subject": longest_subject,
        "shortest_subject": shortest_subject,
        "top_word": top_word, "top_word_count": top_word_count,
        "squash_ratio": (sum(1 for s in subjects if re.search(r"\(#\d+\)\s*$", s)) / total) if total else 0.0,
    }

    # --- awards: the part people actually post --------------------------
    awards: list[tuple[str, str]] = []
    if total >= 10 and night_ratio >= 0.25:
        awards.append(("Night Owl", f"{night_ratio:.0%} of all commits landed between 10pm and 5am. The codebase's second shift."))
    if len(friday_late) >= 3:
        awards.append(("Friday Gambler", f"{len(friday_late)} commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it."))
    if total_deleted > total_added and total_deleted >= 500:
        awards.append(("Demolitionist", f"Deleted {total_deleted:,} lines against {total_added:,} added. The bravest key on the keyboard is Delete."))
    if total >= 20 and sum(c.files for c in commits) / total <= 1.5:
        awards.append(("Surgeon", "Small, precise commits, one concern at a time. Future archaeologists send their thanks."))
    if longest_gap >= 60:
        awards.append(("The Ghost", f"Vanished for {longest_gap} days once, then returned as if nothing happened. It had, in fact, happened."))
    if longest >= 7:
        awards.append(("Streak Keeper", f"{longest} active days in a row at the longest stretch. Showing up is a skill."))
    if body_ratio >= 0.5 and total >= 10:
        awards.append(("Open Book", f"{body_ratio:.0%} of commits carry a real explanation. Reviewers wept, briefly, with joy."))
    if avg_len < 12 and total >= 10:
        awards.append(("Strong Silent Type", f"Average commit message: {avg_len:.0f} characters. The code speaks. Nobody knows what it said."))
    if revert_ratio >= 0.05 and total >= 10:
        awards.append(("Chaos Agent", f"{revert_ratio:.0%} of commits undo earlier commits. A one-person arms race."))
    if oldest_todo_days is not None and oldest_todo_days >= 365:
        awards.append(("Fossil Keeper", f"A TODO has survived {oldest_todo_days} days in the code. It qualifies for the pension plan."))
    if len(swears) >= 3:
        awards.append(("Colourful Commentator", f"{len(swears)} commit messages contain profanity. Honest, if not exactly handbook language."))
    if len(weekend) / total >= 0.3 and total >= 10:
        awards.append(("Weekend Warrior", f"{len(weekend) / total:.0%} of commits landed on a Saturday or Sunday. The roadmap thanks you. The weekend does not."))
    if busiest_count >= 15:
        awards.append(("Marathon Day", f"{busiest_count} commits in a single day ({busiest_day}). Somewhere in there was a lunch break. Probably."))
    if max_deleted_single >= 1000:
        awards.append(("The Purge", f"One commit deleted {max_deleted_single:,} lines. Witnesses described the diff as 'mostly red'."))
    if len([1 for _n, ch in languages if ch >= 20]) >= 5:
        awards.append(("Polyglot", f"Meaningful churn in {len(languages)} languages. Jack of all trades, suspect in all of them."))
    if span_days >= 1095:
        awards.append(("Old Faithful", f"Commits spanning {span_days // 365} years on the same codebase. It has outlived three roadmaps and a rebrand."))
    if phoenix:
        awards.append(("Phoenix", "Vanished for a season, then came back swinging. The comeback commits outnumber the goodbye ones, because there were no goodbye ones."))
    # --- award wave 2 (v0.8) ---------------------------------------------
    merge_commits = [c for c in commits if c.parents >= 2 or c.subject.startswith("Merge ")]
    if total >= 8 and len(merge_commits) / total >= 0.25:
        awards.append(("Merge Goblin", f"{len(merge_commits)} of {total} commits are merges. Somewhere upstream, a rebase weeps quietly."))
    if len(groups) == 1 and total >= 20:
        awards.append(("Lone Wolf", f"Every one of the {total} commits is theirs. The team is a person. The person is the team."))
    avg_body = sum(len(c.body) for c in commits) / total if total else 0
    if total >= 5 and avg_body >= 200:
        awards.append(("Rubber Duck", f"Commit bodies average {avg_body:.0f} characters. The reasoning is all there. All of it. Every thought."))
    timelines: dict[str, list[datetime]] = {}
    for c in commits_in:
        for p in c.paths:
            timelines.setdefault(p, []).append(c.when)
    for v in timelines.values():
        v.sort()
    revived = 0
    for c in commits:
        for p in c.paths:
            dates = timelines.get(p, [])
            earlier = [d for d in dates if d < c.when]
            if earlier and (c.when - max(earlier)).days >= 365:
                revived += 1
                break
    if revived >= 1:
        awards.append(("The Archaeologist", f"Revived {revived} commit(s) touching files untouched for over a year. Brushed off the dust, read the ancient comments, understood nothing, proceeded anyway."))

    return Review(
        repo_name=os.path.basename(os.path.abspath(repo)) or repo,
        author=author, review_date=today,
        span_start=active_days[0], span_end=active_days[-1],
        total_commits=total,
        categories=[comm, rel, ft, jud, con],
        highlights=highlights,
        awards=awards,
        persona=persona,
    )


BOT_RE = re.compile(
    r"(\[bot\]|[-_]bot\b|dependabot|renovate\[?\]?|github-actions|pre-commit-ci|codecov|"
    r"bors\[?\]?|mergify|semantic-release|release-please|imgbot|allcontributors|"
    r"deepsource|sonarcloud|snyk)", re.IGNORECASE)
COAUTHOR_RE = re.compile(r"^Co-authored-by:\s*(.+?)\s*<([^>]+)>",
                         re.IGNORECASE | re.MULTILINE)


def _is_bot(name: str, email: str) -> bool:
    return bool(BOT_RE.search(name or "") or BOT_RE.search(email or ""))


def _author_groups(commits_in: list[Commit], include_bots: bool = False) -> list[tuple[str, list[Commit], str]]:
    """Group commits by identity: same email is the same person, whatever
    name they committed under. Co-authored-by trailers earn the co-author
    shared credit for the commit. Bot identities are excluded unless
    include_bots is set. Returns (display name, commits, identity key)
    where the key is the email when there is one, else the name."""
    groups: dict[str, list[Commit]] = {}
    names_by_key: dict[str, dict[str, int]] = {}

    def credit(key: str, display: str, c: Commit) -> None:
        groups.setdefault(key, []).append(c)
        names = names_by_key.setdefault(key, {})
        names[display] = names.get(display, 0) + 1

    for c in commits_in:
        key = (c.email or "").strip().lower() or f"name:{c.author.strip().lower()}"
        credit(key, c.author, c)
        for m in COAUTHOR_RE.finditer(c.body or ""):
            ca_key = m.group(2).strip().lower()
            if ca_key and ca_key != key:
                credit(ca_key, m.group(1).strip(), c)
    result: list[tuple[str, list[Commit], str]] = []
    for key, cs in groups.items():
        display = max(names_by_key[key].items(), key=lambda kv: kv[1])[0]
        if not include_bots and _is_bot(display, key):
            continue
        result.append((display, cs, key))
    return result


def leaderboard(repo: str, commits_in: list[Commit], markers: list[Marker],
                today: date, file_totals=None, persona: str = "corporate",
                min_commits: int = 5, top: int = 8,
                include_bots: bool = False, tz=None) -> list[Review]:
    """Review every author in the repo and rank them. The office feature."""
    ranked = sorted(((name, len(cs), key) for name, cs, key in
                     _author_groups(commits_in, include_bots=include_bots)),
                    key=lambda kv: -kv[1])
    reviews: list[Review] = []
    for name, count, key in ranked[:top]:
        if count < min_commits:
            continue
        # Target the exact identity by its group key, so two identities who
        # share a display name (one email-keyed, one name-keyed) never
        # collapse into duplicate rows.
        try:
            reviews.append(analyze(repo, commits_in, markers, None, today,
                                   file_totals=file_totals, persona=persona,
                                   include_bots=include_bots, tz=tz,
                                   author_key=key))
        except PipError:
            continue
    return sorted(reviews, key=lambda r: -r.overall_score)


# --------------------------------------------------------------------------
# the improvement plan (generated from the weakest categories)
# --------------------------------------------------------------------------

PLAN_ACTIONS: dict[str, list[str]] = {
    "Communication": [
        "Every commit message must complete the sentence: 'This change will...' If it cannot, the commit is not ready.",
        "The words 'stuff', 'wip', 'misc' and 'fix fix fix' are retired, effective immediately.",
        "Commits touching more than one file get a body. Two lines minimum. Future you is the audience.",
    ],
    "Reliability": [
        "No merges after 10pm without sleeping on it first. The code will keep. The bug you are about to write will too.",
        "Friday after 4pm is for reading code, not shipping it.",
        "Before any commit whose message starts with 'fix', write down what the first attempt missed.",
    ],
    "Follow-through": [
        "Pick the five oldest TODOs. Close them, convert them to tracked issues, or delete them and own the decision.",
        "New rule: a TODO without a date and a name is litter. Date and name, every time.",
        "One TODO closed per week, minimum, until the backlog is younger than you are.",
    ],
    "Judgment": [
        "Every 'temporary' fix gets an expiry date in the comment. When the date passes, it gets reviewed first, not last.",
        "Count the hacks monthly. The number going down is the goal; the number existing is not the shame.",
        "No new workaround merges without a note explaining what the real fix would take.",
    ],
    "Consistency": [
        "Small and daily beats heroic and monthly. Protect the streak, shorten the silences.",
        "End each session by leaving the next step written down, so returning is easy.",
        "If a gap is coming (holiday, life), say so in a commit. Silence reads worse than absence.",
    ],
}


def build_plan(review: Review) -> list[tuple[str, list[str]]]:
    weakest = sorted(review.categories, key=lambda c: c.score)[:3]
    return [(c.name, PLAN_ACTIONS[c.name]) for c in weakest]


# --------------------------------------------------------------------------
# renderers
# --------------------------------------------------------------------------

def render_terminal(review: Review, previous: dict | None = None) -> str:
    lines = []
    lines.append("")
    lines.append(f"  PERFORMANCE IMPROVEMENT PLAN  -  {review.author}")
    lines.append(f"  {review.repo_name}  |  {review.total_commits} commits reviewed  |  {review.span_start} to {review.span_end}")
    lines.append("  " + "-" * 62)
    for c in review.categories:
        bar = "#" * int(c.score / 5)
        lines.append(f"  {c.name:<16} {c.letter}   {c.score:5.1f}  {bar}")
    lines.append("  " + "-" * 62)
    lines.append(f"  OVERALL          {review.overall_letter}   {review.overall_score:5.1f}")
    lines.append(f"  {verdict_for(review)}")
    if previous and previous.get("overall_score") is not None:
        delta = review.overall_score - float(previous["overall_score"])
        if abs(delta) < 0.05:
            delta = 0.0
        when = previous.get("date", "previously")
        arrow = "up" if delta > 0.05 else ("down" if delta < -0.05 else "flat")
        lines.append(f"  Since your last review ({when}): {delta:+.1f} points, {arrow}. "
                     + ("The plan is working." if delta > 0.05 else
                        "The plan has notes." if delta < -0.05 else "Perfectly, suspiciously stable."))
    if review.awards:
        lines.append("")
        lines.append("  AWARDS")
        for title, reason in review.awards:
            lines.append(f"  * {title} - {reason}")
    months = review.highlights.get("months") or []
    if months:
        counts = [n for _m, n in months][-24:]
        blocks = " ▁▂▃▄▅▆▇█"
        top = max(counts) or 1
        spark = "".join(blocks[max(0, min(8, round(n / top * 8)))] for n in counts)
        lines.append("")
        lines.append(f"  Activity (monthly commits): {spark}")
        if review.highlights.get("busiest_day"):
            lines.append(f"  Busiest day: {review.highlights['busiest_day']} "
                         f"({review.highlights['busiest_day_count']} commits)")
    lines.append("")
    lines.append("  This review was generated locally from your own git history.")
    lines.append("  Nothing left this machine. Management has seen enough anyway.")
    lines.append("")
    return "\n".join(lines)


def render_markdown(review: Review) -> str:
    out = []
    out.append("# PERFORMANCE IMPROVEMENT PLAN")
    out.append("")
    out.append(f"**Employee:** {review.author}  ")
    out.append(f"**Project reviewed:** {review.repo_name}  ")
    out.append(f"**Review period:** {review.span_start.isoformat()} to {review.span_end.isoformat()}  ")
    out.append(f"**Commits examined:** {review.total_commits}  ")
    out.append(f"**Review date:** {review.review_date.isoformat()}  ")
    out.append("**Reviewer:** Management (PIP, running locally on the employee's own machine)")
    out.append("")
    out.append(f"## Overall assessment: {review.overall_letter} ({review.overall_score:.0f}/100)")
    out.append("")
    out.append(f"*{verdict_for(review)}*")
    out.append(f"*Review style: {PERSONAS.get(review.persona, PERSONAS['corporate'])['label']}*")
    out.append("")
    out.append("This review is based entirely on the employee's own git history, "
               "the work diary every programmer keeps without meaning to. "
               "All findings below are drawn from that record. No code left this machine "
               "in the preparation of this document; the evidence was already here.")
    for c in review.categories:
        out.append("")
        out.append(f"## {c.name}: {c.letter} ({c.score:.0f}/100)")
        out.append("")
        for e in c.evidence:
            out.append(f"- {e}")
        out.append("")
        out.append(f"**Management notes:** {c.concern} {c.praise}")
    h = review.highlights
    out.append("")
    out.append("## Additional findings")
    out.append("")
    if h.get("nemesis_file"):
        out.append(f"- **Nemesis file:** {h['nemesis_file']} - {int(h['nemesis_churn']):,} lines of churn across the review period. You two have history.")
    if h.get("biggest_commit_subject"):
        out.append(f"- **Largest single commit:** {int(h['biggest_commit_lines']):,} lines changed in \"{h['biggest_commit_subject']}\". A bold unit of work.")
    out.append(f"- **Weekend work:** {h['weekend_commits']} of {review.total_commits} commits landed on a Saturday or Sunday.")
    if h.get("busiest_day"):
        out.append(f"- **Busiest day:** {h['busiest_day']}, with {h['busiest_day_count']} commits.")
    if h.get("languages"):
        langs = ", ".join(f"{name} ({int(churn):,} lines of churn)" for name, churn in h["languages"][:4])
        out.append(f"- **Languages by churn:** {langs}.")
    if h.get("longest_subject"):
        out.append(f"- **Longest commit message:** \"{h['longest_subject']}\" ({len(str(h['longest_subject']))} characters. A novel.)")
    if h.get("shortest_subject"):
        out.append(f"- **Shortest commit message:** \"{h['shortest_subject']}\". A haiku, if you squint.")
    if h.get("top_word"):
        out.append(f"- **Catchphrase:** \"{h['top_word']}\", appearing {h['top_word_count']} times across your commit subjects.")
    if (h.get("squash_ratio") or 0) >= 0.4:
        out.append(f"- **Authorship note:** {h['squash_ratio']:.0%} of these commits look like squash merges (subjects ending in a PR number). Squash merges credit whoever pressed the merge button, not whoever wrote the code, so read this grade as the record of the button-presser.")
    out.append(f"- **Net lines:** {int(h['added']):,} added, {int(h['deleted']):,} deleted.")
    if int(h.get("swears", 0)) > 0:
        out.append(f"- **Language:** {h['swears']} commit messages contain profanity. The record reflects the journey.")
    if review.awards:
        out.append("")
        out.append("## Awards")
        out.append("")
        for title, reason in review.awards:
            out.append(f"- **{title}:** {reason}")
    out.append("")
    out.append("## 30-day improvement plan")
    out.append("")
    out.append(str(PERSONAS.get(review.persona, PERSONAS["corporate"])["plan_intro"]))
    for name, actions in build_plan(review):
        out.append("")
        out.append(f"### {name}")
        for i, a in enumerate(actions, 1):
            out.append(f"{i}. {a}")
    out.append("")
    out.append("## Sign-off")
    out.append("")
    out.append(str(PERSONAS.get(review.persona, PERSONAS["corporate"])["signoff"]))
    out.append("")
    out.append("Signed,  ")
    out.append("**Management**  ")
    out.append("*PIP - pip install on-a-pip*")
    out.append("")
    out.append(f"*{NOT_FOR_EMPLOYMENT}*")
    out.append("")
    return "\n".join(out)


GRADE_COLORS = {"A": "#1d9e62", "B": "#5da423", "C": "#d9a400", "D": "#e07b24", "F": "#d43a2f"}


def awards_html(review: Review) -> str:
    if not review.awards:
        return ""
    items = "".join(
        f'<div class="award"><b>{html.escape(t)}:</b> {html.escape(r)}</div>'
        for t, r in review.awards)
    return (f'<div style="margin-top:14px;border-top:2px solid #222;padding-top:10px">'
            f'<div style="font-weight:bold;letter-spacing:1px;font-size:13px">AWARDS</div>{items}</div>')


def render_svg(review: Review) -> str:
    """A self-contained SVG report card: embeds in READMEs, posts anywhere."""
    rows = ""
    y = 168
    for c in review.categories:
        color = GRADE_COLORS[c.letter]
        rows += (
            f'<text x="36" y="{y}" font-size="15" font-weight="bold" fill="#222">{html.escape(c.name)}</text>'
            f'<circle cx="212" cy="{y - 5}" r="12" fill="{color}"/>'
            f'<text x="212" y="{y}" font-size="13" font-weight="bold" fill="#fff" text-anchor="middle">{c.letter}</text>'
            f'<text x="238" y="{y}" font-size="12" fill="#555">{c.score:.0f}/100</text>\n'
        )
        y += 30
    awards = ""
    if review.awards:
        titles = ", ".join(t for t, _ in review.awards[:3])
        awards = (f'<text x="36" y="{y + 6}" font-size="12" fill="#333">'
                  f'Awards: {html.escape(titles)}</text>')
        y += 22
    bars = ""
    months = review.highlights.get("months") or []
    if months:
        recent = months[-24:]
        top_n = max(n for _m, n in recent) or 1
        bw = 608 / len(recent)
        parts = []
        for i, (_m, n) in enumerate(recent):
            bh = max(2.0, n / top_n * 34)
            parts.append(f'<rect x="{36 + i * bw + 1:.1f}" y="{y + 40 - bh:.1f}" '
                         f'width="{bw - 2:.1f}" height="{bh:.1f}" fill="#8a6d1d"/>')
        bars = (f'<text x="36" y="{y + 12}" font-size="11" fill="#777">Commits per month</text>'
                + "".join(parts))
        y += 48
    height = y + 34
    overall_color = GRADE_COLORS[review.overall_letter]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="680" height="{height}" viewBox="0 0 680 {height}" role="img" aria-label="PIP report card for {html.escape(review.author)}">
  <rect x="3" y="3" width="674" height="{height - 6}" fill="#fffdf7" stroke="#222" stroke-width="3"/>
  <text x="36" y="48" font-family="Georgia, serif" font-size="21" letter-spacing="2" fill="#222">PERFORMANCE IMPROVEMENT PLAN</text>
  <text x="36" y="72" font-family="Georgia, serif" font-size="13" fill="#555">{html.escape(review.author)} | {html.escape(review.repo_name)} | {review.total_commits} commits | {review.span_start.isoformat()} to {review.span_end.isoformat()}</text>
  <rect x="36" y="88" width="76" height="60" rx="8" fill="{overall_color}"/>
  <text x="74" y="132" font-family="Georgia, serif" font-size="42" font-weight="bold" fill="#fff" text-anchor="middle">{review.overall_letter}</text>
  <text x="128" y="112" font-family="Georgia, serif" font-size="14" font-style="italic" fill="#333">{html.escape(verdict_for(review))}</text>
  <text x="128" y="134" font-family="Georgia, serif" font-size="12" fill="#777">Overall score: {review.overall_score:.0f}/100</text>
  <line x1="36" y1="160" x2="644" y2="160" stroke="#222" stroke-width="1"/>
{rows}{awards}{bars}
  <text x="340" y="{height - 14}" font-family="Georgia, serif" font-size="11" fill="#777" text-anchor="middle">Generated locally by PIP from the employee's own git history. pip install on-a-pip · Not for employment decisions.</text>
</svg>
"""


def render_wrapped(review: Review, year: int) -> str:
    import calendar as _cal
    months = review.highlights.get("months") or []
    busiest_month = ""
    if months:
        label, _n = max(months, key=lambda kv: kv[1])
        busiest_month = f"{_cal.month_name[int(label.split('-')[1])]} ({_n} commits)"
    award = review.awards[0][0] if review.awards else "None. A quiet year."
    lines = ["",
             f"  YOUR {year} IN COMMITS  -  {review.author}",
             f"  {review.repo_name}  |  the Wrapped edition",
             "  " + "=" * 62,
             f"  Commits:          {review.total_commits}",
             f"  Grade:            {review.overall_letter} ({review.overall_score:.0f}/100)",
             f"  Busiest month:    {busiest_month or 'n/a'}",
             f"  Busiest day:      {review.highlights.get('busiest_day')} "
             f"({review.highlights.get('busiest_day_count')} commits)",
             f"  Top award:        {award}",
             f"  Catchphrase:      \"{review.highlights.get('top_word') or 'n/a'}\"",
             f"  Lines:            {int(review.highlights.get('added', 0)):,} written, "
             f"{int(review.highlights.get('deleted', 0)):,} deleted",
             "  " + "=" * 62,
             f"  {verdict_for(review)}",
             "  Same time next year. Management will bring the spreadsheet.",
             ""]
    return "\n".join(lines)


def render_wrapped_svg(review: Review, year: int) -> str:
    import calendar as _cal
    months = review.highlights.get("months") or []
    busiest_month = "n/a"
    if months:
        label, _n = max(months, key=lambda kv: kv[1])
        busiest_month = _cal.month_name[int(label.split("-")[1])]
    award = review.awards[0][0] if review.awards else "None"
    color = GRADE_COLORS[review.overall_letter]
    bars = ""
    if months:
        recent = months[-12:]
        top_n = max(n for _m, n in recent) or 1
        bw = 608 / len(recent)
        parts = []
        for i, (_m, n) in enumerate(recent):
            bh = max(2.0, n / top_n * 60)
            parts.append(f'<rect x="{36 + i * bw + 1:.1f}" y="{330 - bh:.1f}" width="{bw - 2:.1f}" '
                         f'height="{bh:.1f}" fill="#e8b93c"/>')
        bars = "".join(parts)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="680" height="400" viewBox="0 0 680 400" role="img" aria-label="{year} in commits for {html.escape(review.author)}">
  <rect x="3" y="3" width="674" height="394" fill="#191919" stroke="#e8b93c" stroke-width="3"/>
  <text x="36" y="58" font-family="Georgia, serif" font-size="30" letter-spacing="3" fill="#e8b93c">YOUR {year} IN COMMITS</text>
  <text x="36" y="84" font-family="Georgia, serif" font-size="14" fill="#ccc">{html.escape(review.author)} | {html.escape(review.repo_name)}</text>
  <rect x="36" y="104" width="86" height="68" rx="8" fill="{color}"/>
  <text x="79" y="154" font-family="Georgia, serif" font-size="48" font-weight="bold" fill="#fff" text-anchor="middle">{review.overall_letter}</text>
  <text x="140" y="128" font-family="Georgia, serif" font-size="17" fill="#fff">{review.total_commits} commits</text>
  <text x="140" y="152" font-family="Georgia, serif" font-size="14" fill="#bbb">Busiest month: {busiest_month}</text>
  <text x="36" y="206" font-family="Georgia, serif" font-size="15" fill="#fff">Top award: {html.escape(award)}</text>
  <text x="36" y="232" font-family="Georgia, serif" font-size="15" fill="#fff">Catchphrase: "{html.escape(str(review.highlights.get('top_word') or 'n/a'))}"</text>
  <text x="36" y="258" font-family="Georgia, serif" font-size="13" font-style="italic" fill="#999">{html.escape(verdict_for(review))}</text>
{bars}
  <text x="340" y="386" font-family="Georgia, serif" font-size="11" fill="#888" text-anchor="middle">PIP Wrapped. Generated locally from git history. pip install on-a-pip</text>
</svg>
"""


def render_share_svg(review: Review) -> str:
    """The 1200x630 share card: the size social platforms actually render."""
    color = GRADE_COLORS[review.overall_letter]
    award = review.awards[0][0] if review.awards else "No awards. A quiet record."
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" role="img" aria-label="PIP review for {html.escape(review.author)}">
  <rect x="4" y="4" width="1192" height="622" fill="#fdfcf8" stroke="#222" stroke-width="3"/>
  <text x="64" y="92" font-family="Georgia, serif" font-size="26" letter-spacing="4" fill="#555">PERFORMANCE IMPROVEMENT PLAN</text>
  <text x="64" y="140" font-family="Georgia, serif" font-size="19" fill="#777">{html.escape(review.author)} | {html.escape(review.repo_name)} | {review.total_commits} commits reviewed</text>
  <rect x="64" y="176" width="220" height="220" rx="14" fill="{color}"/>
  <text x="174" y="330" font-family="Georgia, serif" font-size="150" font-weight="bold" fill="#fff" text-anchor="middle">{review.overall_letter}</text>
  <text x="330" y="238" font-family="Georgia, serif" font-size="30" font-style="italic" fill="#222">{html.escape(verdict_for(review))}</text>
  <text x="330" y="292" font-family="Georgia, serif" font-size="24" fill="#444">Overall score: {review.overall_score:.0f}/100</text>
  <text x="330" y="340" font-family="Georgia, serif" font-size="24" fill="#444">Top award: {html.escape(award)}</text>
  <text x="330" y="388" font-family="Georgia, serif" font-size="24" fill="#444">Catchphrase: "{html.escape(str(review.highlights.get('top_word') or 'n/a'))}"</text>
  <line x1="64" y1="470" x2="1136" y2="470" stroke="#222" stroke-width="1"/>
  <text x="64" y="530" font-family="Georgia, serif" font-size="22" fill="#333">My git history put me on a PIP. Yours can too:</text>
  <text x="64" y="572" font-family="Menlo, monospace" font-size="26" fill="#111">pip install on-a-pip</text>
  <text x="1136" y="572" font-family="Georgia, serif" font-size="15" fill="#999" text-anchor="end">Not for employment decisions.</text>
</svg>
"""


def boards_to_csv(rows: list[tuple[str, Review]], with_repo: bool) -> str:
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow((["repo"] if with_repo else []) +
               ["author", "grade", "score", "commits", "top_award"])
    for name, r in rows:
        w.writerow((([name] if with_repo else []) +
                    [r.author, r.overall_letter, f"{r.overall_score:.1f}",
                     r.total_commits, r.awards[0][0] if r.awards else ""]))
    return buf.getvalue()


def render_badge(review: Review) -> str:
    """A small shields-style grade badge for a README."""
    color = GRADE_COLORS[review.overall_letter]
    value = f"{review.overall_letter} ({review.overall_score:.0f}/100)"
    label_w, value_w = 86, 12 + 8 * len(value)
    total = label_w + value_w
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20" role="img" aria-label="PIP grade: {value}">
  <rect width="{label_w}" height="20" fill="#555"/>
  <rect x="{label_w}" width="{value_w}" height="20" fill="{color}"/>
  <text x="{label_w / 2}" y="14" font-family="Verdana, sans-serif" font-size="11" fill="#fff" text-anchor="middle">my PIP grade</text>
  <text x="{label_w + value_w / 2}" y="14" font-family="Verdana, sans-serif" font-size="11" fill="#fff" text-anchor="middle">{value}</text>
</svg>
"""


def pair_stats(commits_in: list[Commit], top: int = 3) -> list[tuple[str, str, int]]:
    """Author pairs ranked by shared active days: who ships together."""
    days: dict[str, set] = {}
    for name, cs, _k in _author_groups(commits_in):
        days[name] = {c.when.date() for c in cs}
    pairs: list[tuple[str, str, int]] = []
    names = sorted(days)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = len(days[a] & days[b])
            if shared:
                pairs.append((a, b, shared))
    return sorted(pairs, key=lambda p: (-p[2], p[0], p[1]))[:top]


def render_leaderboard(reviews: list[Review], repo_name: str,
                       pairs: list[tuple[str, str, int]] | None = None) -> str:
    lines = ["", f"  PIP LEADERBOARD  -  {repo_name}", "  " + "-" * 62,
             f"  {'#':<3} {'Employee':<26} {'Grade':<6} {'Score':<7} {'Commits':<8} Top award"]
    for i, r in enumerate(reviews, 1):
        award = r.awards[0][0] if r.awards else "-"
        lines.append(f"  {i:<3} {r.author[:25]:<26} {r.overall_letter:<6} {r.overall_score:<7.1f} {r.total_commits:<8} {award}")
    lines.append("  " + "-" * 62)
    lines.append("  Ranked by overall PIP score. Ties broken by whoever panics less.")
    if pairs:
        a, b, shared = pairs[0]
        lines.append(f"  Most in sync: {a} + {b}, {shared} shared active days. "
                     "Management calls this collaboration. The calendar calls it evidence.")
    lines.append("")
    return "\n".join(lines)


def _vs_winner(a_score: float, b_score: float, a: "Review", b: "Review") -> str:
    if abs(a_score - b_score) < 0.05:
        return "Tie"
    return a.author if a_score > b_score else b.author


def render_vs(a: Review, b: Review) -> str:
    lines = ["", f"  HEAD TO HEAD  -  {a.repo_name}", "  " + "-" * 62,
             f"  {'Category':<16} {a.author[:18]:<20} {b.author[:18]:<20} Winner"]
    for ca, cb in zip(a.categories, b.categories):
        lines.append(f"  {ca.name:<16} {ca.letter} {ca.score:<17.1f} {cb.letter} {cb.score:<17.1f} "
                     f"{_vs_winner(ca.score, cb.score, a, b)}")
    lines.append("  " + "-" * 62)
    lines.append(f"  {'OVERALL':<16} {a.overall_letter} {a.overall_score:<17.1f} "
                 f"{b.overall_letter} {b.overall_score:<17.1f} {_vs_winner(a.overall_score, b.overall_score, a, b)}")
    winner = a if a.overall_score >= b.overall_score else b
    loser = b if winner is a else a
    margin = abs(a.overall_score - b.overall_score)
    if margin < 0.05:
        lines.append("  Dead heat. Management suggests a rematch next quarter, or a coin.")
    elif margin < 8:
        lines.append(f"  {winner.author} takes it, narrowly. {loser.author} has been informed. "
                     "There will be a conversation.")
    else:
        lines.append(f"  {winner.author} wins decisively. {loser.author}'s improvement plan "
                     "has been extended to 60 days.")
    lines.append(f"  Awards: {a.author} {len(a.awards)} - {len(b.awards)} {b.author}")
    lines.append("")
    return "\n".join(lines)


def render_vs_markdown(a: Review, b: Review) -> str:
    out = [f"# Head to head: {a.author} vs {b.author}", "",
           f"Repository: {a.repo_name} · {a.review_date.isoformat()}", "",
           "| Category | " + f"{a.author} | {b.author} | Winner |",
           "| --- | --- | --- | --- |"]
    for ca, cb in zip(a.categories, b.categories):
        out.append(f"| {ca.name} | {ca.letter} ({ca.score:.0f}) | {cb.letter} ({cb.score:.0f}) | "
                   f"{_vs_winner(ca.score, cb.score, a, b)} |")
    out.append(f"| **Overall** | **{a.overall_letter} ({a.overall_score:.0f})** | "
               f"**{b.overall_letter} ({b.overall_score:.0f})** | "
               f"**{_vs_winner(a.overall_score, b.overall_score, a, b)}** |")
    out.append("")
    for r in (a, b):
        titles = ", ".join(t for t, _ in r.awards) or "none"
        out.append(f"- **{r.author}:** {r.total_commits} commits, awards: {titles}")
    out.append("")
    out.append("*Generated by PIP. pip install on-a-pip*")
    out.append("")
    out.append(f"*{NOT_FOR_EMPLOYMENT}*")
    out.append("")
    return "\n".join(out)


def scan_repos(root: str, persona: str = "corporate", today: date | None = None,
               max_commits: int = 5000, include_bots: bool = False) -> list[tuple[str, Review]]:
    """Review the top author of every git repo directly inside a folder."""
    today = today or date.today()
    results: list[tuple[str, Review]] = []
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if not os.path.isdir(path):
            continue
        inside = _git(path, ["rev-parse", "--is-inside-work-tree"], check=False).strip()
        if inside != "true":
            continue
        try:
            commits = collect_commits(path, max_commits)
            if not commits:
                continue
            stats, file_totals, paths_by_sha = collect_numstat(path, {c.sha for c in commits})
            for c in commits:
                if c.sha in stats:
                    c.added, c.deleted, c.files = stats[c.sha]
                    c.paths = tuple(paths_by_sha.get(c.sha, ()))
            markers = collect_markers(path)
            review = analyze(path, commits, markers, None, today,
                             file_totals=file_totals, persona=persona,
                             include_bots=include_bots)
            results.append((name, review))
        except PipError:
            continue
    return sorted(results, key=lambda kv: -kv[1].overall_score)


def render_scan(results: list[tuple[str, Review]], root_name: str) -> str:
    lines = ["", f"  PIP SCAN  -  {root_name}  ({len(results)} repositories)", "  " + "-" * 62,
             f"  {'#':<3} {'Repository':<22} {'Top author':<22} {'Grade':<6} {'Score':<7} Commits"]
    for i, (name, r) in enumerate(results, 1):
        lines.append(f"  {i:<3} {name[:21]:<22} {r.author[:21]:<22} {r.overall_letter:<6} "
                     f"{r.overall_score:<7.1f} {r.total_commits}")
    lines.append("  " + "-" * 62)
    lines.append("  Every repo's most prolific author, ranked. Cross-team bragging rights apply.")
    lines.append("")
    return "\n".join(lines)


def render_html(review: Review) -> str:
    rows = ""
    for c in review.categories:
        color = GRADE_COLORS[c.letter]
        rows += (
            f'<div class="row"><span class="cat">{html.escape(c.name)}</span>'
            f'<span class="grade" style="background:{color}">{c.letter}</span>'
            f'<span class="ev">{html.escape(c.evidence[0])}</span></div>\n'
        )
    overall_color = GRADE_COLORS[review.overall_letter]
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>PIP Report Card - {html.escape(review.author)}</title>
<style>
  body {{ font-family: Georgia, 'Times New Roman', serif; background:#f2efe9; margin:0; padding:32px 16px; }}
  .card {{ max-width:680px; margin:0 auto; background:#fffdf7; border:2px solid #222; padding:28px 32px; box-shadow:6px 6px 0 #222; }}
  h1 {{ font-size:22px; letter-spacing:2px; margin:0 0 4px; text-transform:uppercase; }}
  .sub {{ color:#555; font-size:13px; margin-bottom:18px; }}
  .overall {{ display:flex; align-items:center; gap:18px; border-top:2px solid #222; border-bottom:2px solid #222; padding:14px 0; margin-bottom:14px; }}
  .big {{ font-size:64px; font-weight:bold; color:#fff; width:96px; height:96px; display:flex; align-items:center; justify-content:center; background:{overall_color}; border-radius:8px; }}
  .verdict {{ font-style:italic; font-size:16px; }}
  .row {{ display:flex; align-items:flex-start; gap:12px; padding:9px 0; border-bottom:1px dotted #bbb; }}
  .cat {{ width:130px; font-weight:bold; font-size:14px; padding-top:3px; }}
  .grade {{ color:#fff; font-weight:bold; width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex:none; }}
  .ev {{ font-size:13px; color:#333; }}
  .foot {{ margin-top:18px; font-size:12px; color:#777; text-align:center; }}
</style></head><body>
<div class="card">
  <h1>Performance Improvement Plan</h1>
  <div class="sub">Employee: {html.escape(review.author)} &nbsp;|&nbsp; Project: {html.escape(review.repo_name)} &nbsp;|&nbsp;
  {review.total_commits} commits reviewed &nbsp;|&nbsp; {review.span_start.isoformat()} to {review.span_end.isoformat()}</div>
  <div class="overall"><div class="big">{review.overall_letter}</div>
  <div class="verdict">"{html.escape(verdict_for(review))}"</div></div>
{rows}{awards_html(review)}
  <div class="foot">Generated locally by PIP from the employee's own git history. Nothing was uploaded. Not for employment decisions.<br>
  pip install on-a-pip</div>
</div></body></html>
"""


def review_to_json(review: Review) -> dict:
    return {
        "tool": "on-a-pip", "version": __version__,
        "repo": review.repo_name, "author": review.author,
        "review_date": review.review_date.isoformat(),
        "period": [review.span_start.isoformat(), review.span_end.isoformat()],
        "total_commits": review.total_commits,
        "overall": {"letter": review.overall_letter, "score": round(review.overall_score, 1)},
        "categories": [
            {"name": c.name, "letter": c.letter, "score": round(c.score, 1), "evidence": c.evidence}
            for c in review.categories
        ],
        "awards": [{"title": t, "reason": r} for t, r in review.awards],
        "persona": review.persona,
        "highlights": {k: v for k, v in review.highlights.items()},
    }


REFERENCE_OPENERS = {
    "A": "It is a genuine pleasure to recommend {author}. In {total} commits on {repo} "
         "between {start} and {end}, they produced the kind of record managers frame. "
         "{best} was a particular strength. Hire them before someone else reads this file.",
    "B": "I am glad to recommend {author}. Across {total} commits on {repo}, the record is "
         "strong and steady, with {best} standing out. Any team would be better for having "
         "this history pointed at their problems.",
    "C": "I am writing in reference to {author}, who committed {total} times to {repo} "
         "between {start} and {end}. The record is mixed in the way real records are: "
         "{best} was solid, and the rest is documented in a formal improvement plan, "
         "which they have received. Growth is a trajectory, and theirs points up.",
    "D": "To whom it may concern: {author} was, verifiably, present for {total} commits "
         "on {repo}. Their strongest category was {best}. A full performance review is "
         "available and has been shared with the employee. We wish them well in their "
         "30-day plan, and we mean that in every sense it can be taken.",
    "F": "To whom it may concern: {author} committed to {repo} {total} times. "
         "Attendance, in the narrowest technical sense, occurred. Their best category "
         "was {best}, and this letter has been kept brief out of a shared interest "
         "in honesty. A formal improvement plan is in effect.",
}


README_START = "<!-- pip:start -->"
README_END = "<!-- pip:end -->"


def render_readme_section(review: Review, card_file: str = "pip-card.svg",
                          badge_file: str = "pip-badge.svg") -> str:
    award = review.awards[0][0] if review.awards else "None yet"
    return (
        f"{README_START}\n"
        f"## My PIP review\n\n"
        f"![My PIP grade]({badge_file})\n\n"
        f"![PIP report card]({card_file})\n\n"
        f"**Grade: {review.overall_letter} ({review.overall_score:.0f}/100)** · "
        f"{review.total_commits} commits reviewed · Top award: {award} · "
        f"Reviewed {review.review_date.isoformat()}\n\n"
        f"*This section is maintained by [PIP](https://pypi.org/project/on-a-pip/) "
        f"(`on-a-pip --readme`). The record speaks for itself.*\n"
        f"{README_END}"
    )


def update_readme(repo: str, review: Review) -> tuple[str, str, str]:
    """Write the card and badge into the repo and insert or refresh the
    marked PIP section in its README. Returns (readme, card, badge) paths."""
    readme = os.path.join(repo, "README.md")
    if not os.path.isfile(readme):
        raise PipError("no README.md in this repository to write the review into")
    card = os.path.join(repo, "pip-card.svg")
    badge = os.path.join(repo, "pip-badge.svg")
    with open(card, "w", encoding="utf-8") as f:
        f.write(render_svg(review))
    with open(badge, "w", encoding="utf-8") as f:
        f.write(render_badge(review))
    section = render_readme_section(review)
    with open(readme, encoding="utf-8") as f:
        text = f.read()
    if README_START in text and README_END in text:
        head, rest = text.split(README_START, 1)
        _old, tail = rest.split(README_END, 1)
        text = head.rstrip() + "\n\n" + section + tail
    else:
        text = text.rstrip() + "\n\n" + section + "\n"
    with open(readme, "w", encoding="utf-8") as f:
        f.write(text)
    return readme, card, badge


def render_reference(review: Review) -> str:
    best = max(review.categories, key=lambda c: c.score)
    body = REFERENCE_OPENERS[review.overall_letter].format(
        author=review.author, total=review.total_commits, repo=review.repo_name,
        start=review.span_start.isoformat(), end=review.span_end.isoformat(),
        best=best.name)
    persona_label = PERSONAS.get(review.persona, PERSONAS["corporate"])["label"]  # type: ignore[attr-defined]
    return (
        f"# Letter of reference: {review.author}\n\n"
        f"{review.review_date.isoformat()}\n\n"
        f"{body}\n\n"
        f"Overall grade on the record: {review.overall_letter} ({review.overall_score:.0f}/100).\n\n"
        f"Signed,\nManagement ({persona_label})\n"
        f"*Generated by PIP from the employee's own git history. pip install on-a-pip*\n"
    )


# --------------------------------------------------------------------------
# progress tracking (local only, like everything else here)
# --------------------------------------------------------------------------

def _progress_path(repo: str) -> str:
    import hashlib
    key = hashlib.sha1(repo.encode()).hexdigest()[:12]
    base = os.path.join(os.path.expanduser("~"), ".config", "on-a-pip")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"{key}.json")


def load_previous(repo: str) -> dict | None:
    try:
        with open(_progress_path(repo), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def save_current(repo: str, review: Review) -> None:
    entry = {"date": review.review_date.isoformat(),
             "overall_score": round(review.overall_score, 1),
             "overall_letter": review.overall_letter,
             "author": review.author}
    existing = load_previous(repo) or {}
    hist = existing.get("history")
    if not isinstance(hist, list):
        hist = [{k: existing.get(k) for k in entry}] if existing.get("date") else []
    hist.append(entry)
    data = {**entry, "history": hist[-50:]}
    try:
        with open(_progress_path(repo), "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass


def load_history(repo: str) -> list[dict]:
    data = load_previous(repo)
    if not data:
        return []
    hist = data.get("history")
    if isinstance(hist, list):
        return hist
    if data.get("date"):
        return [{"date": data.get("date"), "overall_score": data.get("overall_score"),
                 "overall_letter": data.get("overall_letter"), "author": data.get("author")}]
    return []


def render_history(entries: list[dict], repo_name: str) -> str:
    lines = ["", f"  REVIEW HISTORY  -  {repo_name}", "  " + "-" * 62]
    for e in entries:
        score = float(e.get("overall_score") or 0)
        bar = "█" * max(1, round(score / 5))
        lines.append(f"  {e.get('date')}  {e.get('overall_letter')}  {score:5.1f}  {bar}")
    lines.append("  " + "-" * 62)
    if len(entries) >= 2:
        delta = float(entries[-1].get("overall_score") or 0) - float(entries[0].get("overall_score") or 0)
        if delta > 2:
            lines.append(f"  Trend: up {delta:.1f} points over {len(entries)} reviews. Management notes the trajectory, approvingly.")
        elif delta < -2:
            lines.append(f"  Trend: down {abs(delta):.1f} points over {len(entries)} reviews. Management notes the trajectory, with a folder.")
        else:
            lines.append(f"  Trend: flat over {len(entries)} reviews. Consistency, or a plateau wearing its clothes.")
    lines.append("")
    return "\n".join(lines)


DRILLS: dict[str, list[tuple[str, str]]] = {
    "Communication": [
        ("Every commit subject this week must complete the sentence 'This change will...' before you type it.", "Zero subjects under 10 characters."),
        ("Add a body to every commit explaining why, not what. The diff already says what.", "Body ratio above 80% for the week."),
        ("Ban the words stuff, things, wip, and misc from subjects. If it needs 'misc', it needs two commits.", "Vague-subject count: zero."),
        ("Write one commit message as if the reader is you, in six months, at 2am, during an outage.", "At least one message a stranger could act on."),
    ],
    "Reliability": [
        ("No commits after 4pm on Fridays. Write them, branch them, ship them Monday.", "Friday-late count: zero."),
        ("Before any fix, write down what the last change to that file was. Then fix.", "Revert count: zero."),
        ("Every commit after 1am gets a comment the next morning explaining itself.", "Night commits all accounted for."),
        ("One change per commit, one concern per branch. If the subject needs 'and', split it.", "Average files per commit trending down."),
    ],
    "Follow-through": [
        ("Pick the oldest TODO you own. Close it or delete it. One per day.", "Oldest TODO younger than last week."),
        ("Every 'temporary' fix gets a calendar date in the comment, and the date is this month.", "No undated temporary fixes."),
        ("End each day by finishing one thing instead of starting one thing.", "Work in progress: fewer than three branches."),
        ("Revisit last week's workaround and replace it with the real fix.", "One workaround retired."),
    ],
    "Judgment": [
        ("Before deleting more than 200 lines, write the reason in the commit body.", "Every big deletion explained."),
        ("If a commit needs the word 'hack', it needs a follow-up note in the same breath.", "Hacks with follow-ups: all of them."),
        ("Revert rehearsal: practice reverting your own last commit in a scratch branch.", "You can undo anything you ship, quickly."),
        ("Ask 'what breaks if this is wrong?' and put the answer in the message.", "Risk notes present on risky commits."),
    ],
    "Consistency": [
        ("Commit something small every working day. Streaks are built from boring days.", "Five active days this week."),
        ("Set a commit o'clock: same hour daily, ten minutes, tidy one thing.", "No gaps longer than three days."),
        ("Batch the chaos: one planned work block beats six panic commits.", "Commits spread across the week, not piled onto one day."),
        ("End the week by committing the thing you have been avoiding since Monday.", "The avoided thing: shipped."),
    ],
}


def coach_plan(review: Review) -> list[tuple[int, str, str, str]]:
    weakest = sorted(review.categories, key=lambda c: c.score)[:3]
    plan = []
    for week in range(1, 5):
        cat = weakest[(week - 1) % len(weakest)]
        drill, check = DRILLS[cat.name][week - 1]
        plan.append((week, cat.name, drill, check))
    return plan


def render_coach(review: Review) -> str:
    lines = ["",
             f"  DEVELOPMENT PLAN (COACHING MODE)  -  {review.author}",
             f"  {review.repo_name}  |  current grade {review.overall_letter} ({review.overall_score:.0f}/100)",
             "  " + "=" * 62,
             "  No verdict this time. Just the work. Four weeks, one drill a week,",
             "  each aimed at a category that needs it, each with a way to check.",
             ""]
    for week, cat, drill, check in coach_plan(review):
        lines.append(f"  Week {week}  [{cat}]")
        lines.append(f"    Drill: {drill}")
        lines.append(f"    Check: {check}")
        lines.append("")
    lines.append("  Re-run PIP in four weeks. The grade will have opinions about attendance.")
    lines.append("")
    return "\n".join(lines)


def render_coach_markdown(review: Review) -> str:
    out = [f"## Development plan (coaching mode) for {review.author}", ""]
    for week, cat, drill, check in coach_plan(review):
        out.append(f"- **Week {week} [{cat}]:** {drill} *Check: {check}*")
    out.append("")
    return "\n".join(out)


def parse_tz(text: str):
    """Parse a --tz value: an IANA name (Europe/Berlin) or a fixed offset
    like UTC+05:30 / UTC-4. Returns a tzinfo; PipError with guidance if not."""
    from datetime import timezone as _tz, timedelta as _td
    m = re.fullmatch(r"UTC([+-])(\d{1,2})(?::?(\d{2}))?", text.strip(), re.IGNORECASE)
    if m:
        sign = 1 if m.group(1) == "+" else -1
        hours = int(m.group(2)) + int(m.group(3) or 0) / 60
        return _tz(_td(hours=sign * hours))
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(text)
    except Exception:
        raise PipError(f"timezone '{text}' was not understood. Use an IANA name "
                       "like Europe/Berlin, or a fixed offset like UTC+05:30.")


NOT_FOR_EMPLOYMENT = ("Not for employment decisions. PIP grades a commit record, "
                      "not a person, and it reads best when the person reading it "
                      "is the person who wrote the commits.")


def load_repo_config(repo: str) -> dict:
    """Read .pip.toml defaults (persona, fail_below) from the repo root.
    Deliberately a tiny parser: two string keys, no dependency on tomllib
    (Python 3.11+) so 3.9 and 3.10 keep working."""
    cfg: dict[str, str] = {}
    try:
        with open(os.path.join(repo, ".pip.toml"), encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return cfg
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        m = re.match(r'^(persona|fail_below)\s*=\s*"([^"]+)"', line)
        if m:
            cfg[m.group(1)] = m.group(2)
    return cfg


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="on-a-pip",
        description="PIP: a formal performance review of the programmer, "
                    "generated locally from their own git history.")
    ap.add_argument("repo", nargs="?", default=".",
                    help="a git repository path, a git URL, or a GitHub shorthand like psf/requests (default: current directory)")
    ap.add_argument("--shallow", type=int, metavar="N",
                    help="with a URL: clone only the last N commits (faster on huge repos; the review covers what was fetched)")
    ap.add_argument("--keep", action="store_true",
                    help="with a URL: keep the clone afterwards and print where it is")
    ap.add_argument("--author", help="review only commits by authors matching this text (default: most prolific author)")
    ap.add_argument("--max-commits", type=int, default=10000, help="cap on commits examined (default 10000)")
    ap.add_argument("--days", type=int, help="review only the last N days of history (anchored at the most recent commit)")
    ap.add_argument("--since", metavar="YYYY-MM-DD", help="review only commits on or after this date")
    ap.add_argument("--until", metavar="YYYY-MM-DD", help="review only commits on or before this date")
    ap.add_argument("--reference", metavar="FILE", help="also write a letter of reference based on the grade")
    ap.add_argument("--readme", action="store_true",
                    help="write pip-card.svg and pip-badge.svg into the repo and add or refresh the PIP section in its README")
    ap.add_argument("--persona", choices=sorted(PERSONAS), default=None,
                    help="the reviewing manager's style (default: corporate)")
    ap.add_argument("--leaderboard", action="store_true",
                    help="review every author in the repo and rank them")
    ap.add_argument("--vs", nargs=2, metavar=("AUTHOR_A", "AUTHOR_B"),
                    help="head to head: review two authors in the repo and compare them")
    ap.add_argument("--scan", action="store_true",
                    help="treat the target as a folder of repositories and review the top author of each")
    ap.add_argument("--quarter", action="store_true",
                    help="quarterly ritual mode: review the last 90 days and compare with your last review")
    ap.add_argument("--year", type=int, metavar="YYYY",
                    help="Wrapped mode: review one calendar year and print the year-in-commits edition")
    ap.add_argument("--top", type=int, default=8, help="leaderboard size (default 8)")
    ap.add_argument("--outdir", metavar="DIR",
                    help="write every artifact (review, cards, badge, reference, JSON) into this directory")
    ap.add_argument("--persona-file", metavar="JSON",
                    help="load a custom persona pack from a JSON file (see personas/ in the repo)")
    ap.add_argument("--org", metavar="GITHUB_USER",
                    help="org mode: review the top author of a GitHub user's public repositories")
    ap.add_argument("--org-limit", type=int, default=10,
                    help="how many repositories --org reviews, most recently pushed first (default 10)")
    ap.add_argument("--include-forks", action="store_true",
                    help="with --org, include forked repositories")
    ap.add_argument("--history", action="store_true",
                    help="print this repo's grade history from your saved reviews, then exit")
    ap.add_argument("--coach", action="store_true",
                    help="coaching mode: a four-week drill plan for the weakest categories instead of a verdict")
    ap.add_argument("--blame", metavar="FILE",
                    help="review only the commits that touched this file")
    ap.add_argument("--fail-below", choices=["A", "B", "C", "D", "F"], metavar="GRADE",
                    help="exit with code 3 if the overall grade is worse than GRADE (a novelty CI gate; not an employment tool)")
    ap.add_argument("--include-bots", action="store_true",
                    help="include bot authors (dependabot and friends) instead of excluding them by default")
    ap.add_argument("--tz", metavar="TZ",
                    help="grade in this timezone (IANA name like Europe/Berlin, or UTC+05:30) instead of each commit's own offset")
    ap.add_argument("--branch", metavar="NAME", help="review only this branch")
    ap.add_argument("--path", metavar="PATH", help="review only commits touching this path")
    ap.add_argument("--include-generated", action="store_true",
                    help="count lockfiles and minified files in churn (excluded by default)")
    ap.add_argument("--share", metavar="FILE",
                    help="also write the 1200x630 share card (SVG) to this file")
    ap.add_argument("--csv", action="store_true",
                    help="with --leaderboard, --scan, or --org, print CSV instead of the board")
    ap.add_argument("--md", metavar="FILE", help="write the full review as Markdown")
    ap.add_argument("--html", metavar="FILE", help="write the shareable report card as HTML")
    ap.add_argument("--svg", metavar="FILE", help="write the shareable report card as SVG (embeds in READMEs)")
    ap.add_argument("--badge", metavar="FILE", help="write a small grade badge as SVG")
    ap.add_argument("--json", action="store_true", help="print the review as JSON instead of the summary")
    ap.add_argument("--version", action="version", version=f"on-a-pip {__version__}")
    args = ap.parse_args(argv)

    if args.persona_file:
        try:
            args.persona = load_persona_file(args.persona_file)
        except PipError as e:
            print(f"on-a-pip: {e}", file=sys.stderr)
            return 2
    if args.org:
        return _run_org(args)

    progress_key = args.repo
    repo_arg = args.repo
    clone_root = None
    if is_clone_target(args.repo):
        import atexit
        url = expand_clone_url(args.repo)
        try:
            repo_arg, clone_root = clone_repo(url, args.shallow)
        except PipError as e:
            print(f"on-a-pip: {e}", file=sys.stderr)
            return 2
        except FileNotFoundError:
            print("on-a-pip: git was not found on this machine", file=sys.stderr)
            return 2
        progress_key = url
        if args.keep:
            print(f"Clone kept at {repo_arg}", file=sys.stderr)
        else:
            atexit.register(shutil.rmtree, clone_root, ignore_errors=True)

    repo = os.path.abspath(repo_arg)
    if not is_clone_target(args.repo):
        progress_key = repo
    cfg = load_repo_config(repo) if os.path.isdir(repo) else {}
    if args.persona is None:
        args.persona = cfg.get("persona") if cfg.get("persona") in PERSONAS else "corporate"
    if args.fail_below is None and cfg.get("fail_below") in ("A", "B", "C", "D", "F"):
        args.fail_below = cfg["fail_below"]
    tzinfo_obj = None
    if args.tz:
        try:
            tzinfo_obj = parse_tz(args.tz)
        except PipError as e:
            print(f"on-a-pip: {e}", file=sys.stderr)
            return 2
    if args.history:
        entries = load_history(progress_key)
        if not entries:
            print("No review history yet for this repository. Run a review first; history starts there.")
        else:
            print(render_history(entries, os.path.basename(repo) or repo))
        return 0
    if args.quarter and args.days is None and not (args.since or args.until):
        args.days = 90
    if args.year and not (args.since or args.until):
        args.since = f"{args.year}-01-01"
        args.until = f"{args.year}-12-31"
    if args.scan:
        if not os.path.isdir(repo):
            print(f"on-a-pip: {args.repo} is not a directory to scan", file=sys.stderr)
            return 2
        results = scan_repos(repo, persona=args.persona, include_bots=args.include_bots)
        if not results:
            print("on-a-pip: no git repositories with commits found in that folder", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps({"scan": [{"repo": name, **review_to_json(r)} for name, r in results]},
                             indent=2, default=str))
        elif args.csv:
            print(boards_to_csv(results, with_repo=True), end="")
        else:
            print(render_scan(results, os.path.basename(repo) or repo))
        return 0
    try:
        inside = _git(repo, ["rev-parse", "--is-inside-work-tree"], check=False).strip()
        if inside != "true":
            raise PipError(f"{args.repo} is not a git repository")
        commits = collect_commits(repo, args.max_commits,
                                  branch=args.branch, path=args.path)
        if not commits:
            raise PipError("this repository has no commits yet. Management cannot review potential.")
        commits = scope_commits(commits, args.days)
        if args.since or args.until:
            try:
                lo = date.fromisoformat(args.since) if args.since else date.min
                hi = date.fromisoformat(args.until) if args.until else date.max
            except ValueError:
                raise PipError("--since and --until take dates like 2026-01-31")
            commits = [c for c in commits if lo <= c.when.date() <= hi]
        if not commits:
            raise PipError("no commits in the requested period. Management cannot review a rumor.")
        if len(commits) >= 2000:
            print(f"on-a-pip: {len(commits):,} commits in the record; weighing the "
                  "evidence (line counts can take a moment on large histories)...",
                  file=sys.stderr)
        stats, file_totals, paths_by_sha = collect_numstat(
            repo, {c.sha for c in commits}, branch=args.branch, path=args.path,
            exclude_generated=not args.include_generated)
        for c in commits:
            if c.sha in stats:
                c.added, c.deleted, c.files = stats[c.sha]
                c.paths = tuple(paths_by_sha.get(c.sha, ()))
        if args.blame:
            target = args.blame.replace(os.sep, "/")
            commits = [c for c in commits
                       if any(p == target or p.endswith("/" + target) for p in c.paths)]
            if not commits:
                raise PipError(f"no commits touched '{args.blame}' in this repository's history.")
        markers = collect_markers(repo)
        if args.vs:
            first = analyze(repo, commits, markers, args.vs[0], date.today(),
                            file_totals=file_totals, persona=args.persona,
                            include_bots=args.include_bots, tz=tzinfo_obj)
            second = analyze(repo, commits, markers, args.vs[1], date.today(),
                             file_totals=file_totals, persona=args.persona,
                             include_bots=args.include_bots, tz=tzinfo_obj)
            if args.json:
                print(json.dumps({"versus": [review_to_json(first), review_to_json(second)]},
                                 indent=2, default=str))
            else:
                print(render_vs(first, second))
            if args.md:
                with open(args.md, "w", encoding="utf-8") as f:
                    f.write(render_vs_markdown(first, second))
                print(f"Head to head written to {args.md}")
            return 0
        if args.leaderboard:
            board = leaderboard(repo, commits, markers, date.today(),
                                file_totals=file_totals, persona=args.persona, top=args.top,
                                include_bots=args.include_bots, tz=tzinfo_obj)
            if not board:
                raise PipError("no author has enough commits to rank yet")
            repo_name = os.path.basename(repo) or repo
            pairs = pair_stats(commits)
            if args.json:
                print(json.dumps({"leaderboard": [review_to_json(r) for r in board],
                                  "pairs": [{"authors": [a, b], "shared_days": n}
                                            for a, b, n in pairs]},
                                 indent=2, default=str))
            elif args.csv:
                print(boards_to_csv([(r.repo_name, r) for r in board], with_repo=False), end="")
            else:
                print(render_leaderboard(board, repo_name, pairs=pairs))
            return 0
        review = analyze(repo, commits, markers, args.author, date.today(),
                         file_totals=file_totals, persona=args.persona,
                         include_bots=args.include_bots, tz=tzinfo_obj)
        if args.blame:
            review.repo_name = f"{review.repo_name} :: {args.blame}"
    except PipError as e:
        print(f"on-a-pip: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print("on-a-pip: git was not found on this machine", file=sys.stderr)
        return 2

    previous = None if args.blame else load_previous(progress_key)
    if args.author:
        print("Note: you are reviewing someone else's record. PIP is a joke best "
              "told by the person themselves; share it with them, not about them.",
              file=sys.stderr)
    if args.json:
        print(json.dumps(review_to_json(review), indent=2, default=str))
    elif args.coach:
        print(render_coach(review))
    elif args.year:
        print(render_wrapped(review, args.year))
    else:
        print(render_terminal(review, previous=previous))
    if not args.blame:
        save_current(progress_key, review)
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            content = render_markdown(review)
            if args.coach:
                content += "\n" + render_coach_markdown(review)
            f.write(content)
        print(f"Full review written to {args.md}")
    if args.html:
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(render_html(review))
        print(f"Report card written to {args.html}")
    if args.svg:
        with open(args.svg, "w", encoding="utf-8") as f:
            f.write(render_wrapped_svg(review, args.year) if args.year else render_svg(review))
        print(f"SVG report card written to {args.svg}")
    if args.share:
        with open(args.share, "w", encoding="utf-8") as f:
            f.write(render_share_svg(review))
        print(f"Share card (1200x630) written to {args.share}")
        print(f"Post text: My git history just put me on a Performance Improvement Plan. "
              f"Grade: {review.overall_letter} ({review.overall_score:.0f}/100). "
              f"Get yours: pip install on-a-pip")
    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)
        artifacts = {
            "review.md": render_markdown(review),
            "report-card.html": render_html(review),
            "report-card.svg": render_wrapped_svg(review, args.year) if args.year else render_svg(review),
            "badge.svg": render_badge(review),
            "reference.md": render_reference(review),
            "review.json": json.dumps(review_to_json(review), indent=2, default=str),
        }
        for fname, content in artifacts.items():
            with open(os.path.join(args.outdir, fname), "w", encoding="utf-8") as f:
                f.write(content)
        print(f"All artifacts written to {args.outdir}")
    if args.badge:
        with open(args.badge, "w", encoding="utf-8") as f:
            f.write(render_badge(review))
        print(f"Badge written to {args.badge}")
    if args.reference:
        with open(args.reference, "w", encoding="utf-8") as f:
            f.write(render_reference(review))
        print(f"Reference letter written to {args.reference}")
    if args.readme:
        try:
            readme_path, card_path, badge_path = update_readme(repo, review)
        except PipError as e:
            print(f"on-a-pip: {e}", file=sys.stderr)
            return 2
        print(f"README review section updated in {readme_path}")
        print(f"Card and badge written to {card_path} and {badge_path}")
        if clone_root and not args.keep:
            print("Note: that was a temporary clone, so the README changes went with it. "
                  "Re-run with --keep, or run --readme inside your own checkout.", file=sys.stderr)
    if review.total_commits < 10:
        print("Note: fewer than 10 commits reviewed. Management is extrapolating, "
              "the way management does.", file=sys.stderr)
    if args.fail_below:
        rank = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
        if rank[review.overall_letter] < rank[args.fail_below]:
            print(f"on-a-pip: grade {review.overall_letter} is below the required "
                  f"{args.fail_below}. The gate has spoken.", file=sys.stderr)
            return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
