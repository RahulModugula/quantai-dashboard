# Contributing

## Development Setup

```bash
git clone https://github.com/RahulModugula/quantai-dashboard.git
cd quantai-dashboard
make setup      # installs deps + pre-commit hooks
```

## Running Tests

```bash
make test       # runs pytest with coverage
make lint       # ruff check + format check
```

All tests must pass and lint must be clean before pushing.

## Code Style

- Python 3.11+ (use `X | Y` union syntax, not `Optional[X]`)
- Formatted with ruff (line length 100)
- Type hints on all public functions
- No unused imports or variables (enforced by ruff)

## Architecture Notes

- **Entry point**: `src/api/main.py` → `create_app()`
- **Config**: `src/config/__init__.py` (Pydantic Settings, env prefix `QUANTAI_`)
- **ML models train independently** — ensemble combines at prediction time
- **Walk-forward constraint**: predictions at time `t` use only data before `t`
- **Tests don't require seeded data** — use synthetic fixtures from `conftest.py`

## Making Changes

1. Create a branch from `main`
2. Write tests for new functionality
3. Run `make test && make lint`
4. Submit PR with description of what changed and why
