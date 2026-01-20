.PHONY: setup seed train backtest analyze run test test-ci lint format migrate docker-up docker-down docker-prod clean

PYTHON := python

setup:
	pip install -e ".[dev]"
	pre-commit install

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

test:
	pytest tests/ -v --cov=src --cov-report=term-missing --timeout=30

test-ci:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=xml --timeout=30

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
