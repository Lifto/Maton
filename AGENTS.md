# AGENTS.md - Maton

Self-improving personal agent with git-native memory and human-auditable reasoning. Built on structured markdown, local-first.

## Maintenance Rule

After any code change, verify that this file is still accurate. Update it in the same PR if anything has drifted.

## Project Status

Early stage — CLI (`init`, `ask`, `hitch install/uninstall`), packaged `Maton.md` template, hitch runner, and tests are in place.

## Build & Run

```bash
uv sync                  # install deps
uv run pytest            # run tests
uv run maton init        # create a new maton instance
uv run maton hitch install <instance-dir>   # install platform scheduling
uv run maton hitch uninstall <instance-dir> # remove platform scheduling
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
    maton/              # package source
      __init__.py
      ask.py            # `maton ask`
      cli.py            # Typer entrypoint
      init.py           # `maton init`
      seed/             # copied to each instance by `maton init`
        AGENTS.md       # instance LLM bootstrap
        Maton.md        # getting-started guide
        self.md         # identity seed
        user.md         # user discovery seed
        guardrails.yaml # permission model
        schedule.yaml   # recurring tasks
        backlog.yaml    # task queue
        skills/
          dispatch.md   # dispatcher skill
          ideate.md     # idle-brain ideation skill
          update.md     # seed update skill
          perpetual-loop.md  # architecture reference
      hitch/            # scheduling infrastructure (not copied to instances)
        __init__.py
        runner.py       # dispatch cycle: guards → route → assemble prompt → invoke LLM
        platform.py     # launchd/systemd install/uninstall
  tests/           # pytest
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

A maton instance lives at `~/.maton/matons/maton-YYYYMMDD-HHMMSS/` and is a git repository.
It contains only seed files — no Python package code.

```text
~/.maton/matons/maton-YYYYMMDD-HHMMSS/
├── .git/
├── .gitignore
├── AGENTS.md
├── Maton.md
├── self.md
├── user.md
├── guardrails.yaml
├── schedule.yaml
├── backlog.yaml
├── journal/
│   └── .gitkeep
├── hitch/             (git-ignored, created by init)
│   └── config.yaml    (model, timeout — edit before hitch install)
├── logs/              (git-ignored)
└── skills/
    ├── dispatch.md
    ├── ideate.md
    ├── update.md
    └── perpetual-loop.md
```

## Known Issues

### `maton ask` is broken after v0.2.0

`maton ask <name> <question>` expects:
1. A name-based directory (`~/.maton/matons/<name>/`)
2. `Maton.md` as an identity/system prompt

After the init upgrade, instances use timestamp directories and `Maton.md` is a getting-started guide, not an identity prompt. Both assumptions are broken.

**Status**: Known consequence. Will be fixed in a separate task.
**Workaround**: Use the LLM driver (e.g., OpenCode) to open the instance directory directly.
