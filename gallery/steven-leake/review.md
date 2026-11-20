# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Steven Leake  
**Project reviewed:** monarchx  
**Review period:** 2026-01-20 to 2026-01-20  
**Commits examined:** 1  
**Review date:** 2026-11-19  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: C (69/100)

*Meets some expectations. There is a conversation to be had.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Communication: A (100/100)

- 0 of 1 commit messages (0%) say almost nothing (average message length: 16 characters).
- 1 of 1 commits (100%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: A (100/100)

- 0 of 1 commits (0%) were made between 10pm and 5am.
- 0 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 0 commits are reverts (0%) and 0 (0%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: F (21/100)

- 46 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 1046 days (2.9 years). It has seniority now.
- Senior TODO on file: eslint.config.js:87 - ""react/prop-types": "off", // FIXME"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: F (22/100)

- 43 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 1264 days. It is not temporary. It is load-bearing.
- 0 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: A (100/100)

- Active on 1 of 1 days in the review period (100%).
- Longest streak: 1 days. Longest disappearance: 0 days.
- Average output on an active day: 1.0 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** server/swagger/openapi.json - 5,286 lines of churn across the review period. You two have history.
- **Largest single commit:** 5 lines changed in "Update README.md". A bold unit of work.
- **Weekend work:** 0 of 1 commits landed on a Saturday or Sunday.
- **Busiest day:** 2026-01-20, with 1 commits.
- **Languages by churn:** JavaScript (311,082 lines of churn), json (7,923 lines of churn), Markdown (5,161 lines of churn), Python (3,820 lines of churn).
- **Longest commit message:** "Update README.md" (16 characters. A novel.)
- **Shortest commit message:** "Update README.md". A haiku, if you squint.
- **Catchphrase:** "update", appearing 1 times across your commit subjects.
- **Net lines:** 5 added, 0 deleted.

## Awards

- **Fossil Keeper:** A TODO has survived 1046 days in the code. It qualifies for the pension plan.
- **Polyglot:** Meaningful churn in 42 languages. Jack of all trades, suspect in all of them.

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
