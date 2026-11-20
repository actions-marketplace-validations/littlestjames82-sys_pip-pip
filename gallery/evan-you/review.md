# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Evan You  
**Project reviewed:** core  
**Review period:** 2018-09-19 to 2024-06-18  
**Commits examined:** 3371  
**Review date:** 2026-11-20  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: D (54/100)

*Partially meets expectations. This plan exists for a reason.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Authorship

- **Share of the record:** 3576 of 6180 commits in this history (58%) are by Evan You. The remaining 2604 are by 646 other authors.
- **Most of the rest:** edison (406 commits), 三咲智子 Kevin Deng (110 commits), HcySunYang (91 commits).
- **Arrival:** the history starts 2018-09-19; Evan You's first commit is 2018-09-19, and 0 commits predate it.
- **Authorship: no concerns.** This record is substantially the reviewed author's own work, as a review assumes.

## Communication: A (100/100)

- 21 of 3371 commit messages (1%) say almost nothing (average message length: 46 characters).
- Entered into the record: "wip: warning", "wip: warning", "wip: mixins".
- 695 of 3371 commits (21%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: B (86/100)

- 338 of 3371 commits (10%) were made between 10pm and 5am.
- 228 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 16 commits are reverts (0%) and 817 (24%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (20/100)

- 227 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 2553 days (7.0 years). It has seniority now.
- Senior TODO on file: packages/runtime-core/src/components/BaseTransition.ts:45 - "// In templates these can be written as @before-enter="xxx" as prop names"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (0/100)

- 5 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 2422 days. It is not temporary. It is load-bearing.
- 390 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: C (65/100)

- Active on 731 of 2100 days in the review period (35%).
- Longest streak: 14 days. Longest disappearance: 75 days.
- Average output on an active day: 4.6 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** packages/compiler-core/__tests__/__snapshots__/parse.spec.ts.snap - 17,478 lines of churn across the review period. You two have history.
- **Largest single commit:** 7,478 lines changed in "wip: pass all non-error parsing tests". A bold unit of work.
- **Weekend work:** 394 of 3371 commits landed on a Saturday or Sunday.
- **Busiest day:** 2018-09-19, with 20 commits.
- **Languages by churn:** TypeScript (248,072 lines of churn), snap (38,600 lines of churn), Markdown (22,946 lines of churn), json (20,853 lines of churn).
- **Longest commit message:** "fix(watch): stop instance-bound watchers in post render queue so that changes triggered in beforeUnmount get correct value in callback" (134 characters. A novel.)
- **Shortest commit message:** "wip: refs". A haiku, if you squint.
- **Catchphrase:** "chore", appearing 604 times across your commit subjects.
- **Net lines:** 116,026 added, 78,913 deleted.

## Awards

- **Friday Gambler:** 228 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **The Ghost:** Vanished for 75 days once, then returned as if nothing happened. It had, in fact, happened.
- **Streak Keeper:** 14 active days in a row at the longest stretch. Showing up is a skill.
- **Fossil Keeper:** A TODO has survived 2553 days in the code. It qualifies for the pension plan.
- **Marathon Day:** 20 commits in a single day (2018-09-19). Somewhere in there was a lunch break. Probably.
- **The Purge:** One commit deleted 7,136 lines. Witnesses described the diff as 'mostly red'.
- **Polyglot:** Meaningful churn in 24 languages. Jack of all trades, suspect in all of them.
- **Old Faithful:** Commits spanning 5 years on the same codebase. It has outlived three roadmaps and a rebrand.
- **The Archaeologist:** Revived 65 commit(s) touching files untouched for over a year. Brushed off the dust, read the ancient comments, understood nothing, proceeded anyway.

## 30-day improvement plan

The following actions address the lowest-scoring areas. Progress will be assessed by re-running this review, which is to say, by the record itself.

### Judgment
1. Every 'temporary' fix gets an expiry date in the comment. When the date passes, it gets reviewed first, not last.
2. Count the hacks monthly. The number going down is the goal; the number existing is not the shame.
3. No new workaround merges without a note explaining what the real fix would take.

### Follow-through
1. Pick the five oldest TODOs. Close them, convert them to tracked issues, or delete them and own the decision.
2. New rule: a TODO without a date and a name is litter. Date and name, every time.
3. One TODO closed per week, minimum, until the backlog is younger than you are.

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
