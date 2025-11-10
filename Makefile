.PHONY: setup seed train backtest analyze run test lint format migrate docker-up docker-down clean

PYTHON := python

setup:
	pip install -e ".[dev]"

seed:
	$(PYTHON) scripts/seed_data.py

train:
	$(PYTHON) scripts/train_model.py

backtest:
	$(PYTHON) scripts/run_backtest.py --output backtest_report.json
	@echo "Report saved to backtest_report.json"

analyze:
	$(PYTHON) -m notebooks.backtest_analysis

migrate:
	alembic upgrade head

run:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/

format:
	ruff check src/ tests/ --fix
	ruff format src/ tests/

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage
