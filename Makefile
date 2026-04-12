.PHONY: help install install-dev run test lint format clean

help:
	@echo "Investment Assistant - Available Commands"
	@echo "=========================================="
	@echo "make help        - Show this help message"
	@echo "make install     - Install dependencies"
	@echo "make install-dev - Install dependencies including dev tools"
	@echo "make run         - Run the Streamlit application"
	@echo "make test        - Run tests"
	@echo "make lint        - Run Ruff linting and mypy type checks"
	@echo "make format      - Format code with Ruff"
	@echo "make clean       - Clean up temporary files and caches"

install:
	@poetry install

install-dev:
	@poetry install --with dev

run:
	@hf auth login --token $$HUGGINGFACE_TOKEN
	@poetry run streamlit run src/app.py

test:
	@poetry run pytest -v --cov=src tests/

lint:
	@poetry run ruff check --fix src/
	@poetry run mypy src/

format:
	@poetry run ruff format src/

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.egg-info" -delete
	@rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/
	@rm -rf .mypy_cache/

.DEFAULT_GOAL := help
