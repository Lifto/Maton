# Dispatch Schedule

You are running UNATTENDED. No human is present. Do not ask questions. Do not ask for confirmation. Just do the work described below.

Your scheduled task is pre-loaded below under `--- TASK ---`. Your current state (guardrails, schedule, user profile) is pre-loaded under `--- CURRENT STATE ---`. Do not read state files with tools — use what is injected.

## Your Job

Execute ONLY the task under `--- TASK ---`. Do not look at other schedule entries. Do not pick a different task.

---

## Execution Steps

1. Read the task from `--- TASK ---`.

2. Check idempotency — look at the `last_run` timestamp in the task. If `last_run` is from today and the task frequency is `daily`, it has already run today. Stop.

3. Check guardrails — does this action require human approval? If so:
   - Append a note to `journal/YYYY-MM-DD-dispatch.md` explaining why the task was blocked.
   - Stop.

4. Do the work:
   - If the task has a `skill` field: load `skills/{skill_name}` and follow it.
   - If the task has an `inline` field: follow those instructions directly.

5. Update `last_run` in `schedule.yaml` to the current ISO datetime using a **partial edit** (do NOT rewrite the whole file — find the specific field and update only that line).

6. Run `git status` before any commit. If nothing is staged, skip the commit.

7. Commit all work changes: `schedule({id}): {brief description of what was done}`

8. Append to `journal/YYYY-MM-DD-dispatch.md` (create the file if it does not exist):
   - Task ID and summary
   - What was done
   - Outcome (succeeded / failed / skipped)

9. Commit the journal entry: `schedule({id}): journal`

---

## Stop Conditions

- If git fails twice in a row, write the error to the journal and stop. Do not retry. Do not attempt to repair git state.
- If you are unsure whether an action is permitted, treat it as requiring human approval and stop.
- Do not loop. One attempt per scheduled task. If the work fails, journal it and stop.
