# PIP: your git history just put you on a Performance Improvement Plan

PIP is a free, MIT-licensed tool by Ghost Developer Studio (https://ghostdeveloperstudio.com/pip/) that writes a formal performance review of a programmer from their own git history, entirely on their own machine. Pure Python, zero dependencies.

[![PyPI](https://img.shields.io/pypi/v/on-a-pip)](https://pypi.org/project/on-a-pip/)
[![Tests](https://github.com/littlestjames82-sys/pip-pip/actions/workflows/tests.yml/badge.svg)](https://github.com/littlestjames82-sys/pip-pip/actions/workflows/tests.yml)
[![Python](https://img.shields.io/pypi/pyversions/on-a-pip)](https://pypi.org/project/on-a-pip/)
[![License: MIT](https://img.shields.io/github/license/littlestjames82-sys/pip-pip)](LICENSE)
[![Downloads](https://static.pepy.tech/badge/on-a-pip)](https://pepy.tech/project/on-a-pip)

Every tool reviews your code. **PIP reviews the programmer.**

![PIP in action: install, run, verdict](examples/demo.gif)

![PIP report card](examples/sample-report-card.svg)

No AI, no models, no uploads: PIP is one Python file of plain arithmetic that reads your
local git history and issues a formal manager-style performance review of the person who
wrote it. Grades, evidence, awards, and a 30-day improvement plan. It is a novelty that
takes its evidence seriously, and it is **not for employment decisions**: it grades a
commit record, not a person, and it reads best when the reader is the author.

Every developer keeps a work diary without knowing it: their git history. Every change is in there, with a timestamp and a little note that was supposed to explain it. PIP reads that record, locally, on your own machine, and issues a formal manager-style performance review. With evidence.

```
pip install on-a-pip
```

(or keep it isolated: `pipx install on-a-pip`. The project site lives at https://littlestjames82-sys.github.io/pip-pip/)

Then, inside any git repository:

```
on-a-pip
```

Or see how a famous project's record grades out, straight from the internet:

```
on-a-pip psf/requests                      # GitHub shorthand
on-a-pip https://github.com/psf/requests    # any git URL
on-a-pip psf/requests --leaderboard        # rank the whole team
```

PIP clones the repo into a temp folder, reviews it, and deletes the clone when it is done (`--keep` keeps it, `--shallow 500` fetches only recent history on huge repos). Reviewing a famous project is an education: the creator of Requests grades out at a D with a Night Owl award, and his record splits into two leaderboard rows because he committed under two email addresses and the project has no mailmap to merge them. PIP counts identities the way git does. The record is the record.

```
  PERFORMANCE IMPROVEMENT PLAN  -  Dev Example
  pip-sample  |  8 commits reviewed  |  2025-10-14 to 2026-11-08
  --------------------------------------------------------------
  Communication    F    32.5  ######
  Reliability      C    64.4  ############
  Follow-through   B    84.3  ################
  Judgment         B    83.8  #################
  Consistency      D    43.0  ########
  --------------------------------------------------------------
  OVERALL          C    61.6
  Meets some expectations. There is a conversation to be had.
```

(That is a real review of a deliberately terrible sample history. Yours will be different. Possibly worse.)

## What it grades

- **Communication.** How many of your commit messages actually say anything. "stuff", "wip" and "asdf" are entered into the record, quoted back at you.
- **Reliability.** Commits between 10pm and 5am. Commits shipped Friday after 4pm. Reverts. Chains of commits that start with "fix".
- **Follow-through.** The TODOs still sitting in your code, and how old the oldest one is. A TODO that has been waiting 400 days has seniority.
- **Judgment.** The spots labelled "temporary", "hack" or "workaround", and how long the oldest one has been load-bearing.
- **Consistency.** Active days versus silent stretches, longest streak, longest disappearance.

Then it does what any good PIP does: it writes you a **30-day improvement plan**, generated from your three weakest categories, and signs off with the only appeal process that has ever worked: improve the record.

## Awards

Grades are the paperwork. Awards are the part people post. PIP reads your habits and hands out titles, each one earned by the record:

- **Night Owl** - a quarter or more of your commits land between 10pm and 5am
- **Friday Gambler** - repeated Friday-after-4pm shipping
- **Demolitionist** - you delete more than you add, at scale
- **The Ghost** - a 60+ day disappearance, then a casual return
- **Fossil Keeper** - a TODO old enough to qualify for the pension plan
- **Surgeon**, **Streak Keeper**, **Open Book**, **Strong Silent Type**, **Chaos Agent**, **Weekend Warrior**, **Colourful Commentator**
- **Marathon Day** (15+ commits in one day), **The Purge** (a single commit deleting 1,000+ lines), **Polyglot** (real churn in 5+ languages), **Old Faithful** (3+ years on one codebase), **Phoenix** (a long disappearance followed by a genuine comeback)

It also names your **nemesis file** (the one with the most churn in your history) and your largest single commit, because management did the reading.

## Choose your manager

```
on-a-pip --persona brutal       # the startup CTO
on-a-pip --persona supportive   # the kind lead
on-a-pip --persona passive      # the passive-aggressive middle manager
on-a-pip --persona corporate    # the default. HR is present.
```

The evidence never changes. The tone absolutely does.

## More ways to be reviewed

```
on-a-pip ~/some/repo --md review.md --html card.html --svg card.svg --badge badge.svg
on-a-pip --author "your name"     # review one author (default: the most prolific)
on-a-pip --days 90                # just the last 90 days of history
on-a-pip --since 2026-01-01 --until 2026-03-31   # or a calendar window
on-a-pip --reference letter.md    # also write a letter of reference, based on the grade
on-a-pip --vs "Alice" "Bob"       # head to head: two authors, one repo, one winner
on-a-pip --scan ~/projects        # review the top author of every repo in a folder
on-a-pip --quarter                # the quarterly ritual: last 90 days, compared to your last review
on-a-pip --year 2026              # PIP Wrapped: your year in commits, as a shareable edition
on-a-pip --outdir ./my-review     # write every artifact at once: review, cards, badge, reference, JSON
on-a-pip --fail-below B           # exit code 3 if the grade is worse than B (a CI gate, serious or otherwise)
on-a-pip --history                # your grade trend across every saved review of this repo
on-a-pip --coach                  # coaching mode: a four-week drill plan instead of a verdict
on-a-pip --blame app.py           # a performance review for one file: every commit that touched it
on-a-pip --org psf                # org board: the top author of a GitHub user's public repos
on-a-pip --share card.svg         # the 1200x630 share card, sized for social posts
on-a-pip --tz Europe/Berlin       # grade in your timezone, not the server's
on-a-pip --branch main --path src # narrow the record: one branch, one corner of the tree
on-a-pip --persona-file noir.json # bring your own manager: a custom persona pack
on-a-pip --leaderboard            # review every author in the repo and rank them
on-a-pip psf/requests               # or skip the local part entirely: any public repo by URL
on-a-pip --json                   # machine-readable review
```

- The terminal summary above, now with awards, and a progress line comparing you to your last review (PIP remembers, locally).
- A full formal review in Markdown: per-category evidence, management notes, additional findings, awards, the plan, the sign-off.
- Shareable **report cards** in HTML and **SVG** (the SVG embeds straight into a README), plus a small **grade badge** for your profile.
- A **leaderboard mode** for shared repos. Run it on your team. We accept no responsibility for the standup that follows.
- A **letter of reference** (`--reference`), written by management in the tone your grade deserves. A grades get a glowing letter. F grades get a short one.
- Career stats in every review: busiest day ever, monthly activity sparkline, languages ranked by churn. Identities are grouped by email, so one person under two names is one employee, and two people sharing a name stay two rows.
- **Head-to-head mode** (`--vs`): two authors compared category by category, with a declared winner and consequences for the loser.
- **Folder scan** (`--scan`): point PIP at a directory of projects and get one ranked board of every repo's top author.
- **Mailmap support:** if the repo has a `.mailmap`, PIP honors it, so identity merging follows the project's own records.
- **PIP Wrapped** (`--year`): the year-in-commits edition, with its own dark Wrapped card: busiest month, top award, your catchphrase. `--wrapped-kit DIR` packages the card with ready-to-post text in two lengths, built from your numbers.
- **Hall of fame stats:** longest commit message (the novel), shortest (the haiku), and your catchphrase, the word your subjects cannot stop using.
- Report cards chart your commits per month; `--outdir` writes the full artifact set in one run; `--fail-below` turns a grade into a CI gate.
- **History** (`--history`): every review is saved locally, so your grade becomes a trend line with bars, not a one-off verdict.
- **Coaching mode** (`--coach`): four weeks of drills aimed at your three weakest categories, each with a measurable check.
- **File reviews** (`--blame`): one file, every commit that ever touched it, formally reviewed.
- **Repo config:** a `.pip.toml` in the repo root can set `persona` and `fail_below` once for the whole team; the command line still wins.
- 21 awards now, including The Archaeologist (revives files untouched for a year), Merge Goblin, Lone Wolf, and Rubber Duck (commit bodies longer than some READMEs).
- **Org boards** (`--org`): point PIP at any GitHub user and get one ranked board across their public repos, with an Org MVP. Each repo is cloned in turn, so large repositories take a while; `--org-limit` keeps it quick.
- **Fair records by default:** bot authors (dependabot and friends) are excluded unless you ask for them with `--include-bots`; Co-authored-by trailers earn shared credit; lockfiles and minified files do not count as churn; squash-merge-heavy histories carry an authorship note saying the grade belongs to whoever pressed the merge button.
- **Authorship check:** every review now reports how much of the history is actually the reviewed author's: their share of commits, who wrote the rest, and when they arrived relative to the record. When the pattern matches a rebranded fork (a small share, with the bulk of the history written by others before their first commit), the report says so plainly: "Authorship: mostly inherited." The check is descriptive only; it never changes a grade.
- **Boards export:** `--csv` prints leaderboard, scan, and org boards as CSV; `--json` covers every mode.
- **Pair stats:** the leaderboard now names the pair most in sync, ranked by shared active days.
- **Persona packs:** six managers built in (Corporate, Startup CTO, Supportive Lead, Passive-Aggressive Middle Manager, Pirate Captain, Noir Detective), and `--persona-file` loads your own from a small JSON pack. Two sample packs live in `personas/`.
- A scheduled monthly profile-review Action example lives in `examples/`.

## Examples

The report card:

![Sample report card](examples/sample-report-card.svg)

The 1200x630 share card (`--share`):

![Sample share card](examples/sample-share-card.svg)

PIP Wrapped, the year in commits (`--year`):

![Sample Wrapped card](examples/sample-wrapped.svg)

The full written review is in [examples/sample-review.md](examples/sample-review.md), a rendered HTML card in [examples/report-card-decksmith.html](examples/report-card-decksmith.html), a real leaderboard in [examples/sample-leaderboard.md](examples/sample-leaderboard.md), a head-to-head in [examples/sample-versus.md](examples/sample-versus.md), and a letter of reference in [examples/sample-reference.md](examples/sample-reference.md). The demo GIF above is rendered from the tool's real output by [tools/make_demo_gif.py](tools/make_demo_gif.py).

## The gallery

Famous projects, formally reviewed: [the PIP Gallery](gallery/) has real report cards and
leaderboards for Requests, Flask, Express, and normalize.css, all generated by PIP itself.

Sample outputs live in [`examples/`](examples/): a full sample review, sample report cards, a badge, and a real report card generated from the Decksmith repository.

## Wear your grade

```
on-a-pip --readme
```

Run inside your repo, this writes `pip-card.svg` and `pip-badge.svg` and adds a marked **My PIP review** section to your README (the one at the bottom of this README is PIP reviewing this repo). Re-run it any time to refresh the grade.

To keep it current automatically, use the GitHub Action in your workflow. The Action has two inputs and no outputs; its whole job is to edit and commit files:

| Input | Required | Default | What it does |
| --- | --- | --- | --- |
| `author` | no | *(most prolific author)* | Git author to review, matched against the names in your history. |
| `persona` | no | `corporate` | The reviewing manager's style, as described in `action.yml`: `corporate`, `brutal`, `supportive`, or `passive`. |

It installs `on-a-pip` from PyPI, runs `on-a-pip . --readme` in the checked-out repo, and commits any changes to `README.md`, `pip-card.svg`, and `pip-badge.svg` straight back to the branch it ran on. That commit-and-push design is why the workflow needs `contents: write` and a full clone:

```yaml
name: pip-review
on:
  push:
    branches: [main]
permissions:
  contents: write
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: littlestjames82-sys/pip-pip@v1
        with:
          persona: corporate
          # author: "your name"   # omit to review the most prolific author
```

Every push gets a fresh review, committed by the bot. Your README becomes a living performance record, which is either motivating or a threat, depending on your habits. A ready-made monthly variant for a GitHub profile README lives in [`examples/monthly-profile-review.yml`](examples/monthly-profile-review.yml).

### Grade a contributor on a pull request

Do not point the Action above at a pull request: it commits and pushes, and pull-request tokens (especially from forks) are read-only. For a PR, run the same engine in report-only mode instead. This workflow grades the PR's most recent commit author, posts the full review to the run summary (visible from the PR's Checks tab), and uploads the report card as an artifact:

```yaml
name: pip-review-pr
on:
  pull_request:
permissions:
  contents: read
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install PIP
        run: pip install on-a-pip
      - name: Review the PR author
        run: |
          AUTHOR="$(git log -1 --format=%an)"
          echo "Reviewing git author: $AUTHOR"
          on-a-pip . --author "$AUTHOR" --md pip-review.md --svg pip-card.svg
          cat pip-review.md >> "$GITHUB_STEP_SUMMARY"
      - name: Upload the report card
        uses: actions/upload-artifact@v4
        with:
          name: pip-report-card
          path: |
            pip-review.md
            pip-card.svg
```

Notes on the PR version:

- `git log -1 --format=%an` takes the author name from the PR's latest commit, which is exactly the name PIP matches on. For a PR with several authors, drop the `--author` flag and PIP reviews the most prolific author in the history it can see.
- Nothing is committed and nothing is pushed, so it works on fork PRs with the default read-only token.
- If you do want the card committed onto a same-repo PR branch instead, check out the PR's head branch (`ref: ${{ github.head_ref }}`), give the job `contents: write`, and use the Action from the first example. That does not work for forks.

## Performance

Measured on a modest cloud VM with PIP 1.1, full reviews including line counts:

- **psf/requests:** 6,495 commits reviewed in about **2 seconds**.
- **django/django:** the default 10,000-commit window in about **35 seconds**; the full 35,128-commit history (`--max-commits 40000`) in about the same, because most of the time is git reading line counts and grepping a very large tree, not the grading.

Histories over 2,000 commits print a progress line instead of sitting silent. For a huge repo you only need the recent record from, `--shallow N` on a URL target reviews just that slice.

## Private by construction

PIP runs `git log`, `git grep` and `git blame` on your machine and nothing else. No network, no account, no API key, no telemetry, pure Python standard library. Your history is embarrassing enough without uploading it somewhere.

## Requirements

- Python 3.9+
- git, on your PATH

## Honest notes

- The package is called `on-a-pip` because PyPI rejected `pip-pip` as too similar to `pip` itself, which is fair: you do not get to out-pip pip. The tool was going to be `pip install pip-pip`. Now you install the news that you are on one.
- Grades are deterministic: same history, same review. The formulas are plain arithmetic in one file, `pip_pip.py`, if you want to argue with them.
- PIP reviews the most prolific author in the repo by default. Use `--author` in shared repos.

## Also from Ghost Developer Studio

- **Snap Judgment**: judges your screenshots folder from file metadata only, with a courtroom verdict. `pip install snap-judgment`
- **Dead Projects Society**: builds a graveyard for your abandoned git projects, tombstones and all. `pip install dead-projects-society`
- **Ghost Hands**: governed browser automation for AI agents, with every action classified, policy checked, and trailed. `pip install ghost-hands`
- **Agent Seatbelt**: guardrails for AI coding agents, gating tool calls before they run. `pip install ghost-seatbelt`

## License

MIT. Built by [Ghost Developer Studio](https://ghostdeveloperstudio.com).

<!-- pip:start -->
## My PIP review

![My PIP grade](pip-badge.svg)

![Authorship](pip-authorship-badge.svg)

![PIP report card](pip-card.svg)

**Grade: C (73/100)** · 37 commits reviewed · Top award: Night Owl · Reviewed 2026-11-23

*This section is maintained by [PIP](https://pypi.org/project/on-a-pip/) (`on-a-pip --readme`). The record speaks for itself.*
<!-- pip:end -->
