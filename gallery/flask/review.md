# PERFORMANCE IMPROVEMENT PLAN

**Employee:** David Lord  
**Project reviewed:** gallery-flask-9lcvucet  
**Review period:** 2015-10-30 to 2026-10-30  
**Commits examined:** 1865  
**Review date:** 2026-11-18  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: C (62/100)

*Meets some expectations. There is a conversation to be had.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Communication: A (100/100)

- 22 of 1865 commit messages (1%) say almost nothing (average message length: 42 characters).
- Entered into the record: "failing test", "Update CHANGES", "fix links".
- 735 of 1865 commits (39%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: A (97/100)

- 40 of 1865 commits (2%) were made between 10pm and 5am.
- 38 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 6 commits are reverts (0%) and 89 (5%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: D (42/100)

- 9 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 2753 days (7.5 years). It has seniority now.
- Senior TODO on file: tests/test_testing.py:122 - "bp = flask.Blueprint("company", __name__, subdomain="xxx")"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (22/100)

- 14 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 6068 days. It is not temporary. It is load-bearing.
- 0 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: D (51/100)

- Active on 528 of 4019 days in the review period (13%).
- Longest streak: 7 days. Longest disappearance: 82 days.
- Average output on an active day: 3.5 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** uv.lock - 12,229 lines of churn across the review period. You two have history.
- **Largest single commit:** 5,577 lines changed in "rewrite tutorial docs and example". A bold unit of work.
- **Weekend work:** 379 of 1865 commits landed on a Saturday or Sunday.
- **Busiest day:** 2019-01-06, with 28 commits.
- **Languages by churn:** Python (96,178 lines of churn), rst (46,130 lines of churn), lock (12,229 lines of churn), txt (4,728 lines of churn).
- **Longest commit message:** "use specific pypy versions for travis xenial remove 3.6 from appveyor, reduce in tox remove deprecated travis feature "sudo: false" split docs and devel,lowest travis envs remove osx py2 env in attempt to finish faster move travis matrix to python key" (251 characters. A novel.)
- **Shortest commit message:** "use uv". A haiku, if you squint.
- **Catchphrase:** "merge", appearing 907 times across your commit subjects.
- **Net lines:** 41,843 added, 40,870 deleted.
- **Language:** 1 commit messages contain profanity. The record reflects the journey.

## Awards

- **Friday Gambler:** 38 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **The Ghost:** Vanished for 82 days once, then returned as if nothing happened. It had, in fact, happened.
- **Streak Keeper:** 7 active days in a row at the longest stretch. Showing up is a skill.
- **Fossil Keeper:** A TODO has survived 2753 days in the code. It qualifies for the pension plan.
- **Marathon Day:** 28 commits in a single day (2019-01-06). Somewhere in there was a lunch break. Probably.
- **The Purge:** One commit deleted 2,237 lines. Witnesses described the diff as 'mostly red'.
- **Polyglot:** Meaningful churn in 34 languages. Jack of all trades, suspect in all of them.
- **Old Faithful:** Commits spanning 11 years on the same codebase. It has outlived three roadmaps and a rebrand.

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
