.PHONY: build-cython

# Default Python interpreter
PYTHON := python

ty:
	uv run ty check src integrations/qorme-django/src

format:
	uv run black .
	uv run ruff check --fix .

test:
	uv run python -m unittest

coverage:
	uv run coverage run -m unittest
	uv run coverage report -m

build-cython:
	uv run pip install cython
	uv run cython src/qorme/utils/bitset.pyx
	uv run cython src/qorme/utils/lru_cache.pyx
	uv run cython src/qorme/utils/traceback.pyx

sync:
	uv sync --refresh --reinstall

clean:
	rm -rf src/qorme/utils/*.so
	rm -rf .ruff_cache .coverage
	rm -rf build dist
