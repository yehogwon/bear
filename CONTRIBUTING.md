# CONTRIBUTING

Thanks for contributing.

This repository is experimental. Keep changes small, explicit, and easy to verify.

## Environment

- Python 3.12+
- `uv` for dependency management and command execution
- Ruff for linting and formatting
- pytest for tests

## Setup

```bash
uv sync
```

## Core commands

### Lint

```bash
uv run ruff check .
```

### Format

```bash
uv run ruff format .
```

### Full test suite

```bash
uv run pytest
```

### Single test file

```bash
uv run pytest tests/test_api.py
```

### Single test case

```bash
uv run pytest tests/test_api.py::test_api_vertical_slice
```

### Filter tests by keyword

```bash
uv run pytest -k knowledge
```

### Build

```bash
uv build
```

## Development expectations

- Keep the `src/bear/` package layout.
- Match existing naming and typing patterns.
- Use single quotes.
- Let Ruff own formatting decisions.
- Keep FastAPI route handlers thin and push logic into `BearService`.
- Use explicit exceptions instead of silent failure.
- Add or update tests when behavior changes.

## Commit and branch workflow

- Use Conventional Commits.
- Do not push directly to `main`.
- Create a branch, open a pull request, and merge through the PR flow.

Example commit messages:

- `feat: add approval endpoint`
- `fix: handle missing plan records`
- `docs: update agent guidance`

## Documentation

- `AGENTS.md` is for agentic coding agents and repo-operating guidance.
- `README.md` should stay concise and high-level.
- Update docs when commands, workflow, or project shape change.

## Before opening a PR

Run the relevant verification set.

For most code changes:

```bash
uv run ruff check .
uv run pytest
uv build
```

For docs-only changes, at least re-read the edited files for consistency.
