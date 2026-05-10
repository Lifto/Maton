# Dispatch

**Purpose:** Find the next unit of work and execute it. This is the entry point for the perpetual loop.

You are the LLM driver following these instructions. You have been invoked by the hitch (an OS-level scheduler). You may be running unattended — the human may not be present. Act accordingly: be conservative, follow guardrails, and leave clear audit trails.

---

## Before You Do Anything

Read these files in order. Do not skip any.

1. **`self.md`** — who you are, what you're here to do
2. **`user.md`** — who your human is, what they care about
3. **`guardrails.yaml`** — what you are and are not allowed to do
4. **`schedule.yaml`** — recurring tasks and their due times
5. **`backlog.yaml`** — the task queue

If any file is missing or corrupt, write an error entry to `journal/` and exit without touching trigger. The deadman timer will retry.

---

## Decision: What To Do

Work through this priority list. Execute the **first** category that has actionable work:

### Priority 1: Scheduled tasks that are due

Check `schedule.yaml`. For each enabled recurring task:

- Parse `last_run` and `frequency`/`time`/`day`
- If the task is due (current time ≥ next scheduled time), execute it
- After execution, update `last_run` to the current datetime
- If the task has a `skill` field, load and follow that skill file
- If the task has an `inline` field, follow those instructions directly

### Priority 2: Backlog tasks that are ready

Check `backlog.yaml`. Find tasks where:
- `status` is `ready`
- `blocked_by` is empty or all referenced tasks are `done`

From the eligible tasks, pick the one with the highest priority. Ties are broken by `created` date (oldest first).

### Priority 3: Self-maintenance

If no scheduled tasks are due and no backlog tasks are ready:

1. Check `skills/update.md` — is a seed update due?
2. Review recent `journal/` entries — any patterns worth noting in `self.md`?
3. Scan for stale tasks in `backlog.yaml` (status `in_progress` for >24h with no journal activity — these may be stuck)

If self-maintenance produces work, do it.

### Priority 4: Ideation

If the backlog has no `ready` tasks after Priorities 1-3:

1. Load and follow `skills/ideate.md`
2. The ideation skill reads your state files, discovers your environment, and generates new backlog items
3. After ideation, touch the trigger file so the next dispatch cycle picks up the new tasks

This ensures the maton is never truly idle — if there's nothing to do, figuring out what to do IS the task.

### Priority 5: Nothing to do

If ideation produced no new tasks (everything was already covered):

1. Write a brief journal entry: `"dispatch: no actionable work, ideation found nothing new"`
2. Do NOT touch the trigger file
3. Exit

The deadman timer will check again later.

---

## Executing a Task

For each task you execute:

### 1. Mark in-progress

Update `backlog.yaml`: set the task's `status` to `in_progress`.

### 2. Check guardrails

Before acting, compare your planned actions against `guardrails.yaml`:

- **Repository access**: Am I modifying files in a writable repo? Am I on an allowed branch?
- **Action permissions**: Am I allowed to do this? (commit, create files, run commands, fetch web)
- **Escalation rules**: Does this action match any escalation rule?

If any guardrail is violated:
- Set the task's `status` to `blocked`
- Add `blocked_by: ["human"]`
- Add a note in the task's `context` explaining what guardrail was hit
- Move to the next task

### 3. Execute

Do the work. Use your tools (file read/write, git, shell commands, web fetch) as needed.

Follow the task's context and acceptance criteria closely. If the task has a `skill` field, load and follow that skill file.

### 4. Verify

Check the task's `acceptance` criteria. For each criterion:
- Can you verify it passed? (file exists, test passes, content matches)
- If yes, mark it satisfied
- If no, note what failed

### 5. Record result

If all acceptance criteria pass:
- Set `status` to `done`
- Set `completed` to current date
- Write a brief `result` summary
- Commit all changes with a descriptive message

If acceptance criteria fail:
- Increment a retry counter (track in the task's `context`)
- If retries < `limits.max_retries` from `guardrails.yaml`, set `status` back to `ready`
- If retries ≥ limit, set `status` to `blocked` and add `blocked_by: ["human"]`
- Do NOT commit broken work. Revert if needed.

### 6. Journal

Write a journal entry for this dispatch session:

```
journal/YYYY-MM-DD-dispatch-summary.md
```

Include:
- What tasks were attempted
- What succeeded, what failed, what was skipped
- Any observations or concerns for the human
- Time spent (approximate)

Commit the journal entry.

---

## After All Tasks

### Resource limits

Check `guardrails.yaml` → `limits`:
- Have you hit `max_tasks_per_session`? → stop, even if more tasks are ready
- Have you hit `max_commits_per_session`? → stop

### Self-reschedule decision

Determine whether to touch the trigger file:

**Touch trigger** (run again immediately) if:
- There are more `ready` tasks in the backlog
- A scheduled task is overdue
- You were cut short by resource limits and want to continue

**Do NOT touch trigger** (wait for deadman) if:
- No more actionable work
- You hit a guardrail and need human input
- Quiet hours are approaching (check `guardrails.yaml` → `quiet_hours`)

To self-reschedule:

```bash
touch ~/.maton/hitch/trigger
```

To set a cooldown (don't run for a while):

```bash
echo "2026-05-10T07:00:00-04:00" > ~/.maton/hitch/cooldown
```

---

## Error Handling

- Never leave `backlog.yaml` corrupt. If you can't update it cleanly, don't update it.
- Task errors → mark `blocked`, write error to `context`, journal the failure.
- Infrastructure errors (can't read files, git broken) → write to `logs/`, exit. Don't touch trigger.

Commit all meaningful changes (backlog status, journal entries, task work, schedule updates). Prefix commit messages with `dispatch:`.
