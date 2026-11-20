# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Guido van Rossum  
**Project reviewed:** cpython  
**Review period:** 2021-06-21 to 2026-04-24  
**Commits examined:** 206  
**Review date:** 2026-11-20  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: D (57/100)

*Partially meets expectations. This plan exists for a reason.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Communication: A (100/100)

- 0 of 206 commit messages (0%) say almost nothing (average message length: 61 characters).
- 160 of 206 commits (78%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: A (96/100)

- 4 of 206 commits (2%) were made between 10pm and 5am.
- 9 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 1 commits are reverts (0%) and 11 (5%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (20/100)

- 136 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 2128 days (5.8 years). It has seniority now.
- Senior TODO on file: Doc/builtins/exceptions.rst:284 - ".. XXX xref to sequences"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (22/100)

- 164 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 2128 days. It is not temporary. It is load-bearing.
- 0 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: D (44/100)

- Active on 151 of 1769 days in the review period (9%).
- Longest streak: 5 days. Longest disappearance: 182 days.
- Average output on an active day: 1.4 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** Python/deepfreeze/deepfreeze.c - 296,294 lines of churn across the review period. You two have history.
- **Largest single commit:** 239 lines changed in "gh-108951: add TaskGroup.cancel() (#127214)". A bold unit of work.
- **Weekend work:** 11 of 206 commits landed on a Saturday or Sunday.
- **Busiest day:** 2023-11-17, with 5 commits.
- **Languages by churn:** C (901,706 lines of churn), Python (216,926 lines of churn), rst (116,878 lines of churn), txt (24,009 lines of churn).
- **Longest commit message:** "gh-118335: Rename --experimental-interpreter on Windows to --experimental-jit-interpreter (#118497)" (99 characters. A novel.)
- **Shortest commit message:** "Update CODEOWNERS (#126005)". A haiku, if you squint.
- **Catchphrase:** "cases", appearing 22 times across your commit subjects.
- **Authorship note:** 93% of these commits look like squash merges (subjects ending in a PR number). Squash merges credit whoever pressed the merge button, not whoever wrote the code, so read this grade as the record of the button-presser.
- **Net lines:** 229 added, 48 deleted.

## Awards

- **Friday Gambler:** 9 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **Surgeon:** Small, precise commits, one concern at a time. Future archaeologists send their thanks.
- **The Ghost:** Vanished for 182 days once, then returned as if nothing happened. It had, in fact, happened.
- **Open Book:** 78% of commits carry a real explanation. Reviewers wept, briefly, with joy.
- **Fossil Keeper:** A TODO has survived 2128 days in the code. It qualifies for the pension plan.
- **Polyglot:** Meaningful churn in 94 languages. Jack of all trades, suspect in all of them.
- **Old Faithful:** Commits spanning 4 years on the same codebase. It has outlived three roadmaps and a rebrand.
- **Rubber Duck:** Commit bodies average 301 characters. The reasoning is all there. All of it. Every thought.

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
