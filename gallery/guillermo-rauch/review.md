# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Guillermo Rauch  
**Project reviewed:** nextjs-era  
**Review period:** 2016-10-05 to 2017-08-08  
**Commits examined:** 162  
**Review date:** 2026-11-20  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: D (58/100)

*Partially meets expectations. This plan exists for a reason.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Communication: A (97/100)

- 5 of 162 commit messages (3%) say almost nothing (average message length: 20 characters).
- Entered into the record: "update yarn", "update lockfile", "fix typo".
- 4 of 162 commits (2%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: A (94/100)

- 5 of 162 commits (3%) were made between 10pm and 5am.
- 4 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 4 commits are reverts (2%) and 1 (1%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (20/100)

- 241 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 2738 days (7.5 years). It has seniority now.
- Senior TODO on file: examples/with-reasonml-todo/README.md:30 - "yarn create next-app --example with-reasonml-todo with-reasonml-app"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (22/100)

- 37 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 2778 days. It is not temporary. It is load-bearing.
- 0 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: D (57/100)

- Active on 65 of 308 days in the review period (21%).
- Longest streak: 5 days. Longest disappearance: 62 days.
- Average output on an active day: 2.5 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** packages/next/types/webpack.d.ts - 6,329 lines of churn across the review period. You two have history.
- **Largest single commit:** 0 lines changed in "initial spec". A bold unit of work.
- **Weekend work:** 34 of 162 commits landed on a Saturday or Sunday.
- **Busiest day:** 2016-12-20, with 29 commits.
- **Languages by churn:** JavaScript (255,244 lines of churn), TypeScript (103,908 lines of churn), Markdown (61,967 lines of churn), json (34,463 lines of churn).
- **Longest commit message:** "filter for null *after* `Children` is called to make this work with some `-compat` pollyfills" (93 characters. A novel.)
- **Shortest commit message:** "add lock". A haiku, if you squint.
- **Catchphrase:** "update", appearing 82 times across your commit subjects.
- **Net lines:** 0 added, 0 deleted.

## Awards

- **Friday Gambler:** 4 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **Surgeon:** Small, precise commits, one concern at a time. Future archaeologists send their thanks.
- **The Ghost:** Vanished for 62 days once, then returned as if nothing happened. It had, in fact, happened.
- **Fossil Keeper:** A TODO has survived 2738 days in the code. It qualifies for the pension plan.
- **Marathon Day:** 29 commits in a single day (2016-12-20). Somewhere in there was a lunch break. Probably.
- **Polyglot:** Meaningful churn in 78 languages. Jack of all trades, suspect in all of them.

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
