# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Cory Benfield  
**Project reviewed:** requests  
**Review period:** 2012-02-16 to 2017-11-27  
**Commits examined:** 606  
**Review date:** 2026-11-19  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: C (65/100)

*Meets some expectations. There is a conversation to be had.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Communication: A (100/100)

- 19 of 606 commit messages (3%) say almost nothing (average message length: 41 characters).
- Entered into the record: "Capitalisation.", "Reinstate '$'.", "v2.7.0".
- 303 of 606 commits (50%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: A (97/100)

- 24 of 606 commits (4%) were made between 10pm and 5am.
- 21 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 2 commits are reverts (0%) and 13 (2%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (28/100)

- 15 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 5206 days (14.3 years). It has seniority now.
- Senior TODO on file: src/requests/auth.py:213 - "# XXX not implemented yet"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: D (46/100)

- 4 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 2985 days. It is not temporary. It is load-bearing.
- 0 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: D (54/100)

- Active on 369 of 2112 days in the review period (17%).
- Longest streak: 5 days. Longest disappearance: 85 days.
- Average output on an active day: 1.6 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** requests/cacert.pem - 23,214 lines of churn across the review period. You two have history.
- **Largest single commit:** 9,415 lines changed in "Vendor idna v2.1". A bold unit of work.
- **Weekend work:** 126 of 606 commits landed on a Saturday or Sunday.
- **Busiest day:** 2017-05-09, with 12 commits.
- **Languages by churn:** Python (183,204 lines of churn), pem (23,574 lines of churn), ai (12,215 lines of churn), rst (11,842 lines of churn).
- **Longest commit message:** "Merge branch 'fix-merge-setting' of https://github.com/ak1r4/requests into proposed/2.8.0" (89 characters. A novel.)
- **Shortest commit message:** "v2.7.0". A haiku, if you squint.
- **Catchphrase:** "merge", appearing 283 times across your commit subjects.
- **Net lines:** 23,515 added, 8,308 deleted.

## Awards

- **Friday Gambler:** 21 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **Surgeon:** Small, precise commits, one concern at a time. Future archaeologists send their thanks.
- **The Ghost:** Vanished for 85 days once, then returned as if nothing happened. It had, in fact, happened.
- **Open Book:** 50% of commits carry a real explanation. Reviewers wept, briefly, with joy.
- **Fossil Keeper:** A TODO has survived 5206 days in the code. It qualifies for the pension plan.
- **The Purge:** One commit deleted 2,871 lines. Witnesses described the diff as 'mostly red'.
- **Polyglot:** Meaningful churn in 39 languages. Jack of all trades, suspect in all of them.
- **Old Faithful:** Commits spanning 5 years on the same codebase. It has outlived three roadmaps and a rebrand.
- **Merge Goblin:** 281 of 606 commits are merges. Somewhere upstream, a rebase weeps quietly.
- **The Archaeologist:** Revived 12 commit(s) touching files untouched for over a year. Brushed off the dust, read the ancient comments, understood nothing, proceeded anyway.

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
