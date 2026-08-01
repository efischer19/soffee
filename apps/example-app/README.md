# example-app

> Example application demonstrating the monorepo app pattern.

## Purpose

This application provides a minimal example of how applications work in the
monorepo. It demonstrates:

* Application structure with `pyproject.toml` and uv
* Click-based CLI (per [ADR-011](../../meta/adr/ADR-011-use_click.md))
* Path dependency on a shared library (`example-lib`)
* Testing CLI commands with `click.testing.CliRunner`

## Installation

```bash
cd apps/example-app
uv sync
```

## Usage

```bash
# Run the CLI
uv run example-app hello
# Output: Hello, World!

uv run example-app hello --name Python
# Output: Hello, Python!
```

## Development

```bash
cd apps/example-app
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Dependencies

* **[example-lib](../../libs/example-lib/)** — Shared greeting library
  (path dependency)
* **[Click](https://click.palletsprojects.com/)** — CLI framework
  (see [ADR-011](../../meta/adr/ADR-011-use_click.md))
