# Maton

Self-improving personal agent with git-native memory and human-auditable reasoning.

## Install

```bash
uv tool install maton
```

Or with pip:

```bash
pip install maton
```

## Quick Start

```bash
# Create a maton instance
maton init

# Edit the hitch config — set your model
nano ~/.maton/matons/maton-*/hitch/config.yaml

# Install platform scheduling (launchd on macOS, systemd on Linux)
maton hitch install ~/.maton/matons/maton-YYYYMMDD-HHMMSS

# Remove scheduling cleanly when done
maton hitch uninstall ~/.maton/matons/maton-YYYYMMDD-HHMMSS
```

## How It Works

A maton is a git repository. Its state is its files. Every change is a commit.
Point an LLM at it and it can read itself, understand itself, and act.

The **hitch** is the scheduling layer. It runs a dispatch cycle on a timer:
guards (cooldown, quiet hours, lock) → route (backlog tasks or ideation) → assemble prompt with inline state → invoke the LLM driver.

## Requirements

- Python 3.12+
- An OpenAI-compatible LLM endpoint
- An LLM driver ([OpenCode](https://github.com/nicepkg/opencode) or similar)
