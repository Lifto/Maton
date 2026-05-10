# Dispatch Maintenance

You are running UNATTENDED. No human is present. Do not ask questions. Do not ask for confirmation. Just do the work described below.

The runner has determined that maintenance is needed. Run these checks in order:

---

## Maintenance Checks

1. **Git lock**: Check if `.git/index.lock` exists. If yes, remove it: `rm .git/index.lock`. Append a line to today's journal noting the lock was cleared.

2. **Stuck tasks**: Scan `backlog.yaml` for tasks with `status: in_progress`. For each:
   - Check if there is a journal entry from today or yesterday that mentions the task ID.
   - If no recent journal entry exists, set `status` to `blocked`, add `blocked_by: [human]`, and add a note: "stuck in_progress — no recent journal activity".
   - Use a partial edit. Do NOT rewrite the whole file.

3. **Seed update**: Check if `skills/update.md` exists. If yes, read it and follow its instructions exactly.

4. **Journal review**: Read the last 3 journal entries in `journal/`. If you notice a repeating failure pattern across entries, append a note to `self.md` under an "Observations" section describing the pattern. Use a partial edit.

---

## After Checks

- If any changes were made: run `git status`, stage changed files, and commit with: `maintenance: {brief summary of what was fixed}`
- If nothing needed fixing: append a one-line entry to `journal/YYYY-MM-DD-dispatch.md` (create if it does not exist): `maintenance: all clear`. Commit: `maintenance: all clear`

---

## Stop Conditions

- If git fails twice in a row, write the error to the journal and stop. Do not retry. Do not attempt to repair git state.
- Do not execute backlog tasks. Do not run scheduled items. Do not ideate.
- One pass through the checks. Do not loop.
