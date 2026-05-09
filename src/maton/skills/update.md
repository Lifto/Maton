# Update from Seed

**Purpose:** Check the seed repository for updates and adopt relevant changes.

Seed repo: `https://github.com/Lifto/Maton`

You are the LLM driver following these instructions. Use your git and file tools.
Do NOT auto-adopt — always show the user what changed and let them decide.

---

## Steps

### 1. Fetch the seed

Clone or fetch the seed repo to a temporary location:

```
git clone https://github.com/Lifto/Maton /tmp/maton-seed
```

If already cloned, fetch latest:

```
git -C /tmp/maton-seed fetch origin && git -C /tmp/maton-seed reset --hard origin/main
```

Note the current seed commit hash for the commit message later.

### 2. Identify changed files

Compare seed `src/maton/` against this instance's files. For each file in the
seed, check whether it exists here and whether it differs.

Use diff to compare:

```
diff /tmp/maton-seed/src/maton/<file> ./<file>
```

Build a list: **modified**, **new in seed**, **only in instance** (skip these).

### 3. Review modified files

For each file that differs, show the user the full diff output. Ask:

> "Seed has changes to `<file>`. Adopt this change? (yes / no / merge manually)"

- **yes** — copy the seed version over the instance file
- **no** — skip
- **merge manually** — open both versions side by side and let the user edit

> ⚠️ Python files (`.py`) may have been customised in this instance.
> Merge carefully — do NOT overwrite without reviewing line by line.

### 4. Review new files

For each file present in seed but absent in this instance, show its full content.
Ask:

> "Seed has new file `<file>`. Add it to this instance? (yes / no)"

### 5. Commit adopted changes

After all decisions are made, stage only the adopted files and commit:

```
git add <adopted files>
git commit -m "chore: adopt seed updates from <seed-commit-hash>"
```

Use the seed commit hash noted in Step 1.

---

## Notes

- Skills files (`.md`) are safe to overwrite unless you have local edits.
- Never adopt changes blindly — the diff review in Steps 3–4 is mandatory.
- If the user declines all changes, make no commit.
