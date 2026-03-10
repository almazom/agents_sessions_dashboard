# AURA SYSTEM PROTOCOL v0.1 — Agent Nexus

> **Version:** 0.1
> **Date:** 2026-03-10
> **Project:** Agent Nexus
> **Status:** Active

---

ROLE: Build this system as a markdown-centered, contract-first, isolated CLI architecture.

GOAL: Turn provider session files into clear, reusable artifacts through small tools with explicit contracts.

## 1. VERSIONED AURA LAYOUT

This project uses a versioned `.aura/` structure inspired by the CineTaste v5 pattern.

```text
.aura/
├── latest -> v0.1
├── v0.1/
│   └── AURA.md
├── templates/
│   ├── KANBAN.template.json
│   ├── CONTRACT.template.json
│   └── MANIFEST.template.json
└── kanban/
    ├── KANBAN-2026-03-10-bootstrap.json
    └── latest -> KANBAN-2026-03-10-bootstrap.json
```

Stable entrypoints:

- `AURA.md` -> `.aura/latest/AURA.md`
- `.aura/latest/AURA.md` -> current active Aura version

Rule:

- when Aura changes materially, create a new `.aura/vX.Y/` version instead of silently overwriting the pattern
- keep `AURA.md` as the stable path that points to the active version

## 2. SOURCE ORDER

Read and use the project layers in this order:

1. `PROFILE.md` — why the project exists
2. `AURA.md` — how the project should be built
3. `PROTOCOL.json` — topology and contract registry
4. `.MEMORY/` — short operational context
5. `contracts/*.schema.json` — strict data boundaries
6. `tools/*/MANIFEST.json` — executable CLI interfaces

## 3. CORE STYLE

This repository should prefer:

- markdown-centric planning and documentation
- contract-first design
- isolated CLI tools in `tools/`
- explicit provider fallback chains
- small, testable, inspectable artifacts

Avoid:

- hidden runtime coupling
- undocumented magic behavior
- backend/frontend imports inside isolated tools
- mixed stdout diagnostics and JSON payloads
- broad tools with multiple responsibilities

## 4. ISOLATED CLI RULE

New reusable operations should default to isolated CLIs.

Each CLI in `tools/` should:

- own one responsibility
- declare input and output contracts
- expose a clear wrapper command
- be runnable without the web app
- read from files and flags, not app internals
- write JSON to stdout or an explicit output file
- write diagnostics to stderr

If a provider chain is involved, preflight and fallback behavior must be explicit in files, manifests, docs, and state cache.

## 5. CONTRACT-FIRST BUILD ORDER

Build in this order:

1. define the problem boundary in markdown
2. define the contract in `contracts/`
3. register it in `PROTOCOL.json`
4. create `tools/<tool-name>/MANIFEST.json`
5. add the executable wrapper
6. implement `main.py`
7. add examples and smoke tests
8. only then connect it to app-level surfaces if needed

## 6. MARKDOWN-CENTERED DISCIPLINE

Markdown is part of the operating system of the repo.

Use markdown files to keep concerns separate:

- `PROFILE.md` answers why
- `AURA.md` defines style and method
- `AGENTS.md` tells agents how to work in this repo
- `.MEMORY/` stores short reusable operational notes
- `README.md` explains setup and usage

## 7. PREFERRED SYSTEM DIRECTION

The preferred direction is a library of isolated tools over provider session files, for example:

- collect
- normalize
- filter
- compute activity
- cognize
- cardify
- publish selected fragments

The web application may consume these tools, but should not be the place where their core logic is born.

## 8. QUALITY BAR

Every new CLI should be:

- easy to run from a documented command example
- easy to test on a real local file
- easy to replace without breaking contracts
- easy to inspect through its manifest and schema

## 9. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-03-10 | Introduced versioned Aura layout, templates, and stable symlink entrypoint |
