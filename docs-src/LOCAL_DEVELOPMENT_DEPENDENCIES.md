# Local Development Dependencies

> Tools required for local development in this monorepo.

## Required Tools

| Tool | Version | Purpose | Install |
| :--- | :--- | :--- | :--- |
| **Python** | 3.12+ | Runtime | [python.org](https://www.python.org/) or `pyenv install 3.12` |
| **uv** | latest | Dependency management | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/) |
| **Git** | 2.x | Version control | [git-scm.com](https://git-scm.com/) |

## Recommended Tools

| Tool | Purpose | Install |
| :--- | :--- | :--- |
| **pyenv** | Python version management | [github.com/pyenv/pyenv](https://github.com/pyenv/pyenv) |
| **pre-commit** | Git hook management | `pip install pre-commit` |
| **Docker** | Containerization | [docker.com](https://www.docker.com/) |
| **markdownlint-cli2** | Markdown linting | `npm install -g markdownlint-cli2` |

## Quick Setup

```bash
# 1. Install Python 3.12+ (using pyenv)
pyenv install 3.12
pyenv local 3.12

# 2. Install uv
pip install uv

# 3. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 4. Install all project dependencies
python scripts/setup-local-deps.py

# 5. Verify everything works
./scripts/local-ci-check.sh
```

## Python Version

The minimum Python version for this project is **3.12**, as specified in
`.python-version` and documented in
[ADR-002](https://github.com/efischer19/soffee/blob/main/meta/adr/ADR-002-use_python312.md).

Use `pyenv` to manage Python versions:

```bash
pyenv install 3.12
pyenv local 3.12
python --version  # Should output Python 3.12.x
```

## uv

uv manages dependencies, virtual environments, and package metadata for
each application and library in the monorepo. See
[ADR-015](https://github.com/efischer19/soffee/blob/main/meta/adr/ADR-015-use_uv.md).

```bash
# Install uv
pip install uv

# Install a project's dependencies
cd apps/example-app
uv sync

# Run a command in the project's virtual environment
uv run pytest
```

## Ruff

Ruff handles both linting and formatting for Python code. See
[ADR-005](https://github.com/efischer19/soffee/blob/main/meta/adr/ADR-005-use_ruff.md).

```bash
# Check formatting
uv run ruff format --check .

# Auto-format
uv run ruff format .

# Lint
uv run ruff check .

# Lint with auto-fix
uv run ruff check --fix .
```

## Pre-commit

Pre-commit runs quality checks automatically before each commit:

```bash
pip install pre-commit
pre-commit install

# Run all hooks manually
pre-commit run --all-files
```
