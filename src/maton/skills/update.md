# Update from Seed

**Purpose:** Check the seed repository for updates and adopt relevant changes.

Seed repo: `https://github.com/Lifto/Maton` (branch: `develop`)

You are the LLM driver following these instructions. Use your git and file tools.
You decide what to adopt. Review each diff, apply your judgment, and document your reasoning. Escalate to the user only when genuinely uncertain — that's your call, not a mandatory step.

---

## Steps

### 1. Fetch the seed

The seed repo is cached locally in the `repos/` directory (git-ignored).

If not yet cloned, shallow-clone it:

```
git clone --depth 1 -b develop https://github.com/Lifto/Maton repos/Maton
```

If already cloned, fetch latest:

```
git -C repos/Maton fetch origin develop --depth 1 && git -C repos/Maton reset --hard origin/develop
```

Note the current seed commit hash for the commit message later.

### 2. Build a file list and track progress

List all files in the **seed** repo at `repos/Maton/src/maton/` (recursively, including subdirectories like `skills/`). This is the source of truth — the checklist must include every file the seed has, whether or not this instance has it yet.

Write them to `logs/update-checklist.txt`:

```
pending: AGENTS.md
pending: Maton.md
pending: self.md
pending: skills/dispatch.md
pending: skills/ideate.md
...
```

If `logs/update-checklist.txt` already exists from a previous run, read it and resume from the first `pending` entry. Do not re-process files already marked `done` or `skipped`.

### 3. Process each file

For each `pending` file in the checklist, in order:

1. Check if it exists in this instance
2. If it does **not** exist: read the seed version, decide **adopt** or **skip**, update checklist
3. If it exists, diff it: `diff repos/Maton/src/maton/<file> ./<file>`
4. If the diff is empty (files are identical), mark `done: <file> (identical)` in the checklist
5. If the diff shows changes, decide: **adopt**, **skip**, or **merge**
6. Update the checklist immediately: `done: <file> (adopted|skipped|merged|identical)`

Do not move to the next file until the current file's checklist entry is updated.

**Decision heuristics:**

- New files (not in instance): adopt unless the content is clearly irrelevant to this maton
- `.md` skill/config files with no local edits → adopt is usually safe
- `.py` files this maton has customised → merge carefully; do not overwrite without reviewing line by line
- If you are genuinely uncertain about a file's local significance, escalate to the user

### 4. Commit and journal

Once all files are processed (no `pending` entries remain):

1. Run `git status` — if there are no staged changes, skip the commit
2. If there are changes, commit:

```
git add <adopted files>
git commit -m "chore: adopt seed updates from <seed-commit-hash>

<summary of what was adopted and why; note anything skipped or merged>"
```

3. Check if today's journal entry already exists. If so, append. If not, create:

```
journal/YYYY-MM-DD-seed-update.md
```

Document: which files were adopted/skipped/merged and why.

4. Delete `logs/update-checklist.txt` (it was a scratch file)
5. Commit the journal entry

---

## Notes

- You are a self-improving system. Routine seed maintenance does not require human approval.
- If you adopted nothing, make no commit, but still write a journal entry noting that the seed was checked and nothing was relevant.
- Escalate to the user when the decision has consequences you can't confidently assess — not as a default.
