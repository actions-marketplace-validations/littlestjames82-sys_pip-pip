# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Sebastián Ramírez  
**Project reviewed:** fastapi  
**Review period:** 2023-08-14 to 2026-11-18  
**Commits examined:** 1209  
**Review date:** 2026-11-19  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: C (59/100)

*Meets some expectations. There is a conversation to be had.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Communication: A (100/100)

- 0 of 1209 commit messages (0%) say almost nothing (average message length: 57 characters).
- 495 of 1209 commits (41%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: A (91/100)

- 241 of 1209 commits (20%) were made between 10pm and 5am.
- 55 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 0 commits are reverts (0%) and 0 (0%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (20/100)

- 179 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 2378 days (6.5 years). It has seniority now.
- Senior TODO on file: docs/es/docs/async.md:230 - "Todos los cajeros haciendo todo el trabajo con un cliente tras otro 👨‍💼⏯."

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (22/100)

- 41 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 2549 days. It is not temporary. It is load-bearing.
- 0 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: C (63/100)

- Active on 355 of 1193 days in the review period (30%).
- Longest streak: 11 days. Longest disappearance: 39 days.
- Average output on an active day: 3.4 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** uv.lock - 26,198 lines of churn across the review period. You two have history.
- **Largest single commit:** 58,885 lines changed in "🔧 Update docs setup with latest configs and plugins (#11953)". A bold unit of work.
- **Weekend work:** 329 of 1209 commits landed on a Saturday or Sunday.
- **Busiest day:** 2026-07-01, with 27 commits.
- **Languages by churn:** Markdown (558,472 lines of churn), Python (263,117 lines of churn), YAML (36,627 lines of churn), lock (26,399 lines of churn).
- **Longest commit message:** "🌐 Fix typos in French translations for `docs/fr/docs/advanced/path-operation-advanced-configuration.md`, `docs/fr/docs/alternatives.md`, `docs/fr/docs/async.md`, `docs/fr/docs/features.md`, `docs/fr/docs/help-fastapi.md`, `docs/fr/docs/index.md`, `docs/fr/docs/python-types.md`, `docs/fr/docs/tutorial/body.md`, `docs/fr/docs/tutorial/first-steps.md`, `docs/fr/docs/tutorial/query-params.md` (#10154)" (400 characters. A novel.)
- **Shortest commit message:** "🔖 Release 0.103.2". A haiku, if you squint.
- **Catchphrase:** "update", appearing 601 times across your commit subjects.
- **Authorship note:** 86% of these commits look like squash merges (subjects ending in a PR number). Squash merges credit whoever pressed the merge button, not whoever wrote the code, so read this grade as the record of the button-presser.
- **Net lines:** 363,937 added, 264,977 deleted.

## Awards

- **Friday Gambler:** 55 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **Streak Keeper:** 11 active days in a row at the longest stretch. Showing up is a skill.
- **Fossil Keeper:** A TODO has survived 2378 days in the code. It qualifies for the pension plan.
- **Marathon Day:** 27 commits in a single day (2026-07-01). Somewhere in there was a lunch break. Probably.
- **The Purge:** One commit deleted 26,206 lines. Witnesses described the diff as 'mostly red'.
- **Polyglot:** Meaningful churn in 18 languages. Jack of all trades, suspect in all of them.
- **Old Faithful:** Commits spanning 3 years on the same codebase. It has outlived three roadmaps and a rebrand.
- **The Archaeologist:** Revived 53 commit(s) touching files untouched for over a year. Brushed off the dust, read the ancient comments, understood nothing, proceeded anyway.

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
