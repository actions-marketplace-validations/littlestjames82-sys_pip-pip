# Changelog

All notable changes to PIP (PyPI: `on-a-pip`) are recorded here. Versions are
the tool's own; the record is the record.

## 1.4.1 (Nov 24, 2026)

- **GitHub Marketplace release.** The PIP Review Action is published to
  GitHub Marketplace, pinned the normal way as
  `littlestjames82-sys/pip-pip@v1` instead of `@main`. `action.yml` gains
  Marketplace branding (award icon, purple). The README Action docs are
  rewritten: an inputs table for `author` and `persona`, the
  commit-and-push contract (why a workflow needs `contents: write` and
  `fetch-depth: 0`), and a report-only pull request example that posts
  the review to the run summary instead of committing anything.
  `examples/monthly-profile-review.yml` is fixed: it passed an input the
  Action does not define, and re-committed files the Action already
  commits itself. A `.pre-commit-hooks.yaml` is included, for running PIP
  as a pre-commit hook. The README also gains a PyPI downloads badge and
  an Also from Ghost Developer Studio section. The review engine is
  unchanged from 1.4.0: same grades, same flags, and reviews of record
  reproduce exactly as before.

## 1.4.0 (Nov 20, 2026)

- **Authorship badge.** The 1.3.0 authorship check becomes a badge a
  README can carry: `render_authorship_badge` draws a shields-style SVG
  ("authorship" / "94% self-authored") next to the grade badge. The
  percent rounds half up on the exact commit fraction, and the color
  follows the true share: bright green at 90% and up, through yellow
  green, yellow, and orange, down to red under 10%. A mostly inherited
  history says so instead, in red, whatever the share; a review with no
  authorship data reads "no data" in grey. `--authorship-badge FILE`
  writes the SVG, `--authorship-badge-json FILE` writes the shields.io
  endpoint JSON for anyone who would rather let shields render it, and
  `--readme` now writes `pip-authorship-badge.svg` into the repo and
  adds its image line to the PIP section, right under the grade badge.
  The `--json` output gains an additive `authorship_badge` key with the
  same message and colors, so the SVG, the endpoint, and the JSON can
  never disagree. Nothing else changes: reviews of record reproduce
  exactly as before.

## 1.3.0 (Nov 20, 2026)

- **Authorship check.** Every review gains an Authorship section (terminal,
  Markdown, HTML card, and JSON): the reviewed author's share of the
  history's commits, the other authors ranked, the history's start against
  the author's first commit, and how much of the record predates them.
  When the share is at most 10% and at least half the history was written
  by others before the author's first commit (in a history of 20+
  commits), the report flags it: "Authorship: mostly inherited." That is
  the shape of a rebranded fork, and the review now says so instead of
  quietly grading somebody else's work. Identities cluster by email with
  mailmap applied, and name variants ("Timothy Carambat" /
  "timothycarambat") merge into one author. The check is descriptive
  only: no score, grade, or award changes, and reviews of record
  reproduce exactly as before.

## 1.2.0

- `--wrapped-kit DIR`: a share kit for the year. Writes the Wrapped card
  (SVG) and a post.txt with two ready-to-post drafts (a short one sized
  for X, a standard one for LinkedIn/Facebook), built from your own
  numbers. Implies `--year` for the current year when none is given.
- Org mode is usable on big accounts now: each repo prints a progress
  line to stderr as it is reviewed, and `--shallow N` is honored by org
  clones, so a huge repository no longer means a long silent wait.

## 1.1.1

- Org mode repaired: `--org` crashed with a NameError once it got past the
  GitHub listing step (two imports lived only inside other functions). It
  now runs end to end, verified live, with a regression test that drives
  the whole org flow against a local repository.
- Org reviews now record file paths for every commit, not just the ones
  with line counts, so path-based awards score the same as in a local
  review.
- README badges: PyPI version, test status, supported Pythons, license.

## 1.1.0: The Fuller File

- Progress line on stderr for large histories (2,000+ commits), so a big
  review never looks hung.
- Gallery doubled: FastAPI, Vue, Prettier, and Tokio join Requests, Flask,
  Express, and normalize.css.
- Three new sample persona packs: Drill Sergeant, The Therapist, The VC.
  The persona pack format is documented and frozen as v1 in
  [personas/README.md](personas/README.md).
- New examples: a Requests leaderboard, a head-to-head (Reitz vs Benfield),
  and a letter of reference.
- Fixed `tools/make_gallery.py`, which had been carrying a mangled block
  since the 0.8 plumbing change. The gallery is regenerated.
- Bot detection now also catches `-bot`/`_bot` suffixed names (vue-bot
  topped the Vue board before this). Surnames like Talbot and Abbot are
  explicitly not bots, and are regression-tested as such.
- Fixed a leaderboard bug the regenerated gallery exposed: when two
  identities shared a display name and one was name-keyed (no email), the
  board could show the larger identity twice. Boards now target identities
  by their exact group key. Regression-tested.

## 1.0.1

- Fixed `clone_label` mangling repo names from Windows-style `file://`
  paths. Found by the new Windows CI leg within an hour of it existing.

## 1.0.0: The Front Door

- Fair by default: bot authors excluded (`--include-bots` restores them),
  Co-authored-by trailers earn shared credit, lockfiles and minified files
  no longer count as churn, squash-merge-heavy histories carry an
  authorship note.
- `--tz` grades in the author's timezone. `--branch` and `--path` narrow
  the record.
- `--share` writes the 1200x630 share card. `--csv` prints boards as CSV.
- "Not for employment decisions" on every artifact. The AI branding is
  gone: PIP is plain arithmetic and says so.
- README rebuilt around the verdict card. Windows and macOS CI legs.
- First GitHub releases; project site at
  https://littlestjames82-sys.github.io/pip-pip/

## 0.9.0: The Org Chart

- `--org` GitHub-user boards, pair stats on leaderboards, persona packs
  (`--persona-file`) with Pirate Captain and Noir Detective samples, a
  scheduled monthly-review Action example.

## 0.8.0: The Personnel File

- `--history` grade trend, `--coach` four-week drills, `--blame` single-file
  reviews, `.pip.toml` repo config, award wave 2 (Merge Goblin, Lone Wolf,
  Rubber Duck, The Archaeologist; 21 total).

## 0.7.0

- `--year` PIP Wrapped, hall-of-fame stats, commits-per-month bars on the
  card, `--fail-below` CI gate, `--outdir` full artifact set, `--top`.

## 0.6.0

- `--vs` head-to-head, `--scan` folder mode, `.mailmap` support, `--quarter`.

## 0.5.1

- Fixed reviews silently emptying on Python 3.9/3.10 when git emits UTC
  dates with a `Z` suffix.

## 0.5.0

- `--readme` mode (card, badge, marked README section), reusable GitHub
  Action, self-review workflow.

## 0.4.0

- Identity grouping by email, career stats, five new awards, `--reference`
  letter of reference, `--since`/`--until`.

## 0.3.0

- Review any public repo by URL or GitHub shorthand.

## 0.2.0

- 12-award system, four manager personas, `--leaderboard`, `--days`, SVG
  report card and README badge, nemesis file, progress tracking.

## 0.1.0

- The first review: five graded categories, evidence, a 30-day plan,
  terminal summary, Markdown review, HTML report card, `--json`.
