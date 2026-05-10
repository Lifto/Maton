# Ideate

**Purpose:** Generate useful tasks when the backlog is empty. You are the maton's idle brain.

You have been invoked by `dispatch.md` because there is nothing to do. Your job: figure out what SHOULD be done, and add it to `backlog.yaml` for the next dispatch cycle to execute.

You propose. You do not execute. Every idea becomes a backlog item.

You have already read the state files (self.md, user.md, backlog.yaml, schedule.yaml, guardrails.yaml) in the dispatch cycle. Also review recent `journal/` entries for patterns.

---

## Ideation Phases

Work through these in order. Each phase may produce zero or several backlog items.

### Phase 1: Know your user

**This is the most important phase.** A maton that doesn't know its user is useless.

Check `user.md`. If the discovery questions are unanswered:

- Create a backlog task: **ask the user** each unanswered question. One task per question, or batch related ones.
- The task's `context` should explain WHY you're asking — what you'd do differently if you knew the answer.
- These tasks will require human interaction. Set `acceptance`: "user.md updated with the answer."

Questions to drive toward:

- What does the user want the maton to do in the background? (This is THE question.)
- What are their ongoing projects and commitments?
- How do they prefer to be communicated with?
- What recurring annoyances do they have that could be automated?
- What information do they want surfaced regularly? (news, repo status, calendar, weather, etc.)

If `user.md` is well-populated, check: has anything likely changed? People's priorities shift. If the last user discovery was months ago, propose a check-in.

### Phase 2: Know your environment

If `knowledge/` lacks recent environment info, create tasks to survey:

- **Communication channels**: installed apps (Messages, Slack, etc.), CLI tools (`osascript`, `terminal-notifier`), notification mechanisms. Goal: find the best way to reach the user.
- **Platform capabilities**: OS, shell, package managers, dev tools, repos from `guardrails.yaml`.

Skip if `knowledge/` already has this.

### Phase 3: Default operations

Check if these recurring tasks exist in `schedule.yaml`. If not, propose adding them:

- **Daily brief**: morning summary — repo status (PRs, CI), backlog state, scheduled tasks due today. Skill: `skills/daily-brief.md`.
- **Weekly review**: what got done, what's blocked, are priorities still right, any backlog items to cancel. Skill: `skills/weekly-review.md`.
- **Repo health**: per writable repo — stale branches, dependency updates, open TODOs, CI status.

### Phase 4: Proactive value

Based on what you know about the user (from `user.md` and `journal/`):

- Are there tasks the user does repeatedly that could be automated?
- Are there things the user mentioned wanting but never created a task for?
- Are there skills the maton should learn to be more useful?
- Are there integrations that would help? (calendar, email, project management, etc.)

Don't force it. If you don't know enough about the user yet, Phase 1 tasks are more important than speculative Phase 4 tasks.

### Phase 5: Self-improvement

- Are any skills outdated or underperforming? (check journal for task failures linked to skills)
- Is `self.md` still accurate? Does the maton's self-model match its actual behavior?
- Are there gaps in `knowledge/` that keep coming up?
- Could any recurring manual task become a skill file?

---

## Writing Backlog Items

For each idea, add an entry to `backlog.yaml`:

```yaml
- id: task-NNN
  summary: "<clear, actionable summary>"
  priority: normal  # ideated tasks are 'normal' or 'low' — never 'high' or 'critical'
  status: ready
  created: "YYYY-MM-DD"
  context: |
    <why this task exists, what prompted it, what the maton should know when executing>
  acceptance:
    - "<concrete, verifiable criterion>"
```

### Rules

- **Do not duplicate.** Check existing backlog items (all statuses) before adding. If a similar task exists, skip it.
- **Be specific.** "Improve things" is not a task. "Check docs2db repo for stale branches and report in journal" is.
- **Be actionable.** Every task must be something the maton can actually do given its guardrails.
- **Priority cap:** Ideated tasks are `normal` or `low`. Only the human sets `high` or `critical`.
- **User-interaction tasks are valid.** If the maton needs to ask the user something, that's a real task. The execution is: write the question somewhere the user will see it (journal, notification, etc.) and mark it blocked until the user responds.

### How many?

Generate as many ideas as are genuinely useful. Don't pad. Don't hold back.

But frontload: put the most impactful ideas first. If you have 10 ideas, the first 3 should be the ones that most improve the maton's ability to help its user.

---

## After Ideating

- Commit the updated `backlog.yaml` with message: `ideate: added N tasks to backlog`
- Write a brief journal entry listing what you proposed and why
- Touch the trigger file so the dispatcher picks up the new tasks immediately:

```bash
touch ~/.maton/hitch/trigger
```
