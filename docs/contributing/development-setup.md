# Development Setup

How to set up a local development environment for contributing to Qorme.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git

## Clone and install

```bash
git clone https://github.com/qorme/qorme-py.git
cd qorme-py

# Install all dependencies (core + dev + integrations)
uv sync
```

The workspace includes:
- `src/qorme/` — Core SDK
- `integrations/qorme-django/` — Django integration
- `docs/` — This documentation

## Project structure

```
qorme-py/
├── src/qorme/                    # Core SDK
│   ├── context/                  # QueryContext, ContextVar tracking
│   ├── contrib/celery/           # Celery integration
│   ├── db/                       # Database driver instrumentation
│   │   └── integrations/         # sqlite, psycopg, psycopg2
│   ├── ingest/                   # Telemetry pipeline (queue, flusher)
│   ├── ml/                       # ML domain base, MLStore, SSE client
│   ├── orm/                      # ORMQuery tracker, data structures
│   └── utils/                    # Wrapper, BitSet, Traceback (C extensions)
├── integrations/
│   └── qorme-django/             # Django integration
│       └── src/qorme_django/
│           ├── domains/          # Django-specific domains
│           │   └── ml/           # Optimization domains
│           └── contrib/          # Wagtail, Taggit
├── tests/                        # Core SDK tests
└── docs/                    # MkDocs documentation
```

## Running tests

```bash
# Core SDK tests
uv run pytest tests/

# Django integration tests
uv run pytest integrations/qorme-django/tests/

# With coverage
uv run pytest tests/ --cov=qorme --cov-report=term-missing

# Specific test
uv run pytest tests/test_events.py -v
```

## Building C extensions

The C extensions (bitset, traceback, lru_cache) are built from `.c` files checked into the repo. Cython is **not** required for normal development.

To regenerate the `.c` files from `.pyx` sources (only needed if you modify `.pyx` files):

```bash
# Install Cython first (not included in dev dependencies)
uv pip install cython
uv run cythonize -i src/qorme/utils/bitset.pyx
uv run cythonize -i src/qorme/utils/traceback.pyx
uv run cythonize -i src/qorme/utils/lru_cache.pyx
```

## Building documentation

```bash
cd docs

# Install doc dependencies
uv sync

# Serve locally with hot reload
uv run mkdocs serve --dev-addr 0.0.0.0:8100

# Build for production
uv run mkdocs build
```

## Code style

- Type hints on all public APIs
- Docstrings on all public classes and methods
- `__slots__` on all domain classes for memory efficiency
- `logging` for all runtime messages (no `print()`)

## Pull request checklist

- [ ] Tests pass (`uv run pytest`)
- [ ] Type checking passes
- [ ] New domains have tests
- [ ] Documentation updated for new features
- [ ] C extensions rebuilt if `.pyx` files changed
