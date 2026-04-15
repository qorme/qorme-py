lint:
	uv run ruff check .
	uv run black --check .

format:
	uv run black .
	uv run ruff check --fix .

ty:
	uv run ty check src integrations/qorme-django/src

test:
	uv run python -m unittest

coverage:
	uv run coverage run -m unittest
	uv run coverage report -m

build-cython:
	uv run pip install cython==3.2.4
	uv run cython src/qorme/utils/bitset.pyx
	uv run cython src/qorme/utils/lru_cache.pyx
	uv run cython src/qorme/utils/traceback.pyx

sync:
	uv sync --refresh --reinstall

clean:
	rm -rf src/qorme/utils/*.so
	rm -rf .ruff_cache .coverage
	rm -rf build dist
