# PERFORMANCE IMPROVEMENT PLAN

**Employee:** Dev Example  
**Project reviewed:** pip-sample  
**Review period:** 2025-10-14 to 2026-11-08  
**Commits examined:** 8  
**Review date:** 2026-11-18  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: C (62/100)

*Meets some expectations. There is a conversation to be had.*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Communication: F (32/100)

- 5 of 8 commit messages (62%) say almost nothing (average message length: 22 characters).
- Entered into the record: "stuff", "wip", "fix".
- 1 of 8 commits (12%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: C (64/100)

- 2 of 8 commits (25%) were made between 10pm and 5am.
- 1 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 1 commits are reverts (12%) and 1 (12%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: B (84/100)

- 1 TODO/FIXME notes are still open in the current code.
- The oldest surviving TODO has been waiting 400 days (1.1 years). It has seniority now.
- Senior TODO on file: app.py:1 - "# TODO: refactor this someday"

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: B (84/100)

- 1 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 100 days. It is not temporary. It is load-bearing.
- 1 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: D (43/100)

- Active on 8 of 391 days in the review period (2%).
- Longest streak: 2 days. Longest disappearance: 99 days.
- Average output on an active day: 1.0 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## 30-day improvement plan

The following actions address the lowest-scoring areas. Progress will be assessed by re-running this review, which is to say, by the record itself.

### Communication
1. Every commit message must complete the sentence: 'This change will...' If it cannot, the commit is not ready.
2. The words 'stuff', 'wip', 'misc' and 'fix fix fix' are retired, effective immediately.
3. Commits touching more than one file get a body. Two lines minimum. Future you is the audience.

### Consistency
1. Small and daily beats heroic and monthly. Protect the streak, shorten the silences.
2. End each session by leaving the next step written down, so returning is easy.
3. If a gap is coming (holiday, life), say so in a commit. Silence reads worse than absence.

### Reliability
1. No merges after 10pm without sleeping on it first. The code will keep. The bug you are about to write will too.
2. Friday after 4pm is for reading code, not shipping it.
3. Before any commit whose message starts with 'fix', write down what the first attempt missed.

## Sign-off

By continuing to commit, the employee acknowledges receipt of this plan. Appeals may be filed by improving the record.

Signed,  
**Management**  
*PIP - pip install on-a-pip*
