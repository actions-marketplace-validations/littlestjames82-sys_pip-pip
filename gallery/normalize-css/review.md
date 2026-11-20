# PERFORMANCE IMPROVEMENT PLAN

**Employee:** battaglr  
**Project reviewed:** normalize-css  
**Review period:** 2015-04-02 to 2016-06-30  
**Commits examined:** 10  
**Review date:** 2026-11-19  
**Reviewer:** Management (PIP, running locally on the employee's own machine)

## Overall assessment: B (75/100)

*Meets and often exceeds expectations. Keep doing most of this.*
*Review style: Corporate*

This review is based entirely on the employee's own git history, the work diary every programmer keeps without meaning to. All findings below are drawn from that record. No code left this machine in the preparation of this document; the evidence was already here.

## Authorship

- **Share of the record:** 10 of 360 commits in this history (3%) are by battaglr. The remaining 350 are by 41 other authors.
- **Most of the rest:** Nicolas Gallagher (208 commits), Jonathan Neal (95 commits), Aleks Hudochenkov (4 commits).
- **Arrival:** the history starts 2011-04-21; battaglr's first commit is 2015-04-02, and 238 commits predate it.
- **Authorship: mostly inherited.** The bulk of this record was written by other people before the reviewed author arrived. The grades in this review describe that record, not one person's work, and should be read that way.

## Communication: A (100/100)

- 0 of 10 commit messages (0%) say almost nothing (average message length: 35 characters).
- 2 of 10 commits (20%) include any explanation beyond the subject line.

**Management notes:** Commit messages are the only explanation future maintainers get. When you write a real message, it tends to be a genuinely useful one.

## Reliability: B (86/100)

- 3 of 10 commits (30%) were made between 10pm and 5am.
- 0 commits landed on a Friday at or after 4pm, the industry's most dangerous hour.
- 0 commits are reverts (0%) and 0 (0%) begin with the word 'fix'.

**Management notes:** Work shipped tired, or shipped twice, costs the team twice. A low revert habit, where present, is the mark of someone who checks before they ship.

## Follow-through: A (100/100)

- 0 TODO/FIXME notes are still open in the current code.

**Management notes:** A TODO is a promise. Old TODOs are promises in default. Every TODO you do close is one the next person never has to meet.

## Judgment: D (54/100)

- 2 spots in the code are labelled temporary, a hack, or a workaround.
- The oldest 'temporary' measure has been in production 5204 days. It is not temporary. It is load-bearing.
- 0 commits were checked in openly marked as work in progress.

**Management notes:** Temporary is the most permanent word in software. Labelling a hack as a hack is honesty many developers skip entirely.

## Consistency: F (34/100)

- Active on 6 of 456 days in the review period (1%).
- Longest streak: 1 days. Longest disappearance: 346 days.
- Average output on an active day: 1.7 commits.

**Management notes:** Bursts followed by silence are harder on a project than a steady pace. Showing up regularly is most of the job, and it is the part nobody can automate.

## Additional findings

- **Nemesis file:** normalize.css - 4,286 lines of churn across the review period. You two have history.
- **Largest single commit:** 285 lines changed in "Update and organize the normalize.css file". A bold unit of work.
- **Weekend work:** 3 of 10 commits landed on a Saturday or Sunday.
- **Busiest day:** 2016-03-14, with 4 commits.
- **Languages by churn:** CSS (4,686 lines of churn), HTML (2,365 lines of churn), Markdown (1,060 lines of churn), json (313 lines of churn).
- **Longest commit message:** "Use explicit `outline-width` property instead of `outline`" (58 characters. A novel.)
- **Shortest commit message:** "Remove double space". A haiku, if you squint.
- **Catchphrase:** "remove", appearing 4 times across your commit subjects.
- **Net lines:** 157 added, 169 deleted.

## Awards

- **Night Owl:** 30% of all commits landed between 10pm and 5am. The codebase's second shift.
- **The Ghost:** Vanished for 346 days once, then returned as if nothing happened. It had, in fact, happened.
- **Weekend Warrior:** 30% of commits landed on a Saturday or Sunday. The roadmap thanks you. The weekend does not.
- **Polyglot:** Meaningful churn in 9 languages. Jack of all trades, suspect in all of them.

## 30-day improvement plan

The following actions address the lowest-scoring areas. Progress will be assessed by re-running this review, which is to say, by the record itself.

### Consistency
1. Small and daily beats heroic and monthly. Protect the streak, shorten the silences.
2. End each session by leaving the next step written down, so returning is easy.
3. If a gap is coming (holiday, life), say so in a commit. Silence reads worse than absence.

### Judgment
1. Every 'temporary' fix gets an expiry date in the comment. When the date passes, it gets reviewed first, not last.
2. Count the hacks monthly. The number going down is the goal; the number existing is not the shame.
3. No new workaround merges without a note explaining what the real fix would take.

### Reliability
1. No merges after 10pm without sleeping on it first. The code will keep. The bug you are about to write will too.
2. Friday after 4pm is for reading code, not shipping it.
3. Before any commit whose message starts with 'fix', write down what the first attempt missed.

## Sign-off

By continuing to commit, the employee acknowledges receipt of this plan. Appeals may be filed by improving the record.

Signed,  
**Management**  
*PIP - pip install on-a-pip*

*Not for employment decisions. PIP grades a commit record, not a person, and it reads best when the person reading it is the person who wrote the commits.*
