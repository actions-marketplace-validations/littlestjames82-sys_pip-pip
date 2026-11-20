# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Rich Harris  
**Project reviewed:** svelte  
**Review period:** 2017-08-20 to 2024-03-16  
**Commits examined:** 3080  
**Review date:** 2026-11-20  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: D (56/100)

*Partially meets expectations. This plan exists for a reason.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Authorship

- **Share of the record:** 3964 of 9293 commits in this history (43%) are by Rich Harris. The remaining 5329 are by 947 other authors.
- **Most of the rest:** Simon H (765 commits), Conduitry (722 commits), Dominic Gannaway (497 commits).
- **Arrival:** the history starts 2017-08-20; Rich Harris's first commit is 2017-08-20, and 0 commits predate it.
- **Authorship: no concerns.** This record is substantially the reviewed author's own work, as a review assumes.

## Communication: A (96/100)

- 216 of 3080 commit messages (7%) say almost nothing (average message length: 38 characters).
- Entered into the record: "validation", "update tests", "update tests".
- 1054 of 3080 commits (34%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: A (93/100)

- 342 of 3080 commits (11%) were made between 10pm and 5am.
- 163 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 6 commits are reverts (0%) and 176 (6%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (20/100)

- 279 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 1327 days (3.6 years). It has seniority now.
- Senior TODO on file: documentation/docs/03-template-syntax/03-each.md:131 - "{#each todos as todo}"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (21/100)

- 22 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 841 days. It is not temporary. It is load-bearing.
- 5 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: D (50/100)

- Active on 439 of 2401 days in the review period (18%).
- Longest streak: 12 days. Longest disappearance: 199 days.
- Average output on an active day: 7.0 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** compiler.js - 43,153 lines of churn across the review period. You two have history.
- **Largest single commit:** 7,753 lines changed in "feat(site-2): Split docs (#8435)". A bold unit of work.
- **Weekend work:** 1384 of 3080 commits landed on a Saturday or Sunday.
- **Busiest day:** 2018-04-28, with 48 commits.
- **Languages by churn:** JavaScript (520,638 lines of churn), Markdown (112,804 lines of churn), svelte (107,516 lines of churn), TypeScript (79,573 lines of churn).
- **Longest commit message:** "Merge branch 'feat/2174_dev_runtime_warning_when_passing_unknown_props' of https://github.com/colincasey/svelte into colincasey-feat/2174_dev_runtime_warning_when_passing_unknown_props" (184 characters. A novel.)
- **Shortest commit message:** "doh". A haiku, if you squint.
- **Catchphrase:** "merge", appearing 1113 times across your commit subjects.
- **Net lines:** 34,289 added, 30,891 deleted.
- **Language:** 10 commit messages contain profanity. The record reflects the journey.

## Awards

- **Friday Gambler:** 163 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **Surgeon:** Small, precise commits, one concern at a time. Future archaeologists send their thanks.
- **The Ghost:** Vanished for 199 days once, then returned as if nothing happened. It had, in fact, happened.
- **Streak Keeper:** 12 active days in a row at the longest stretch. Showing up is a skill.
- **Fossil Keeper:** A TODO has survived 1327 days in the code. It qualifies for the pension plan.
- **Colourful Commentator:** 10 commit messages contain profanity. Honest, if not exactly handbook language.
- **Weekend Warrior:** 45% of commits landed on a Saturday or Sunday. The roadmap thanks you. The weekend does not.
- **Marathon Day:** 48 commits in a single day (2018-04-28). Somewhere in there was a lunch break. Probably.
- **The Purge:** One commit deleted 3,994 lines. Witnesses described the diff as 'mostly red'.
- **Polyglot:** Meaningful churn in 30 languages. Jack of all trades, suspect in all of them.
- **Old Faithful:** Commits spanning 6 years on the same codebase. It has outlived three roadmaps and a rebrand.
- **Merge Goblin:** 1112 of 3080 commits are merges. Somewhere upstream, a rebase weeps quietly.
- **The Archaeologist:** Revived 4 commit(s) touching files untouched for over a year. Brushed off the dust, read the ancient comments, understood nothing, proceeded anyway.

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
