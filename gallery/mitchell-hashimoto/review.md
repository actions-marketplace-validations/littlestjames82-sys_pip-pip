# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Mitchell Hashimoto  
**Project reviewed:** terraform  
**Review period:** 2015-09-13 to 2017-08-30  
**Commits examined:** 1032  
**Review date:** 2026-11-20  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: D (57/100)

*Partially meets expectations. This plan exists for a reason.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Authorship

- **Share of the record:** 1399 of 29886 commits in this history (5%) are by Mitchell Hashimoto. The remaining 28487 are by 1924 other authors.
- **Most of the rest:** James Bardin (4360 commits), Martin Atkins (2954 commits), Paul Stack (2120 commits).
- **Arrival:** the history starts 2014-12-14; Mitchell Hashimoto's first commit is 2015-09-13, and 208 commits predate it.
- **Authorship: no concerns.** This record is substantially the reviewed author's own work, as a review assumes.

## Communication: A (100/100)

- 9 of 1032 commit messages (1%) say almost nothing (average message length: 44 characters).
- Entered into the record: "wip", "v0.7.9", "update HIL".
- 197 of 1032 commits (19%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: A (96/100)

- 80 of 1032 commits (8%) were made between 10pm and 5am.
- 60 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 5 commits are reverts (0%) and 2 (0%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (20/100)

- 131 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 2599 days (7.1 years). It has seniority now.
- Senior TODO on file: internal/backend/local/backend_local.go:170 - "// TODO: Need to route the operation context through into here, so that"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (13/100)

- 169 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 3592 days. It is not temporary. It is load-bearing.
- 6 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: D (57/100)

- Active on 184 of 718 days in the review period (26%).
- Longest streak: 25 days. Longest disappearance: 145 days.
- Average output on an active day: 5.6 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** internal/rpcapi/terraform1/terraform1.pb.go - 114,805 lines of churn across the review period. You two have history.
- **Largest single commit:** 0 lines changed in "command/get: fix typo". A bold unit of work.
- **Weekend work:** 139 of 1032 commits landed on a Saturday or Sunday.
- **Busiest day:** 2017-01-26, with 35 commits.
- **Languages by churn:** Go (923,759 lines of churn), mdx (59,185 lines of churn), proto (23,993 lines of churn), hcl (11,211 lines of churn).
- **Longest commit message:** "Merge branch 'fix-field-reader-setsubkeys-computed' of https://github.com/vancluever/terraform into vancluever-fix-field-reader-setsubkeys-computed" (147 characters. A novel.)
- **Shortest commit message:** "wip". A haiku, if you squint.
- **Catchphrase:** "terraform", appearing 438 times across your commit subjects.
- **Net lines:** 0 added, 0 deleted.

## Awards

- **Friday Gambler:** 60 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **Surgeon:** Small, precise commits, one concern at a time. Future archaeologists send their thanks.
- **The Ghost:** Vanished for 145 days once, then returned as if nothing happened. It had, in fact, happened.
- **Streak Keeper:** 25 active days in a row at the longest stretch. Showing up is a skill.
- **Fossil Keeper:** A TODO has survived 2599 days in the code. It qualifies for the pension plan.
- **Marathon Day:** 35 commits in a single day (2017-01-26). Somewhere in there was a lunch break. Probably.
- **Polyglot:** Meaningful churn in 32 languages. Jack of all trades, suspect in all of them.
- **Phoenix:** Vanished for a season, then came back swinging. The comeback commits outnumber the goodbye ones, because there were no goodbye ones.

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
