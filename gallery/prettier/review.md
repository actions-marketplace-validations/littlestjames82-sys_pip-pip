# PERFORMANCE IMPROVEMENT PLAN

**Employee:** fisker Cheung  
**Project reviewed:** prettier  
**Review period:** 2022-05-28 to 2026-11-13  
**Commits examined:** 2564  
**Review date:** 2026-11-19  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: C (60/100)

*Meets some expectations. There is a conversation to be had.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Authorship

- **Share of the record:** 1930 of 2827 commits in this history (68%) are by fisker Cheung. The remaining 897 are by 281 other authors.
- **Most of the rest:** SUZUKI Sosuke (157 commits), Sosuke Suzuki (124 commits), Konv Suu (79 commits).
- **Arrival:** the history starts 2022-05-28; fisker Cheung's first commit is 2022-05-28, and 0 commits predate it.
- **Authorship: no concerns.** This record is substantially the reviewed author's own work, as a review assumes.

## Communication: A (100/100)

- 39 of 2564 commit messages (2%) say almost nothing (average message length: 45 characters).
- Entered into the record: "Fix", "Fix", "Fix".
- 797 of 2564 commits (31%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: B (85/100)

- 527 of 2564 commits (21%) were made between 10pm and 5am.
- 135 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 18 commits are reverts (1%) and 334 (13%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (20/100)

- 264 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 2937 days (8.0 years). It has seniority now.
- Senior TODO on file: src/language-html/utilities/index.js:57 - "// TODO: handle non-text children in <pre>"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (22/100)

- 36 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 3250 days. It is not temporary. It is load-bearing.
- 0 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: C (72/100)

- Active on 701 of 1631 days in the review period (43%).
- Longest streak: 22 days. Longest disappearance: 27 days.
- Average output on an active day: 3.7 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** tests/format/less/less-test-suite/__snapshots__/format.test.js.snap - 21,129 lines of churn across the review period. You two have history.
- **Largest single commit:** 28,924 lines changed in "Test: Update `printWidth` indicator (#10293)". A bold unit of work.
- **Weekend work:** 503 of 2564 commits landed on a Saturday or Sunday.
- **Busiest day:** 2026-01-15, with 29 commits.
- **Languages by churn:** snap (347,427 lines of churn), JavaScript (178,127 lines of churn), Markdown (65,501 lines of churn), cjs (36,187 lines of churn).
- **Longest commit message:** "Replace `getNextNonSpaceNonCommentCharacterIndex` with `getNextNonSpaceNonCommentCharacterIndexWithStartIndex` internally (#14319)" (130 characters. A novel.)
- **Shortest commit message:** "Fix". A haiku, if you squint.
- **Catchphrase:** "update", appearing 489 times across your commit subjects.
- **Authorship note:** 84% of these commits look like squash merges (subjects ending in a PR number). Squash merges credit whoever pressed the merge button, not whoever wrote the code, so read this grade as the record of the button-presser.
- **Net lines:** 383,743 added, 185,484 deleted.

## Awards

- **Friday Gambler:** 135 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **Streak Keeper:** 22 active days in a row at the longest stretch. Showing up is a skill.
- **Fossil Keeper:** A TODO has survived 2937 days in the code. It qualifies for the pension plan.
- **Marathon Day:** 29 commits in a single day (2026-01-15). Somewhere in there was a lunch break. Probably.
- **The Purge:** One commit deleted 18,807 lines. Witnesses described the diff as 'mostly red'.
- **Polyglot:** Meaningful churn in 48 languages. Jack of all trades, suspect in all of them.
- **Old Faithful:** Commits spanning 4 years on the same codebase. It has outlived three roadmaps and a rebrand.
- **The Archaeologist:** Revived 224 commit(s) touching files untouched for over a year. Brushed off the dust, read the ancient comments, understood nothing, proceeded anyway.

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
