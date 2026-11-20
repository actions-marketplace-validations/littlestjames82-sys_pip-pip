# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Alex Crichton  
**Project reviewed:** tokio  
**Review period:** 2016-07-30 to 2018-03-09  
**Commits examined:** 357  
**Review date:** 2026-11-19  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: C (59/100)

*Meets some expectations. There is a conversation to be had.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Authorship

- **Share of the record:** 357 of 4879 commits in this history (7%) are by Alex Crichton. The remaining 4522 are by 1094 other authors.
- **Most of the rest:** Alice Ryhl (714 commits), Carl Lerche (649 commits), Taiki Endo (172 commits).
- **Arrival:** the history starts 2016-07-30; Alex Crichton's first commit is 2016-07-30, and 0 commits predate it.
- **Authorship: no concerns.** This record is substantially the reviewed author's own work, as a review assumes.

## Communication: A (100/100)

- 2 of 357 commit messages (1%) say almost nothing (average message length: 36 characters).
- Entered into the record: "Fix tests", "Typo".
- 172 of 357 commits (48%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: A (93/100)

- 45 of 357 commits (13%) were made between 10pm and 5am.
- 11 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 0 commits are reverts (0%) and 15 (4%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (20/100)

- 87 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 3356 days (9.2 years). It has seniority now.
- Senior TODO on file: examples/tinyhttp.rs:153 - "// TODO: we should grow this headers array if parsing fails and asks"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (22/100)

- 72 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 2309 days. It is not temporary. It is load-bearing.
- 0 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: C (61/100)

- Active on 153 of 588 days in the review period (26%).
- Longest streak: 7 days. Longest disappearance: 34 days.
- Average output on an active day: 2.3 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** tokio-trace/src/macros.rs - 6,790 lines of churn across the review period. You two have history.
- **Largest single commit:** 2,364 lines changed in "Reorganize the `event_loop` module". A bold unit of work.
- **Weekend work:** 46 of 357 commits landed on a Saturday or Sunday.
- **Busiest day:** 2016-09-07, with 16 commits.
- **Languages by churn:** Rust (642,076 lines of churn), Markdown (18,003 lines of churn), toml (9,824 lines of churn), YAML (9,291 lines of churn).
- **Longest commit message:** "Merge branch 'aphs-core-stream' of https://github.com/aidanhs/tokio-core" (72 characters. A novel.)
- **Shortest commit message:** "Typo". A haiku, if you squint.
- **Catchphrase:** "merge", appearing 98 times across your commit subjects.
- **Net lines:** 18,593 added, 9,624 deleted.

## Awards

- **Friday Gambler:** 11 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **Streak Keeper:** 7 active days in a row at the longest stretch. Showing up is a skill.
- **Fossil Keeper:** A TODO has survived 3356 days in the code. It qualifies for the pension plan.
- **Marathon Day:** 16 commits in a single day (2016-09-07). Somewhere in there was a lunch break. Probably.
- **The Purge:** One commit deleted 1,325 lines. Witnesses described the diff as 'mostly red'.
- **Polyglot:** Meaningful churn in 9 languages. Jack of all trades, suspect in all of them.
- **Merge Goblin:** 98 of 357 commits are merges. Somewhere upstream, a rebase weeps quietly.

## 30-day improvement plan

The following actions address the lowest-scoring areas. Progress will be assessed by re-running this review, which is to say, by the record itself.

### Follow-through
1. Pick the five oldest TODOs. Close them, convert them to tracked issues, or delete them and own the decision.
2. New rule: a TODO without a date and a name is litter. Date and name, every time.
3. One TODO closed per week, minimum, until the backlog is younger than you are.

### Judgment
1. Every 'temporary' fix gets an expiry date in the comment. When the date passes, it gets reviewed first, not last.
2. Count the hacks monthly. The number going down is the goal; the number existing is not the shame.
3. No new workaround merges without a note explaining what the real fix would take.

### Consistency
1. Small and daily beats heroic and monthly. Protect the streak, shorten the silences.
2. End each session by leaving the next step written down, so returning is easy.
3. If a gap is coming (holiday, life), say so in a commit. Silence reads worse than absence.

## Sign-off

By continuing to commit, the employee acknowledges receipt of this plan. Appeals may be filed by improving the record.

Signed,  
**Management**  
*PIP - pip install on-a-pip*

*Not for employment decisions. PIP grades a commit record, not a person, and it reads best when the person reading it is the person who wrote the commits.*
