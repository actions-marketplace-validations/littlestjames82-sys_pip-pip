#!/usr/bin/env python3
"""PIP - the Performance Improvement Plan for programmers.

Every AI tool reviews your code. PIP reviews *you*.

PIP reads a developer's own git history (locally, read-only, nothing is
uploaded anywhere) and issues a formal, manager-style performance review
with evidence: commit-message quality, late-night and Friday-afternoon
habits, reverts, fix chains, TODOs left to grow old, and "temporary" hacks
that quietly became permanent.

Pure Python standard library. No dependencies, no accounts, no network.

    pip install pip-pip
    pip-pip                  # review the top author of the repo in cwd
    pip-pip ~/some/repo --md review.md --html card.html
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

__version__ = "0.1.0"

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


def collect_numstat(repo: str, shas: set[str], cap: int = 5000) -> dict[str, tuple[int, int, int]]:
    """Map sha -> (added, deleted, files). Capped for very large histories."""
    out = _git(repo, ["log", f"--max-count={cap}", "--numstat", "--format=%H"])
    stats: dict[str, tuple[int, int, int]] = {}
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
    return stats


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


def analyze(repo: str, commits_in: list[Commit], markers: list[Marker],
            author_filter: str | None, today: date) -> Review:
    # Pick the employee: explicit filter, else the most prolific author.
    by_author: dict[str, list[Commit]] = {}
    for c in commits_in:
        by_author.setdefault(c.author, []).append(c)
    if author_filter:
        matches = {a: cs for a, cs in by_author.items()
                   if author_filter.lower() in a.lower()}
        if not matches:
            raise PipError(f"no commits found for author matching '{author_filter}'")
        author, commits = max(matches.items(), key=lambda kv: len(kv[1]))
    else:
        author, commits = max(by_author.items(), key=lambda kv: len(kv[1]))
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

    highlights: dict[str, object] = {
        "night_commits": len(night), "friday_late": len(friday_late),
        "reverts": len(reverts), "fixes": len(fixes), "vague": len(vague),
        "todos": len(todos), "oldest_todo_days": oldest_todo_days,
        "temps": len(temps), "oldest_temp_days": oldest_temp_days,
        "active_days": len(active_days), "span_days": span_days,
        "longest_streak": longest, "longest_gap": longest_gap,
        "added": sum(c.added for c in commits), "deleted": sum(c.deleted for c in commits),
    }
    return Review(
        repo_name=os.path.basename(os.path.abspath(repo)) or repo,
        author=author, review_date=today,
        span_start=active_days[0], span_end=active_days[-1],
        total_commits=total,
        categories=[comm, rel, ft, jud, con],
        highlights=highlights,
    )


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

def render_terminal(review: Review) -> str:
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
    lines.append(f"  {VERDICTS[review.overall_letter]}")
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
    out.append(f"*{VERDICTS[review.overall_letter]}*")
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
    out.append("")
    out.append("## 30-day improvement plan")
    out.append("")
    out.append("The following actions address the lowest-scoring areas. "
               "Progress will be assessed by re-running this review, which is to say, "
               "by the record itself.")
    for name, actions in build_plan(review):
        out.append("")
        out.append(f"### {name}")
        for i, a in enumerate(actions, 1):
            out.append(f"{i}. {a}")
    out.append("")
    out.append("## Sign-off")
    out.append("")
    out.append("By continuing to commit, the employee acknowledges receipt of this plan. "
               "Appeals may be filed by improving the record.")
    out.append("")
    out.append("Signed,  ")
    out.append("**Management**  ")
    out.append("*PIP - pip install pip-pip*")
    out.append("")
    return "\n".join(out)


GRADE_COLORS = {"A": "#1d9e62", "B": "#5da423", "C": "#d9a400", "D": "#e07b24", "F": "#d43a2f"}


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
  <div class="verdict">"{VERDICTS[review.overall_letter]}"</div></div>
{rows}
  <div class="foot">Generated locally by PIP from the employee's own git history. Nothing was uploaded.<br>
  pip install pip-pip</div>
</div></body></html>
"""


def review_to_json(review: Review) -> dict:
    return {
        "tool": "pip-pip", "version": __version__,
        "repo": review.repo_name, "author": review.author,
        "review_date": review.review_date.isoformat(),
        "period": [review.span_start.isoformat(), review.span_end.isoformat()],
        "total_commits": review.total_commits,
        "overall": {"letter": review.overall_letter, "score": round(review.overall_score, 1)},
        "categories": [
            {"name": c.name, "letter": c.letter, "score": round(c.score, 1), "evidence": c.evidence}
            for c in review.categories
        ],
        "highlights": {k: v for k, v in review.highlights.items()},
    }


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="pip-pip",
        description="PIP: a formal performance review of the programmer, "
                    "generated locally from their own git history.")
    ap.add_argument("repo", nargs="?", default=".", help="path to a git repository (default: current directory)")
    ap.add_argument("--author", help="review only commits by authors matching this text (default: most prolific author)")
    ap.add_argument("--max-commits", type=int, default=10000, help="cap on commits examined (default 10000)")
    ap.add_argument("--md", metavar="FILE", help="write the full review as Markdown")
    ap.add_argument("--html", metavar="FILE", help="write the shareable report card as HTML")
    ap.add_argument("--json", action="store_true", help="print the review as JSON instead of the summary")
    ap.add_argument("--version", action="version", version=f"pip-pip {__version__}")
    args = ap.parse_args(argv)

    repo = os.path.abspath(args.repo)
    try:
        inside = _git(repo, ["rev-parse", "--is-inside-work-tree"], check=False).strip()
        if inside != "true":
            raise PipError(f"{args.repo} is not a git repository")
        commits = collect_commits(repo, args.max_commits)
        if not commits:
            raise PipError("this repository has no commits yet. Management cannot review potential.")
        stats = collect_numstat(repo, {c.sha for c in commits})
        for c in commits:
            if c.sha in stats:
                c.added, c.deleted, c.files = stats[c.sha]
        markers = collect_markers(repo)
        review = analyze(repo, commits, markers, args.author, date.today())
    except PipError as e:
        print(f"pip-pip: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError:
        print("pip-pip: git was not found on this machine", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(review_to_json(review), indent=2, default=str))
    else:
        print(render_terminal(review))
    if args.md:
        with open(args.md, "w", encoding="utf-8") as f:
            f.write(render_markdown(review))
        print(f"Full review written to {args.md}")
    if args.html:
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(render_html(review))
        print(f"Report card written to {args.html}")
    if review.total_commits < 10:
        print("Note: fewer than 10 commits reviewed. Management is extrapolating, "
              "the way management does.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
