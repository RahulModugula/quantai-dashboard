# Contributing

## Good first contribution: add a distressed-credit situation

The fastest way to help is to add a real restructuring as a worked example — no
infrastructure, just a YAML file:

```bash
pip install -r requirements-credit.txt
python -m examples.distressed.run new examples/distressed/situations/my_company.yaml
# fill in the cap structure, timeline, operating metrics, and risks
python -m examples.distressed.run run examples/distressed/situations/my_company.yaml
```

Use [`examples/distressed/situations/`](examples/distressed/situations/) as your
guide (`ati_2023.yaml`, `serta_2020.yaml`, `hertz_2020.yaml`). Ground every
figure in a public filing or reputable source, mark approximations inline
(`# ~approx`) and say "unknown" rather than guessing, and include a
`DECISION_POINT` event. `tests/test_credit_situation_loader.py` validates every
bundled file automatically.

## Development Setup

```bash
git clone https://github.com/RahulModugula/quantai-dashboard.git
cd quantai-dashboard
make setup      # installs deps + pre-commit hooks

# Working on just the credit committee? You don't need the full ML stack:
pip install -r requirements-credit.txt
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
