# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Hanks  
**Project reviewed:** vue  
**Review period:** 2016-12-09 to 2018-03-08  
**Commits examined:** 47  
**Review date:** 2026-11-19  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: D (56/100)

*Partially meets expectations. This plan exists for a reason.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Communication: A (100/100)

- 0 of 47 commit messages (0%) say almost nothing (average message length: 62 characters).
- 18 of 47 commits (38%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: B (79/100)

- 14 of 47 commits (30%) were made between 10pm and 5am.
- 0 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 1 commits are reverts (2%) and 5 (11%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (20/100)

- 215 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 3869 days (10.6 years). It has seniority now.
- Senior TODO on file: benchmarks/dbmon/lib/memory-stats.js:58 - "// TODO, add a sanity check to see if values are bucketed."

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (36/100)

- 6 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 3870 days. It is not temporary. It is load-bearing.
- 1 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: D (46/100)

- Active on 30 of 455 days in the review period (7%).
- Longest streak: 3 days. Longest disappearance: 113 days.
- Average output on an active day: 1.6 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** dist/vue.js - 149,891 lines of churn across the review period. You two have history.
- **Largest single commit:** 2,130 lines changed in "[release] weex-vue-framework@2.4.2-weex.1 (#6196)". A bold unit of work.
- **Weekend work:** 7 of 47 commits landed on a Saturday or Sunday.
- **Busiest day:** 2017-07-10, with 4 commits.
- **Languages by churn:** JavaScript (1,531,956 lines of churn), TypeScript (76,114 lines of churn), Markdown (14,572 lines of churn), json (3,954 lines of churn).
- **Longest commit message:** "feat($compiler): supports compiling v-bind to the weex native directive in recycle-list" (87 characters. A novel.)
- **Shortest commit message:** "feat(weex): wrap IFFE for appCode". A haiku, if you squint.
- **Catchphrase:** "weex", appearing 58 times across your commit subjects.
- **Authorship note:** 66% of these commits look like squash merges (subjects ending in a PR number). Squash merges credit whoever pressed the merge button, not whoever wrote the code, so read this grade as the record of the button-presser.
- **Net lines:** 6,521 added, 2,815 deleted.

## Awards

- **Night Owl:** 30% of all commits landed between 10pm and 5am. The codebase's second shift.
- **The Ghost:** Vanished for 113 days once, then returned as if nothing happened. It had, in fact, happened.
- **Fossil Keeper:** A TODO has survived 3869 days in the code. It qualifies for the pension plan.
- **The Purge:** One commit deleted 1,318 lines. Witnesses described the diff as 'mostly red'.
- **Polyglot:** Meaningful churn in 24 languages. Jack of all trades, suspect in all of them.
- **Phoenix:** Vanished for a season, then came back swinging. The comeback commits outnumber the goodbye ones, because there were no goodbye ones.
- **The Archaeologist:** Revived 2 commit(s) touching files untouched for over a year. Brushed off the dust, read the ancient comments, understood nothing, proceeded anyway.

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
