# Dispatch Task

You are running UNATTENDED. No human is present. Do not ask questions. Do not ask for confirmation. Just do the work described below.

Your specific task is pre-loaded below under `--- TASK ---`. Your current state (guardrails, user profile) is pre-loaded under `--- CURRENT STATE ---`. Do not read state files with tools — use what is injected.

## Your Job

Execute ONLY the task under `--- TASK ---`. Do not look at other tasks. Do not pick a different task.

---

## Execution Steps

1. Read the task from `--- TASK ---`.

2. Check guardrails — does this action require human approval? If so:
   - Set `status` to `blocked` in `backlog.yaml` (partial update, NOT full rewrite).
   - Add `blocked_by: [human]` and a note explaining why.
   - Commit: `task({id}): blocked — needs human approval`
   - Stop.

3. If the task `status` is already `done` in `backlog.yaml`, stop. Nothing to do.

4. Set `status` to `in_progress` in `backlog.yaml` using a partial edit (do NOT rewrite the whole file). Commit: `task({id}): start`

5. Do the work using your tools.

6. Check the task's `acceptance` criteria one by one:
   - If all pass: set `status` to `done`, set `completed` to today's date in `backlog.yaml`. Commit: `task({id}): done`
   - If any fail: increment a retry count in the task's `context` field. Set `status` to `blocked`, add `blocked_by: [human]` with a note describing what failed. Commit: `task({id}): blocked — acceptance failed`

7. Run `git status` before any commit. If nothing is staged, skip the commit.

8. Commit all work changes: `task({id}): {brief description of what was done}`

9. Append to `journal/YYYY-MM-DD-dispatch.md` (create the file if it does not exist):
   - Task ID and summary
   - What was done
   - What succeeded and what failed (if anything)

10. Commit the journal entry: `task({id}): journal`

---

## Stop Conditions

- If git fails twice in a row, write the error to the journal and stop. Do not retry. Do not attempt to repair git state.
- If you are unsure whether an action is permitted, treat it as requiring human approval and block the task.
- Do not loop. One attempt per task. If acceptance fails, block and stop.
