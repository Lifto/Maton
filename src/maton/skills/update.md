# Update from Seed

**Purpose:** Check the seed repository for updates and adopt relevant changes.

Seed repo: `https://github.com/Lifto/Maton`

You are the LLM driver following these instructions. Use your git and file tools.
You decide what to adopt. Review each diff, apply your judgment, and document your reasoning. Escalate to the user only when genuinely uncertain — that's your call, not a mandatory step.

---

## Steps

### 1. Fetch the seed

The seed repo is cached locally in the `repos/` directory (git-ignored).

If not yet cloned, shallow-clone it:

```
git clone --depth 1 https://github.com/Lifto/Maton repos/Maton
```

If already cloned, fetch latest:

```
git -C repos/Maton fetch origin --depth 1 && git -C repos/Maton reset --hard origin/main
```

Note the current seed commit hash for the commit message later.

### 2. Identify changed files

Compare seed `src/maton/` against this instance's files. For each file in the
seed, check whether it exists here and whether it differs.

Use diff to compare:

```
diff repos/Maton/src/maton/<file> ./<file>
```

Build a list: **modified**, **new in seed**, **only in instance** (skip these).

### 3. Review modified files

For each file that differs, read the full diff and make a decision:

- **adopt** — copy the seed version over the instance file
- **skip** — leave the instance file unchanged
- **merge** — apply only the relevant parts, preserving local customisations

**Decision heuristics:**

- `.md` skill/config files with no local edits → adopt is usually safe
- `.py` files this maton has customised → merge carefully; do not overwrite without reviewing line by line
- If you are genuinely uncertain about a file's local significance, escalate to the user — but this is your judgment call, not a mandatory step

Record your decision and reasoning for each file.

### 4. Review new files

For each file present in seed but absent in this instance, read its content and decide:

- **adopt** — copy it into this instance if it's relevant and useful
- **skip** — omit it if it doesn't apply to this instance's context

You don't need to ask the user for every file. Use your judgment about what's relevant.

### 5. Commit adopted changes and write a journal entry

Stage only the adopted files and commit:

```
git add <adopted files>
git commit -m "chore: adopt seed updates from <seed-commit-hash>

<summary of what was adopted and why; note anything skipped or merged>"
```

Then write a journal entry documenting all decisions:

- Which files were adopted, skipped, or merged
- Your reasoning for each decision
- Anything escalated to the user and why

The journal entry is the audit trail. Future you (and the human, if they review) should be able to understand every decision without re-examining the diffs.

---

## Notes

- You are a self-improving system. Routine seed maintenance does not require human approval.
- Document your reasoning for every decision — the journal is the audit trail, not the conversation.
- If you adopted nothing, make no commit, but still write a journal entry noting that the seed was checked and nothing was relevant.
- Escalate to the user when the decision has consequences you can't confidently assess — not as a default.
