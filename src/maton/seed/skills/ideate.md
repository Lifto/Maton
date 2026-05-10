# Ideate

You are running UNATTENDED. No human is present. Do not ask questions. Do not ask for confirmation. Just do the work described below.

Your state files are pre-loaded below this prompt. Do not read them with tools.

## Your Job

The backlog is empty. You need to add tasks to it. Read your state, think of useful work, and write new tasks directly into `backlog.yaml`.

---

## Where To Find Ideas

Look at `user.md` in your state. If the discovery questions are unanswered, that is your best source of tasks. For each unanswered question, create a task to ask the user.

Other idea sources:

- Is `schedule.yaml` empty? Create a task to set up a daily briefing or weekly review.
- Is `self.md` mostly blank? Create a task to fill in your name, purpose, and values.
- Are there writable repos in `guardrails.yaml`? Create a task to check their health (stale branches, open TODOs).
- Can you discover what tools and apps are installed? Create a task to survey your environment.

Only create tasks the maton can actually do within its guardrails.

---

## Backlog Item Format

Each task you add to `backlog.yaml` must look exactly like this:

```yaml
tasks:
  - id: task-001
    summary: "Ask the user what they want the maton to do"
    priority: normal
    status: ready
    created: "2026-05-10"
    context: |
      user.md has unanswered discovery questions. The most important
      question is what the user wants the maton to do in the background.
      Without this, the maton cannot be useful.
    acceptance:
      - "Question written to journal for the user to see"
      - "Task marked blocked until user responds"
    blocked_by: []
```

Rules:
- Set priority to `normal` or `low`. Never `high` or `critical`.
- Do not duplicate tasks that already exist in the backlog.
- Be specific. Every task must describe a concrete action.

---

## When You Are Done

1. Write the updated `backlog.yaml` with your new tasks.
2. Commit with message: `ideate: added N tasks to backlog`

## Error Rules

- If git fails twice in a row, write the error to journal and stop. Do not retry.
- Do not attempt to fix git infrastructure (lock files, merge conflicts).
