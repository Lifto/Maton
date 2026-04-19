# Task: Define maton installation and filesystem layout

## Questions to resolve

### 1. How does someone create a new maton?

`maton init Liftomaton`

The command creates a new maton instance with the given name.

### 2. Where does it live?

`~/.maton/matons/<name>/`

Example: `~/.maton/matons/Liftomaton/`

Follows the standard dot-directory convention in the user's home directory. The extra `matons/` level leaves room for runtime config, logs, or other non-instance files under `~/.maton/`.

### 3. One maton per machine, or many?

Multiple matons per machine. Each is its own git repository under `~/.maton/matons/`.

The runtime provides a menu to select which maton to run if no name is given on the command line.

### 4. What's the minimum that exists after init?

A git repository with a single file: `Maton.md`.

`Maton.md` contains:
- The maton's government name (the name given at init)
- The date and time of its creation

This is the birth certificate. Everything else gets added later — by the maton, by the human, or by both.

### 5. Automated testing

The project has automated tests from the start. Testing infrastructure is set up as part of the initial project scaffold, before any feature code is written. The test framework and conventions are documented in AGENTS.md.
