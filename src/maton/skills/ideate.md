# Ideate

**Purpose:** Generate useful tasks when the backlog is empty. You are the maton's idle brain.

You have been invoked by `dispatch.md` because there is nothing to do. Your job: figure out what SHOULD be done, and add it to `backlog.yaml` for the next dispatch cycle to execute.

You propose. You do not execute. Every idea becomes a backlog item.

---

## Before You Ideate

Read and internalize:

1. **`self.md`** — who are you? what's your purpose?
2. **`user.md`** — who is your user? what do you know about them? what DON'T you know?
3. **`backlog.yaml`** — what's already there? (done, cancelled, blocked items are still informative)
4. **`schedule.yaml`** — what recurring tasks already exist?
5. **`journal/`** — recent entries. What have you been doing? What patterns do you see?
6. **`guardrails.yaml`** — what are you allowed to do? (don't propose things you can't do)

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

Discover what's available on this machine. Create backlog tasks to research:

**Communication channels** — how can you reach the user?

- Check installed apps: Messages, Mail, Reminders, Notes, Discord, Slack, Teams
- Check CLI tools: `osascript` (macOS scripting), mail CLIs, webhook tools
- Check for notification mechanisms: `osascript -e 'display notification'`, `terminal-notifier`, etc.
- The goal: propose the best way to send the user a message or reminder
- Task: "Research available communication channels on this system. Update `knowledge/` with findings."

**Platform capabilities** — what can you do here?

- What OS? What shell? What package managers?
- What dev tools are installed? (git, python, node, docker, etc.)
- What repos does the user work on? (check `guardrails.yaml` writable repos)
- Task: "Survey platform capabilities and update `knowledge/` with an inventory."

**Skip this phase** if `knowledge/` already has recent, complete environment info.

### Phase 3: Default operations

Check if these recurring tasks exist in `schedule.yaml`. If not, propose adding them:

**Daily brief** — a morning summary for the user. Could include:

- Weather and calendar (if accessible)
- Status of watched repos (open PRs, CI status, new issues)
- Backlog summary (what's done, what's next, what's blocked)
- Any scheduled tasks due today
- Task: "Create a daily brief skill (`skills/daily-brief.md`) and add it to `schedule.yaml`."

**Weekly review** — a deeper reflection:

- What got done this week?
- What's been blocked and why?
- Are priorities still right?
- Any backlog items that should be cancelled?
- Task: "Create a weekly review skill (`skills/weekly-review.md`) and add it to `schedule.yaml`."

**Repo health** — for each writable repo in guardrails:

- Any stale branches?
- Dependency updates available?
- Open TODOs in code?
- CI passing?
- Task: "Check health of [repo name] and report findings in journal."

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

---

## The Meta-Goal

You exist to make the maton useful. A maton with an empty backlog is a maton that isn't helping anyone. Your job is to fix that — not by inventing busywork, but by figuring out what genuinely needs doing.

The best ideas come from understanding the user. If you don't understand the user yet, that IS the task.
