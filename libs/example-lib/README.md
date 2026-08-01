# example-lib

> Example shared library demonstrating the monorepo library pattern.

## Purpose

This library provides a minimal example of how shared libraries work in the
monorepo. It demonstrates:

* Library structure with `pyproject.toml` and uv
* Snake\_case Python package naming (`example_lib`)
* Kebab-case directory naming (`example-lib`)
* Path dependency pattern for monorepo consumers
* Testing with pytest

## Installation

From an application in the monorepo, add a path dependency:

```toml
[project]
dependencies = [
    "example-lib @ file://../../libs/example-lib"
]
```

Then install:

```bash
uv sync
```

## Usage

```python
from example_lib import greet

message = greet("World")
print(message)  # "Hello, World!"
```

## API

### `greet(name: str) -> str`

Returns a greeting message for the given name.

* **Parameters:** `name` — The name to greet
* **Returns:** A greeting string in the format `"Hello, {name}!"`

## Development

```bash
cd libs/example-lib
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
