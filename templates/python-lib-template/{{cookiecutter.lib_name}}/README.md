# {{ cookiecutter.lib_name }}

> {{ cookiecutter.description }}

## Installation

Add a path dependency from your application:

```toml
[project]
dependencies = [
    "{{ cookiecutter.lib_name }} @ file://../../libs/{{ cookiecutter.lib_name }}"
]
```

## Development

```bash
cd libs/{{ cookiecutter.lib_name }}
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
