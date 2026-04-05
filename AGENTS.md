# AGENTS

## Architecture summary

The scaffold separates typed domain state from orchestration logic, markdown-backed local persistence, tool policy, provider adapters, execution backends, and human-facing channels. A small runtime service coordinates the research loop while keeping actions inspectable, permission-aware, and backend-agnostic.

## Directory structure

```text
src/bear/
  backends/          Execution target adapters
  channels/          Human communication adapters
  config/            Runtime configuration
  core/              Shared interfaces and service contracts
  domain/            Typed domain models and enums
  policy/            Permission evaluation models
  providers/         LLM and coding-agent adapters
  runtime/           Vertical-slice orchestration services and demo
  storage/           Markdown-backed local persistence
  tools/             Tool registry and audit metadata
  web/               FastAPI app and local control plane entrypoint
tests/               Core and API tests
.github/             CI and collaboration templates
```

## Developer workflow with `uv`

```bash
uv sync
uv run ruff check .
uv run ruff format .
uv run pytest
```

## Commit convention

Use Conventional Commits for commit messages in this repository, such as `feat: add local execution backend` or `fix: handle missing plan ids`.

## Branch workflow

Do not push directly to `main`. Create another branch, open a pull request, and merge through the PR flow.

## Run the demo flow

```bash
uv run bear-demo
```

That command creates a project, idea, hypothesis, plan, dry-run execution, result summary, artifacts, and suggested next step in the local markdown state store.

## Run the local webserver

```bash
uv run bear-web
```

Then open `http://127.0.0.1:8000`.

## Current vertical slice

The first slice includes:

- project creation
- research idea and hypothesis creation
- experiment plan and code task generation
- approval-gated execution requests for non-dry-run runs
- dry-run backend execution through a local backend adapter
- result collection, artifact persistence, and lightweight analysis
- global knowledge nodes and cross-project links
- autopilot and semi-autopilot session start and pause controls
- local web UI and JSON API for inspection and actions
- tool registry and explicit `allow` / `request` / `disallow` policy model

## What remains for later phases

The scaffold leaves real model providers, coding-agent executors, richer Discord behavior, and scheduler-aware resource management as clean extension points rather than pretending they already exist.
