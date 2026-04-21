# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-21

### Added
- `maton init <name>` — create a new maton instance as a git repo at `~/.maton/matons/<name>/`
- `maton ask <name> <question>` — query a maton via local LLM (OpenAI-compatible endpoint)
- Self-describing `Maton.md` generated at init with identity, state system, and task conventions
- Git-native state: every change is a commit, history is the log

[0.1.0]: https://github.com/Lifto/Maton/releases/tag/v0.1.0
