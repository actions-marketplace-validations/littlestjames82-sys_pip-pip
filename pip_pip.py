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
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

__version__ = "0.5.0"

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
    name = name.split("/")[-1].split(":")[-1]
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name) or "repo"


def clone_repo(url: str, shallow: int | None = None) -> tuple[str, str]:
    """Clone into a fresh temp dir. Returns (repo_path, temp_root)."""
    import shutil
    import tempfile
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


@dataclass
class Marker:
    kind: str               # TODO / FIXME / HACK / TEMP ...
    path: str
    line: int
    text: str
    born: date | None       # date the line was introduced (blame), if known


def collect_commits(repo: str, max_commits: int) -> list[Commit]:
    fmt = FS.join(["%H", "%an", "%ae", "%aI", "%s", "%b"]) + RS
    out = _git(repo, ["log", f"--max-count={max_commits}", f"--format={fmt}"])
    commits: list[Commit] = []
    for rec in out.split(RS):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        parts = rec.split(FS)
        if len(parts) < 6:
            continue
        sha, author, email, iso, subject, body = parts[0], parts[1], parts[2], parts[3], parts[4], FS.join(parts[5:])
        try:
            when = datetime.fromisoformat(iso)
        except ValueError:
            continue
        commits.append(Commit(sha=sha, author=author, email=email, when=when,
                              subject=subject.strip(), body=body.strip()))
    return commits


def collect_numstat(repo: str, shas: set[str], cap: int = 5000):
    """Return (per-commit stats, per-file totals).

    Per-commit: sha -> (added, deleted, files).
    Per-file: path -> (added, deleted, commits_touched).
    Capped for very large histories.
    """
    out = _git(repo, ["log", f"--max-count={cap}", "--numstat", "--format=%H"])
    stats: dict[str, tuple[int, int, int]] = {}
    files: dict[str, tuple[int, int, int]] = {}
    current: str | None = None
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"[0-9a-f]{40}", line):
            current = line
            if current in shas:
                stats.setdefault(current, (0, 0, 0))
            continue
        if current is None or current not in shas:
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            a, d = parts[0], parts[1]
            added = int(a) if a.isdigit() else 0
            deleted = int(d) if d.isdigit() else 0
            pa, pd, pf = stats[current]
            stats[current] = (pa + added, pd + deleted, pf + 1)
            fname = parts[2]
            if " => " in fname:
                fname = fname.split(" => ")[-1].strip("{}")
            fa, fd, fc = files.get(fname, (0, 0, 0))
            files[fname] = (fa + added, fd + deleted, fc + 1)
    return stats, files


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
}


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
            persona: str = "corporate") -> Review:
    # Pick the employee: explicit filter, else the most prolific identity.
    # Identities group by email: one person under two names is one employee.
    groups = _author_groups(commits_in)
    if author_filter:
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


def _author_groups(commits_in: list[Commit]) -> list[tuple[str, list[Commit], str]]:
    """Group commits by identity: same email is the same person, whatever
    name they committed under. Returns (display name, commits, identity key)
    where the key is the email when there is one, else the name."""
    groups: dict[str, list[Commit]] = {}
    for c in commits_in:
        key = (c.email or "").strip().lower() or f"name:{c.author.strip().lower()}"
        groups.setdefault(key, []).append(c)
    result: list[tuple[str, list[Commit], str]] = []
    for key, cs in groups.items():
        names: dict[str, int] = {}
        for c in cs:
            names[c.author] = names.get(c.author, 0) + 1
        result.append((max(names.items(), key=lambda kv: kv[1])[0], cs, key))
    return result


def leaderboard(repo: str, commits_in: list[Commit], markers: list[Marker],
                today: date, file_totals=None, persona: str = "corporate",
                min_commits: int = 5, top: int = 8) -> list[Review]:
    """Review every author in the repo and rank them. The office feature."""
    ranked = sorted(((name, len(cs), key) for name, cs, key in _author_groups(commits_in)),
                    key=lambda kv: -kv[1])
    reviews: list[Review] = []
    for name, count, key in ranked[:top]:
        if count < min_commits:
            continue
        # Target the exact identity: by email when the key is one, so two
        # people who share a display name never collapse into one row.
        target = key if "@" in key else name
        try:
            reviews.append(analyze(repo, commits_in, markers, target, today,
                                   file_totals=file_totals, persona=persona))
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
{rows}{awards}
  <text x="340" y="{height - 14}" font-family="Georgia, serif" font-size="11" fill="#777" text-anchor="middle">Generated locally by PIP from the employee's own git history. pip install on-a-pip</text>
</svg>
"""


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


def render_leaderboard(reviews: list[Review], repo_name: str) -> str:
    lines = ["", f"  PIP LEADERBOARD  -  {repo_name}", "  " + "-" * 62,
             f"  {'#':<3} {'Employee':<26} {'Grade':<6} {'Score':<7} {'Commits':<8} Top award"]
    for i, r in enumerate(reviews, 1):
        award = r.awards[0][0] if r.awards else "-"
        lines.append(f"  {i:<3} {r.author[:25]:<26} {r.overall_letter:<6} {r.overall_score:<7.1f} {r.total_commits:<8} {award}")
    lines.append("  " + "-" * 62)
    lines.append("  Ranked by overall PIP score. Ties broken by whoever panics less.")
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
  <div class="foot">Generated locally by PIP from the employee's own git history. Nothing was uploaded.<br>
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
    data = {"date": review.review_date.isoformat(),
            "overall_score": round(review.overall_score, 1),
            "overall_letter": review.overall_letter,
            "author": review.author}
    try:
        with open(_progress_path(repo), "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass


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
    ap.add_argument("--persona", choices=sorted(PERSONAS), default="corporate",
                    help="the reviewing manager's style (default: corporate)")
    ap.add_argument("--leaderboard", action="store_true",
                    help="review every author in the repo and rank them")
    ap.add_argument("--md", metavar="FILE", help="write the full review as Markdown")
    ap.add_argument("--html", metavar="FILE", help="write the shareable report card as HTML")
    ap.add_argument("--svg", metavar="FILE", help="write the shareable report card as SVG (embeds in READMEs)")
    ap.add_argument("--badge", metavar="FILE", help="write a small grade badge as SVG")
    ap.add_argument("--json", action="store_true", help="print the review as JSON instead of the summary")
    ap.add_argument("--version", action="version", version=f"on-a-pip {__version__}")
    args = ap.parse_args(argv)

    progress_key = args.repo
    repo_arg = args.repo
    clone_root = None
    if is_clone_target(args.repo):
        import atexit
        import shutil
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
    try:
        inside = _git(repo, ["rev-parse", "--is-inside-work-tree"], check=False).strip()
        if inside != "true":
            raise PipError(f"{args.repo} is not a git repository")
        commits = collect_commits(repo, args.max_commits)
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
        stats, file_totals = collect_numstat(repo, {c.sha for c in commits})
        for c in commits:
            if c.sha in stats:
                c.added, c.deleted, c.files = stats[c.sha]
        markers = collect_markers(repo)
        if args.leaderboard:
            board = leaderboard(repo, commits, markers, date.today(),
                                file_totals=file_totals, persona=args.persona)
            if not board:
                raise PipError("no author has enough commits to rank yet")
            repo_name = os.path.basename(repo) or repo
            if args.json:
                print(json.dumps({"leaderboard": [review_to_json(r) for r in board]}, indent=2, default=str))
            else:
                print(render_leaderboard(board, repo_name))
            return 0
        review = analyze(repo, commits, markers, args.author, date.today(),
                         file_totals=file_totals, persona=args.persona)
    except PipError as e:
        print(f"on-a-pip: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print("on-a-pip: git was not found on this machine", file=sys.stderr)
        return 2

    previous = load_previous(progress_key)
    if args.json:
        print(json.dumps(review_to_json(review), indent=2, default=str))
    else:
        print(render_terminal(review, previous=previous))
    save_current(progress_key, review)
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(render_markdown(review))
        print(f"Full review written to {args.md}")
    if args.html:
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(render_html(review))
        print(f"Report card written to {args.html}")
    if args.svg:
        with open(args.svg, "w", encoding="utf-8") as f:
            f.write(render_svg(review))
        print(f"SVG report card written to {args.svg}")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
