# PERFORMANCE IMPROVEMENT PLAN

**Employee:** David Heinemeier Hansson  
**Project reviewed:** rails  
**Review period:** 2021-11-23 to 2026-02-18  
**Commits examined:** 145  
**Review date:** 2026-11-20  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: D (55/100)

*Partially meets expectations. This plan exists for a reason.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Authorship

- **Share of the record:** 258 of 29998 commits in this history (1%) are by David Heinemeier Hansson. The remaining 29740 are by 2386 other authors.
- **Most of the rest:** Jean Boussier (3071 commits), Ryuta Kamizono (2779 commits), Rafael Mendonça França (2300 commits).
- **Arrival:** the history starts 2010-01-02; David Heinemeier Hansson's first commit is 2018-12-03, and 87 commits predate it.
- **Authorship: no concerns.** This record is substantially the reviewed author's own work, as a review assumes.

## Communication: A (100/100)

- 2 of 145 commit messages (1%) say almost nothing (average message length: 49 characters).
- Entered into the record: "Fix signature", "Fix example".
- 84 of 145 commits (58%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: A (93/100)

- 11 of 145 commits (8%) were made between 10pm and 5am.
- 7 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 2 commits are reverts (1%) and 5 (3%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (20/100)

- 191 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 5896 days (16.2 years). It has seniority now.
- Senior TODO on file: actionview/test/actionpack/controller/capture_test.rb:32 - "@todo = "some todo""

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (22/100)

- 110 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 7724 days. It is not temporary. It is load-bearing.
- 0 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: F (42/100)

- Active on 77 of 1549 days in the review period (5%).
- Longest streak: 6 days. Longest disappearance: 192 days.
- Average output on an active day: 1.9 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** guides/source/active_record_querying.md - 3,847 lines of churn across the review period. You two have history.
- **Largest single commit:** 577 lines changed in "Add Rails.app.creds to provide combined credentials lookup in ENV and encrypted file (#56404)". A bold unit of work.
- **Weekend work:** 36 of 145 commits landed on a Saturday or Sunday.
- **Busiest day:** 2024-08-07, with 10 commits.
- **Languages by churn:** Ruby (196,090 lines of churn), Markdown (41,555 lines of churn), JavaScript (2,585 lines of churn), tt (655 lines of churn).
- **Longest commit message:** "By definition, new apps wont have any deprecations to worry about. So dont expose those controls for new apps by default (#51831)" (129 characters. A novel.)
- **Shortest commit message:** "Fix example". A haiku, if you squint.
- **Catchphrase:** "default", appearing 33 times across your commit subjects.
- **Authorship note:** 50% of these commits look like squash merges (subjects ending in a PR number). Squash merges credit whoever pressed the merge button, not whoever wrote the code, so read this grade as the record of the button-presser.
- **Net lines:** 1,387 added, 94 deleted.

## Awards

- **Friday Gambler:** 7 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **Surgeon:** Small, precise commits, one concern at a time. Future archaeologists send their thanks.
- **The Ghost:** Vanished for 192 days once, then returned as if nothing happened. It had, in fact, happened.
- **Open Book:** 58% of commits carry a real explanation. Reviewers wept, briefly, with joy.
- **Fossil Keeper:** A TODO has survived 5896 days in the code. It qualifies for the pension plan.
- **Polyglot:** Meaningful churn in 34 languages. Jack of all trades, suspect in all of them.
- **Old Faithful:** Commits spanning 4 years on the same codebase. It has outlived three roadmaps and a rebrand.
- **Phoenix:** Vanished for a season, then came back swinging. The comeback commits outnumber the goodbye ones, because there were no goodbye ones.
- **Rubber Duck:** Commit bodies average 216 characters. The reasoning is all there. All of it. Every thought.
- **The Archaeologist:** Revived 1 commit(s) touching files untouched for over a year. Brushed off the dust, read the ancient comments, understood nothing, proceeded anyway.

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
