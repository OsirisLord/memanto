---
name: install-memanto
description: One-shot setup: create a memanto agent for this project, verify the Moorcheh API key, and patch CLAUDE.md so every future skill invocation auto-injects past context.
argument-hint: "Paste your MOORCHEH_API_KEY if not already set in the environment."
---

# /install-memanto

Sets up cross-session persistent memory for this project using the **memanto-skills** package. Run this once per repo after installing the `memanto-skills` CLI.

## What it does

1. **Checks prerequisites** — verifies `memanto-skills` is installed and `MOORCHEH_API_KEY` is set.
2. **Creates a memanto agent** — runs `memanto-skills init` to create a project-scoped agent for storing engineering decisions, preferences, and facts.
3. **Patches `CLAUDE.md`** — appends a hook section that tells the agent to run `memanto-skills inject` at session start and `memanto-skills extract` at session end.
4. **Verifies the hook works** — runs `memanto-skills inject` and confirms it produces a context block (or a "no memories" placeholder).

## Prerequisites

- Python 3.10+ installed
- `pip install memanto-skills` (or `pip install -e .` from the cloned repo)
- A free Moorcheh API key from https://moorcheh.ai/

## After installation

All subsequent skill invocations will automatically:

- **At session start**: Query memanto for past decisions, preferences, and facts relevant to the current task.
- **At session end**: Extract key information from the session and store it as memories.

For the fully autonomous experience (no CLAUDE.md dependency), use the shell wrapper:

```bash
alias claude='memanto-skills exec claude'
```

## What gets stored

| Memory type | Examples |
|-------------|----------|
| `decision`  | "Chose SWR over React Query for data fetching" |
| `preference` | "Prefer function components over classes" |
| `fact`      | "API at /api/v1, uses pnpm" |
| `goal`      | "Refactor auth layer to use JWT" |
| `artifact`  | "Created ADR-001 on caching strategy" |

## How it works

This is a one-shot installation skill. It does NOT run the memory hooks itself — it installs the mechanism so every future skill session inherits the context.

**Important note**: This hook method relies on `CLAUDE.md` being read by your agent at session start. Confirmed working with Claude Code v0.1+ and Codex CLI.
