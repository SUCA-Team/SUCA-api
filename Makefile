.PHONY: help install dev-install run test lint format type-check clean migrate migrate-auto db-upgrade db-downgrade docker-build docker-run all-checks

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation and setup
install: ## Install production dependencies
	poetry install --only=main

dev-install: ## Install all dependencies including dev dependencies
	poetry install

setup: dev-install ## Setup the development environment
	@echo "Development environment setup complete!"

# Development server
run: ## Run the development server
	poetry run uvicorn src.suca.main:app --reload  

run-prod: ## Run the production server
	poetry run uvicorn src.suca.main:app

# Testing
test: ## Run all tests
	poetry run pytest

test-cov: ## Run tests with coverage report
	poetry run pytest --cov=src/suca --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	poetry run pytest --watch

# Code quality
lint: ## Run linting checks
	poetry run ruff check src/ tests/

lint-fix: ## Run linting and fix auto-fixable issues
	poetry run ruff check --fix src/ tests/

format: ## Format code with ruff
	poetry run ruff format src/ tests/

format-check: ## Check if code is properly formatted
	poetry run ruff format --check src/ tests/

type-check: ## Run type checking with mypy
	poetry run mypy src/

# Database operations
migrate: ## Create a new migration
	@read -p "Enter migration message: " msg; \
	poetry run alembic revision --autogenerate -m "$$msg"

migrate-empty: ## Create an empty migration
	@read -p "Enter migration message: " msg; \
	poetry run alembic revision -m "$$msg"

db-upgrade: ## Upgrade database to latest migration
	poetry run alembic upgrade head

db-downgrade: ## Downgrade database by one migration
	poetry run alembic downgrade -1

db-reset: ## Reset database to base (WARNING: destroys all data)
	poetry run alembic downgrade base
	poetry run alembic upgrade head

db-history: ## Show migration history
	poetry run alembic history

db-current: ## Show current migration
	poetry run alembic current

# Comprehensive checks
all-checks: lint type-check test ## Run all code quality checks and tests

ci-checks: format-check lint type-check test ## Run all CI checks (non-modifying)

# Clean up
clean: ## Clean up cache files and temporary directories
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +

# Docker operations (if needed)
docker-build: ## Build Docker image
	docker build -t suca-api .

docker-run: ## Run Docker container
	docker run -p 8000:8000 suca-api

# Development utilities
shell: ## Open poetry shell
	poetry shell

update: ## Update dependencies
	poetry update

security: ## Check for security vulnerabilities
	poetry run pip-audit

deps-tree: ## Show dependency tree
	poetry show --tree

deps-outdated: ## Show outdated dependencies
	poetry show --outdated

# Environment info
info: ## Show environment information
	@echo "Python version:"
	@poetry run python --version
	@echo "\nPoetry version:"
	@poetry --version
	@echo "\nProject dependencies:"
	@poetry show

# Quick development workflow
dev: dev-install all-checks ## Full development setup and checks

# Production ready check
prod-ready: clean all-checks ## Ensure code is production ready