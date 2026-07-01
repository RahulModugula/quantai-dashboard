# Contributing

## Good first contribution: add a distressed-credit situation

The fastest way to help is to add a real restructuring as a worked example — no
infrastructure, just a YAML file:

```bash
pip install -e .          # lightweight: litellm + pyyaml + rich, no ML stack
quantai-credit new examples/distressed/situations/my_company.yaml
# fill in the cap structure, timeline, operating metrics, and risks
quantai-credit validate examples/distressed/situations/my_company.yaml   # free, no key
quantai-credit run examples/distressed/situations/my_company.yaml        # needs an LLM key
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

# Working on just the credit committee? You don't need the ML stack:
make setup-credit   # pip install -e ".[dev]" — litellm + pyyaml + rich + test tools

# Working on the equity reference build / API / dashboard too?
make setup          # pip install -e ".[equity,dev]" + pre-commit hooks
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

The credit committee (the core) and the equity reference build share one
`BaseAgent`, but are otherwise decoupled — the credit path never imports the ML
stack.

**Credit committee** (`examples/distressed/`):
- **Entry point**: `examples/distressed/run.py` → `main()` (the `quantai-credit` CLI)
- **Deterministic math**: `credit_tools.py` — leverage, coverage, pari-passu
  recovery waterfall, fulcrum, attachment/detachment, asset coverage. Face value
  is the canonical claim across all tools; PIK accrual is opt-in and applied
  consistently. Preferred/equity is not counted as funded debt.
- **Free snapshot**: `snapshot.py` (`validate`) — no LLM; warns loudly on
  structures the generic waterfall can't model (uptier priming, ABS/silo).
- **Situations are data**: `models.py` parses a YAML `Situation`; adding a deal
  is pure YAML, no code.

**Equity reference build** (`src/`, behind the `equity` extra):
- **Entry point**: `src/api/main.py` → `create_app()`; config in `src/config/`
  (Pydantic Settings, env prefix `QUANTAI_`).
- **Walk-forward constraint**: predictions at time `t` use only data before `t`.
- `src/agents` lazily imports the equity orchestrator (PEP 562) so importing the
  shared `BaseAgent` never drags in torch/pandas.
- **Tests don't require seeded data** — use synthetic fixtures from `conftest.py`.

## Making Changes

1. Create a branch from `main`
2. Write tests for new functionality
3. Run `make test && make lint`
4. Submit PR with description of what changed and why
