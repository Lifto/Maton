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
# Create a maton
maton init my-maton

# Ask it something
maton ask my-maton "what's your name?"
```

## How It Works

A maton is a git repository. Its state is its files. Every change is a commit.
Point an LLM at it and it can read itself, understand itself, and act.

## Requirements

- Python 3.12+
- An OpenAI-compatible LLM endpoint (e.g., [oMLX](https://github.com/jundot/omlx) for local inference)
