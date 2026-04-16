# Terminology

## Maton (capitalized)

The project. The package. The shared codebase that defines what a maton is. Installed via pip or uv. Contains the runtime — the loop, the LLM client, the tool system. Analogous to a species, or a genome.

## maton (lowercase)

An instance. A living individual. A maton's state — its memory, tasks, skills, and configuration — lives in a git repository as structured markdown files. This is the auditable core of the maton, but not necessarily all of it. A maton may also have a body: hardware it runs on, devices it controls, networks it inhabits.

A maton has a name. The name is permanent and tied to its identity, its git history, and its filesystem path.

## Canonical examples

**Tomatomaton** — the maton whose purpose is to improve, promote, and maintain Maton itself. A public maton. The project's dogfood.

**Liftomaton** — the creator's personal maton. A private maton. Its purpose is to serve its human.

## Identity vs personality

A maton has two layers:

**Identity** is structural. The maton's name, its purpose, its git history, its accumulated knowledge. Identity is facts. Identity doesn't change without a commit.

**Personality** is presentational. How the maton speaks, its tone, its persona when interacting with its human. Personality lives in a configuration file and can be changed freely. A maton named Liftomaton might present as a British woman named Mim. The identity is Liftomaton. The personality is Mim. One is the government name, the other is how you'd introduce yourself at a party.

## Task

The unit of work. A task is a directory containing structured markdown files: what to do, how to verify success, and the history of attempts. Tasks are recursive — a task can spawn tasks, and the children are the same class as the parent. Tasks are the same whether created by a human or by a maton.

## Human

The bootstrap. The source of purpose. Humans express needs, and those needs become tasks. A human's normal interface to a maton is conversation — speaking or typing — and the maton translates that into the structured files that drive the system. But because the system is built on plain files, a human can also read, edit, or create those files directly. This is the audit path and, when needed, a way for humans to read and modify the system directly.

Matons exist to serve human needs. The system is human-auditable because humans are part of the system — they build it, maintain it, and audit its self-improvements. If they can't read it, the loop breaks.
