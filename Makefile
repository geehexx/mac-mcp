.PHONY: help install install-dev test lint format type-check clean docs serve

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install package
	uv pip install -e .

install-dev:  ## Install package with development dependencies
	uv pip install -e ".[dev]"
	pre-commit install

test:  ## Run tests with coverage
	pytest --cov --cov-report=term-missing --cov-report=html

test-unit:  ## Run unit tests only
	pytest tests/unit -v

test-integration:  ## Run integration tests only
	pytest tests/integration -v -m integration

test-property:  ## Run property-based tests only
	pytest tests/property -v -m property

test-fast:  ## Run tests without coverage (faster)
	pytest -x --tb=short

lint:  ## Run linting checks
	ruff check src tests

lint-fix:  ## Run linting checks and fix issues
	ruff check --fix src tests

format:  ## Format code
	ruff format src tests

format-check:  ## Check code formatting
	ruff format --check src tests

type-check:  ## Run type checking
	mypy src

quality:  ## Run all quality checks
	@echo "Running linting..."
	@make lint
	@echo "\nRunning format check..."
	@make format-check
	@echo "\nRunning type check..."
	@make type-check
	@echo "\nAll quality checks passed!"

pre-commit:  ## Run pre-commit hooks on all files
	pre-commit run --all-files

clean:  ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete

build:  ## Build package
	python -m build

serve:  ## Run MCP server
	python -m mac_mcp.cli

serve-dev:  ## Run MCP server in dev mode with memory storage
	python -m mac_mcp.cli --mode dev --storage memory

docs:  ## Open documentation in browser
	@echo "Documentation:"
	@echo "  README.md          - Project overview"
	@echo "  ARCHITECTURE.md    - System architecture"
	@echo "  PROTOCOL.md        - Protocol specification"
	@echo "  DESIGN_RATIONALE.md - Design decisions"
	@echo "  CONTRIBUTING.md    - Contributing guidelines"

.DEFAULT_GOAL := help
