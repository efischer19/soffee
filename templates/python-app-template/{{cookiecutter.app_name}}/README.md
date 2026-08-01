# {{ cookiecutter.app_name }}

> {{ cookiecutter.description }}

## Installation

```bash
cd apps/{{ cookiecutter.app_name }}
uv sync
```

## Usage

```bash
uv run {{ cookiecutter.app_name }} hello
```

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
