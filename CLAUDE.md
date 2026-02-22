# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

See [AGENTS.md](./AGENTS.md) for comprehensive project documentation including:
- Project architecture and key files
- Common commands (dev, test, eval, typecheck)
- Code patterns (middleware, tools, testing)
- Dependencies and configuration

## Quick Reference

**Requires:** `ANTHROPIC_API_KEY` env var (or `.env` file).
**Python:** 3.14 — use `uv run` for all commands.

```bash
uv run poe dev          # Run agent (default: Haiku model)
uv run poe test         # Unit tests
uv run poe eval         # DeepEval evaluations
uv run poe check        # Lint + format + typecheck
uv run poe serve        # FastAPI server (dev mode, port 8000)
uv run poe ci           # CI checks (lint + typecheck + test)
```

**Use Sonnet instead of Haiku:**
```bash
PDF_AGENT_MODEL=sonnet uv run poe dev
```
