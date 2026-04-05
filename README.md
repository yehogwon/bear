# bear

![bear banner](assets/banner.webp)

`bear` is a highly experimental autonomous research assistant scaffold.

Everything in this repository is vibe-coded, risky, has not had a security review, and may break at any time.

## What it is

The project is a local-first Python scaffold for a research loop that can track projects, ideas, hypotheses, experiment plans, executions, results, knowledge links, and lightweight agent sessions.

The current implementation includes:

- a packaged Python project under `src/bear/`
- a FastAPI control plane
- markdown-backed local state
- dry-run and approval-gated execution flow
- a small test suite

## Quick start

```bash
uv sync
uv run ruff check .
uv run pytest
```

## Run the demo

```bash
uv run bear-demo
```

## Run the web app

```bash
uv run bear-web
```

Then open `http://127.0.0.1:8000`.

## Where to look next

- `AGENTS.md` for agent and repo-operating guidance
- `CONTRIBUTING.md` for contributor workflow
- `src/bear/runtime/service.py` for the main orchestration path
- `src/bear/web/app.py` for the API surface

## Status

This is not a stable or security-reviewed system. Treat it as an experimental scaffold, not production-ready software.
