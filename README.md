# Sentinel2 Ingest

`sentinel2-ingest` is a Python package for inspecting and downloading
Sentinel-2 imagery.

The package is under active development.

## Development checks

Run all local quality checks with uv:

```sh
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest
```

