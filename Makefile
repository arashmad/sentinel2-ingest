.PHONY: check format help lint test typecheck

help:
	@printf '%s\n' \
		'Available commands:' \
		'  make lint       Run Ruff lint checks.' \
		'  make format     Validate Ruff formatting.' \
		'  make typecheck  Run mypy type checks.' \
		'  make test       Run the test suite.' \
		'  make check      Run all quality checks.' \
		'  make help       Show this help message.'

lint:
	uv run ruff check .

format:
	uv run ruff format --check .

typecheck:
	uv run mypy src

test:
	uv run pytest

check: lint format typecheck test
