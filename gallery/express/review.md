# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Tj Holowaychuk  
**Project reviewed:** express  
**Review period:** 2010-04-11 to 2014-02-19  
**Commits examined:** 2788  
**Review date:** 2026-11-19  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: C (72/100)

*Meets some expectations. There is a conversation to be had.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Authorship

- **Share of the record:** 2788 of 4940 commits in this history (56%) are by Tj Holowaychuk. The remaining 2152 are by 376 other authors.
- **Most of the rest:** Douglas Christopher Wilson (1232 commits), Jonathan Ong (84 commits), Roman Shtylman (70 commits).
- **Arrival:** the history starts 2010-04-10; Tj Holowaychuk's first commit is 2010-04-11, and 1 commits predate it.
- **Authorship: no concerns.** This record is substantially the reviewed author's own work, as a review assumes.

## Communication: B (87/100)

- 348 of 2788 commit messages (12%) say almost nothing (average message length: 29 characters).
- Entered into the record: "Updated JSpec", "Docs", "_ -> val".
- 278 of 2788 commits (10%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: A (95/100)

- 101 of 2788 commits (4%) were made between 10pm and 5am.
- 87 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 13 commits are reverts (0%) and 242 (9%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (20/100)

- 29 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 2758 days (7.6 years). It has seniority now.
- Senior TODO on file: test/express.static.js:32 - ".get('/todo.txt')"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: A (92/100)

- 0 spots in the code are labelled temporary, a hack, or a workaround.
- 0 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: C (68/100)

- Active on 513 of 1411 days in the review period (36%).
- Longest streak: 15 days. Longest disappearance: 29 days.
- Average output on an active day: 5.4 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** docs/api.html - 33,065 lines of churn across the review period. You two have history.
- **Largest single commit:** 5,316 lines changed in "removed old docs". A bold unit of work.
- **Weekend work:** 264 of 2788 commits landed on a Saturday or Sunday.
- **Busiest day:** 2011-11-08, with 70 commits.
- **Languages by churn:** JavaScript (112,223 lines of churn), HTML (45,503 lines of churn), Markdown (17,984 lines of churn), 1 (7,760 lines of churn).
- **Longest commit message:** "Fixed bug messing with error handlers when listenFD() is called instead of listen(). [thanks guillermo]" (103 characters. A novel.)
- **Shortest commit message:** ".". A haiku, if you squint.
- **Catchphrase:** "docs", appearing 286 times across your commit subjects.
- **Net lines:** 72,590 added, 69,699 deleted.
- **Language:** 6 commit messages contain profanity. The record reflects the journey.

## Awards

- **Friday Gambler:** 87 commits shipped on a Friday at or after 4pm. Courage, or something adjacent to it.
- **Streak Keeper:** 15 active days in a row at the longest stretch. Showing up is a skill.
- **Fossil Keeper:** A TODO has survived 2758 days in the code. It qualifies for the pension plan.
- **Colourful Commentator:** 6 commit messages contain profanity. Honest, if not exactly handbook language.
- **Marathon Day:** 70 commits in a single day (2011-11-08). Somewhere in there was a lunch break. Probably.
- **The Purge:** One commit deleted 5,316 lines. Witnesses described the diff as 'mostly red'.
- **Polyglot:** Meaningful churn in 38 languages. Jack of all trades, suspect in all of them.
- **Old Faithful:** Commits spanning 3 years on the same codebase. It has outlived three roadmaps and a rebrand.
- **The Archaeologist:** Revived 20 commit(s) touching files untouched for over a year. Brushed off the dust, read the ancient comments, understood nothing, proceeded anyway.

## 30-day improvement plan

The following actions address the lowest-scoring areas. Progress will be assessed by re-running this review, which is to say, by the record itself.

### Follow-through
1. Pick the five oldest TODOs. Close them, convert them to tracked issues, or delete them and own the decision.
2. New rule: a TODO without a date and a name is litter. Date and name, every time.
3. One TODO closed per week, minimum, until the backlog is younger than you are.

### Consistency
1. Small and daily beats heroic and monthly. Protect the streak, shorten the silences.
2. End each session by leaving the next step written down, so returning is easy.
3. If a gap is coming (holiday, life), say so in a commit. Silence reads worse than absence.

### Communication
1. Every commit message must complete the sentence: 'This change will...' If it cannot, the commit is not ready.
2. The words 'stuff', 'wip', 'misc' and 'fix fix fix' are retired, effective immediately.
3. Commits touching more than one file get a body. Two lines minimum. Future you is the audience.

## Sign-off

By continuing to commit, the employee acknowledges receipt of this plan. Appeals may be filed by improving the record.

Signed,  
**Management**  
*PIP - pip install on-a-pip*

*Not for employment decisions. PIP grades a commit record, not a person, and it reads best when the person reading it is the person who wrote the commits.*
