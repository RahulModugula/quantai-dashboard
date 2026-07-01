.PHONY: setup setup-credit credit seed train backtest analyze run test test-credit test-ci lint format migrate docker-up docker-down docker-prod clean

PYTHON := python

# Full stack: credit committee + equity pipeline + API + dashboard + dev tools.
setup:
	pip install -e ".[equity,dev]"
	pre-commit install

# Credit committee only — no ML/data stack (litellm + pyyaml + rich).
setup-credit:
	pip install -e ".[dev]"

# Run the bundled credit committee example (needs an LLM key; see README).
credit:
	$(PYTHON) -m examples.distressed.run run examples/distressed/situations/ati_2023.yaml

seed:
	$(PYTHON) scripts/seed_data.py

train:
	$(PYTHON) scripts/train_model.py

backtest:
	$(PYTHON) scripts/run_backtest.py --output backtest_report.json
	@echo "Report saved to backtest_report.json"

ablation:
	$(PYTHON) scripts/run_ablation.py --ticker AAPL --type both --output ablation_report.json
	@echo "Ablation report saved to ablation_report.json"

analyze:
	$(PYTHON) -m notebooks.backtest_analysis

migrate:
	alembic upgrade head

run:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Credit-only tests — run under the lightweight install (no ML stack needed).
test-credit:
	pytest tests/test_distressed_credit.py tests/test_credit_correctness.py \
	  tests/test_credit_snapshot.py tests/test_credit_situation_loader.py \
	  tests/test_credit_tools_advanced.py tests/test_envision_2023.py -v --timeout=30

test:
	pytest tests/ -v --cov=src --cov=examples --cov-report=term-missing --timeout=30

test-ci:
	pytest tests/ -v --cov=src --cov=examples --cov-report=term-missing --cov-report=xml --timeout=30

lint:
	ruff check src/ tests/
	ruff format src/ tests/ --check

format:
	ruff check src/ tests/ --fix
	ruff format src/ tests/

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-prod:
	docker compose -f docker-compose.prod.yml up --build -d

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage coverage.xml
