# memanto-skills — Cross-Session Memory for mattpocock/skills

**Eliminate context fragmentation.** Every Claude Code skill session (`/tdd`, `/grill-with-docs`, `/diagnose`, etc.) is currently an isolated event. Architectural decisions made in one session are invisible when you start a fresh terminal for the next skill. memanto-skills bridges that gap.

[![Bounty](https://img.shields.io/badge/Bounty-%24100-blue)](https://github.com/moorcheh-ai/memanto/issues/508)

## How it works

Two autonomous hooks run around every skill execution:

1. **Pre-inject** — Before your agent starts, memanto-skills queries the Memanto backend for past decisions, preferences, and facts relevant to your current task. The result is prepended to the prompt context.
2. **Post-extract** — After your session completes, memanto-skills captures the session transcript (via `script(1)`) and sends it to Memanto's backend LLM. The LLM extracts structured memories — architecture decisions, framework preferences, codebase conventions — and stores them automatically.

## Quickstart

### 1. Prerequisites

- Python 3.10+
- A free Moorcheh API key from [moorcheh.ai](https://moorcheh.ai/)

### 2. Install

```bash
cd examples/claudecode-skills-memanto
pip install -e .
```

### 3. Set your API key

```bash
export MOORCHEH_API_KEY=your_key_here
```

### 4. Initialize for your project

```bash
cd my-project
memanto-skills init
```

### 5. Run skills with automatic memory

**Autonomous mode (recommended):**

```bash
memanto-skills exec claude /tdd "Add pagination"
memanto-skills exec claude /grill-with-docs "Design the data fetching layer"
```

The wrapper uses `script(1)` to capture the full interactive session.

**CLAUDE.md mode:** Use the `/install-memanto` skill (run once per repo) to patch CLAUDE.md with hook instructions.

### 6. Verify

```bash
memanto-skills status
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `memanto-skills init` | Create/activate a Memanto agent for the current project |
| `memanto-skills inject` | Print a context block (pipe into agent prompt) |
| `memanto-skills extract [text-or-file]` | Send content to Memanto's LLM for memory extraction |
| `memanto-skills exec <command>` | **Primary:** run a command with autonomous pre/post hooks |
| `memanto-skills status` | Show agent health and recent memories |

## Files

```
memanto_skills/
├── __init__.py      # Package entrypoint
├── config.py        # API key + project config
├── memory.py        # Memanto SDK wrapper (remember, recall, answer)
├── extraction.py    # LLM-based memory extraction (no heuristic parsing)
├── injection.py     # Context block builder for prompt injection
├── executor.py      # Shell wrapper with script(1) capture
└── cli.py           # Click CLI
skills/
└── install-memanto/
    └── SKILL.md     # One-shot install skill for CLAUDE.md mode
tests/
├── test_extraction.py  # _parse_answer + _store_memories tests
└── test_executor.py    # _find_artifacts_after + _find_git_diff tests
```

## Why `script(1)`?

`script(1)` is a POSIX-standard utility available on every Linux/macOS system. It launches a subprocess with a PTY and captures ALL I/O — both the user's prompts and the agent's responses. On Windows, or when `script` is unavailable, the wrapper falls back to `subprocess.run` with stdout/stderr capture.

## License

MIT
