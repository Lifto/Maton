# Principles

Maton is a self-improving personal agent running on local hardware. Its value is measured by what it does, not by how clever it is. These principles constrain every design decision.

## 1. Structure is cognition

Weaker models with good scaffolding outperform stronger models with none. The agent's knowledge, tasks, and reasoning live in structured markdown files organized in directories. This structure is the agent's external mind — it doesn't need to hold everything in context, it needs to know where to look.

Markdown is the format because it is native to both humans and LLMs. No database, no embeddings store, no binary formats. If a person can't open a folder and read the files to understand what the agent knows and is doing, the design has failed.

## 2. Git is memory

All agent state — knowledge, skills, task history, configuration — lives in a git repository. This gives us:

- **History**: when did the agent learn this, and from what?
- **Diff**: what changed between when it worked and when it didn't?
- **Rollback**: revert a bad skill or a wrong memory.
- **Branching**: the agent works on a branch and merges only on success.

The agent does not "remember" things. It commits them.

## 3. Human-readable machinery

Every piece of the system is observable by reading files. A person can open the agent's working directory, read the markdown, and understand exactly what it knows, what it's working on, what it tried, what failed, and why. This builds the trust required to grant the agent more autonomy over time.

This also means a human participates through the same interface as the agent. Drop a task file in the right directory and the agent picks it up. No API, no special interface — just a file in a folder.

## 4. Verification before commitment

Self-improvement without verification is drift. Every task carries its own definition of success. After the agent acts, it runs the check. If the check passes, the change is committed. If not, it is reverted. Failed attempts are preserved in history as evidence of what didn't work.

The hard part is defining good checks for fuzzy tasks. The structured task format helps — concrete acceptance criteria that even a small model can evaluate against.

The loop: act → verify → commit or revert → learn.

Without the verify step, it's just act → hope.

## 5. Recursive uniformity

A task is a task is a task. When a task spawns a task, the child is the same class as the parent. Same structure, same acceptance criteria, same verify-then-commit cycle. No "subtask" type, no "parent task" type.

This means:
- The agent's self-improvement work is just tasks.
- A human can inject a task at any level and it looks identical to one the agent created.
- Tasks compose naturally — a task's acceptance criteria can include "these child tasks all passed."
- The task tree is observable by walking directories.

## 6. OS-native

The filesystem is the most mature interface in computing. Text files are the most robust format across time. Git is the most proven versioning system. These are not implementation choices — they are the foundation.

Build on the operating system's primitives instead of building abstractions on top of them. Use the verbs of the filesystem (read, write, mkdir, mv) the way REST uses the verbs of HTTP. The less custom machinery, the stronger and more minimal the system.
