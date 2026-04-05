# AGENTS
This file is for agentic coding agents working in this repository.

## Repo snapshot
- Project: `bear`
- Language: Python 3.12+
- Package manager: `uv`
- Web stack: FastAPI + Pydantic v2
- Packaging: Hatchling
- Persistence: markdown-backed state under `.bear/state/`
- Package layout: `src/bear/`
- Tests: pytest
- Lint/format: Ruff
- Type checking: basedpyright in the dev group

Keep the `src/bear/` layout. It is the better default here because the project is packaged and tested as a real Python distribution, and the `src/` layout avoids accidental imports from the repo root.

## Rule discovery
- No `.cursor/rules/` directory was found.
- No `.cursorrules` file was found.
- No `.github/copilot-instructions.md` file was found.

There are no additional Cursor or Copilot rule files to merge into this guidance.

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
tests/               API and service tests
.github/             CI and issue / PR templates
```

## Build, lint, test, and run commands
Run commands from the repository root.

### Install dependencies
```bash
uv sync
```

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
uv run pytest tests/test_service.py
```

### Single test by node id
```bash
uv run pytest tests/test_service.py::test_vertical_slice_persists_entities
```

### Test selection by keyword
```bash
uv run pytest -k approval
```

### Build distributions
```bash
uv build
```

### Run the demo flow
```bash
uv run bear-demo
```

### Run the local web app
```bash
uv run bear-web
```

## Testing notes
- Tests live under `tests/`.
- `pythonpath = ["src"]`.
- pytest uses `--import-mode=importlib`.
- Existing test patterns are in `tests/test_api.py`, `tests/test_service.py`, and `tests/test_policy_and_registry.py`.

## Code style guidelines
### Imports
- Use top-of-file imports only.
- Group imports in Ruff-compatible order: standard library, third-party, then local imports.
- Prefer explicit imports over wildcard imports.

### Formatting
- Ruff is the formatter.
- Line length is 100.
- Quote style is single quotes.

### Types
- Use type hints throughout.
- Prefer concrete return types on public functions and service methods.
- Use Pydantic models for structured state and request/response payloads.
- Follow existing aliases like `JsonDict = dict[str, object]` where useful.
- Do not suppress type errors with casts or ignores unless absolutely necessary.

### Naming
- Modules and functions: `snake_case`
- Classes and enums: `PascalCase`
- Request payload models: explicit names like `ProjectCreateRequest`
- IDs use prefixes like `proj_`, `idea_`, and `plan_`

### State and persistence
- Shared domain state lives in `src/bear/domain/models.py`.
- Shared enums live in `src/bear/domain/enums.py`.
- Persist state through `MarkdownRepository` in `src/bear/storage/markdown.py`.
- Keep state inspectable and serializable.

### Service and API conventions
- Keep business logic in `BearService` in `src/bear/runtime/service.py`.
- Keep FastAPI route handlers thin in `src/bear/web/app.py`.
- Return JSON-ready payloads with `model_dump(mode='json')`.

### Error handling
- Raise explicit exceptions for invalid state or missing records.
- Existing code uses `KeyError` for missing records and `PermissionError` for policy violations.
- Do not silently swallow errors or add empty `except` blocks.

## Practical editing guidance
- Prefer minimal, local diffs.
- Match existing style before introducing new abstractions.
- Extend existing modules before creating new ones when the behavior clearly belongs there.
- Add tests for new behavior or API changes.
- If you change commands or workflow, update both `AGENTS.md` and `CONTRIBUTING.md`.

## Git and review workflow
- Use Conventional Commits.
- Do not push directly to `main`.
- Create a branch, open a PR, and merge through the PR flow.

## Before finishing a change
- Docs-only change: re-read edited files for consistency.
- Python change: run `uv run ruff check .`.
- Behavior change: run targeted pytest or the full suite.
- Packaging or command change: run `uv build`.
- Web/API change: run relevant API tests and, when practical, exercise the flow manually.
