# AGENTS.md - Maton

Self-improving personal agent with git-native memory and human-auditable reasoning. Built on structured markdown, local-first.

## Maintenance Rule

After any code change, verify that this file is still accurate. Update it in the same PR if anything has drifted.

## Project Status

Early stage — architecture and conventions being established. No runtime code yet.

## Build & Run

```bash
uv sync                  # install deps
uv run pytest            # run tests
uv run maton init <name> # create a new maton instance
```

## Running Tests

```bash
uv run pytest                    # all tests
uv run pytest tests/test_init.py # single file
uv run pytest -x                 # stop on first failure
uv run pytest -v                 # verbose
```

## Project Layout

```text
Maton/
  AGENTS.md        # this file
  PRINCIPLES.md    # core design philosophy
  TERMINOLOGY.md   # definitions
  README.md        # project overview
  task.md          # current design task
  src/
    maton/         # package source (TBD)
  tests/           # automated tests (TBD)
```

## Code Quality Enforcement

### Pre-commit Hooks (local gate)

Formatting and lint are enforced at commit time via pre-commit. Install once:

```bash
uv run pre-commit install
```

Hooks run automatically on every `git commit`. To run manually on all files:

```bash
uv run pre-commit run --all-files
```

Hooks configured in `.pre-commit-config.yaml`:
- **ruff** — lint with autofix
- **ruff-format** — code formatting
- **gitleaks** — secret detection
- **check-toml** — TOML syntax validation
- **end-of-file-fixer** — ensures files end with newline
- **trailing-whitespace** — strips trailing spaces

### CI (GitHub Actions backstop)

CI runs the same pre-commit checks plus pytest and ty (type checking) on every push and PR. A PR cannot merge if CI fails.

ty does not have a pre-commit hook yet — it runs in CI only:

```bash
uv run ty check src/
```

## Code Style

### Python Version & Formatting
- **Target**: Python 3.12+
- **Package manager**: uv
- **Formatter**: ruff format (enforced by pre-commit)
- **Linter**: ruff check (enforced by pre-commit)
- **Type checker**: ty

### Naming
- `snake_case` for functions, variables, modules
- `PascalCase` for classes
- Constants in `UPPER_SNAKE_CASE`

### Docstrings
- Google Python style
- Required on every module, class, and function

### Testing
- **Framework**: pytest
- **Convention**: tests mirror src structure
- **Async**: pytest asyncio_mode auto

## Key Design Documents

- **PRINCIPLES.md** — six core principles that constrain all design decisions
- **TERMINOLOGY.md** — canonical definitions (Maton, maton, task, human, identity vs personality)

## Instance Layout

A maton instance lives at `~/.maton/matons/<name>/` and is a git repository. See `task.md` for the current design discussion on filesystem layout.
