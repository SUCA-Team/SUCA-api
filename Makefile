# Makefile for SUCA API
# Compatible with Windows PowerShell and Unix-like systems

.PHONY: help install dev-install run test lint format type-check clean migrate db-upgrade all-checks

# Detect OS
ifeq ($(OS),Windows_NT)
    SHELL := powershell.exe
    .SHELLFLAGS := -NoProfile -Command
    RM := Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    FIND_PYCACHE := Get-ChildItem -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    PYTHON := poetry run python
else
    SHELL := /bin/bash
    RM := rm -rf
    FIND_PYCACHE := find . -type d -name "__pycache__" -exec rm -rf {} +
    PYTHON := poetry run python
endif

# Colors for help message (Unix only)
ifndef OS
    CYAN := \033[36m
    RESET := \033[0m
else
    CYAN := 
    RESET := 
endif

# ============================================================================
# Help
# ============================================================================

help: ## Show this help message
    @echo "Available commands:"
ifeq ($(OS),Windows_NT)
    @powershell -Command "Select-String -Pattern '^[a-zA-Z_-]+:.*?## .*$$' -Path Makefile | ForEach-Object { $$_.Line -replace '(^[a-zA-Z_-]+):.*?## (.*)$$', '  $$1 - $$2' }"
else
    @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
endif

# ============================================================================
# Installation
# ============================================================================

install: ## Install production dependencies only
    poetry install --only=main

dev-install: ## Install all dependencies including dev
    poetry install

setup: dev-install ## Setup development environment
    @echo "Development environment setup complete!"

# ============================================================================
# Development Server
# ============================================================================

run: ## Run development server with auto-reload
    poetry run uvicorn src.suca.main:app --reload --host 127.0.0.1 --port 8000

run-prod: ## Run production server (no reload)
    poetry run uvicorn src.suca.main:app --host 0.0.0.0 --port 8000 --workers 4

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests
    poetry run pytest

test-cov: ## Run tests with coverage report
    poetry run pytest --cov=src/suca --cov-report=html --cov-report=term-missing

test-watch: ## Run tests in watch mode (requires pytest-watch)
    poetry run ptw

test-file: ## Run specific test file (usage: make test-file FILE=tests/test_auth.py)
    poetry run pytest $(FILE) -v

test-func: ## Run specific test function (usage: make test-func FUNC=test_login_success)
    poetry run pytest -k $(FUNC) -v

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run linting checks
    poetry run ruff check src/ tests/

lint-fix: ## Fix auto-fixable linting issues
    poetry run ruff check --fix src/ tests/

format: ## Format code with ruff
    poetry run ruff format src/ tests/

format-check: ## Check if code is properly formatted
    poetry run ruff format --check src/ tests/

type-check: ## Run type checking with mypy
    poetry run mypy src/

# ============================================================================
# Database Operations
# ============================================================================

migrate: ## Create new migration (usage: make migrate MSG="add user table")
    @poetry run alembic revision --autogenerate -m "$(MSG)"

migrate-empty: ## Create empty migration (usage: make migrate-empty MSG="custom changes")
    @poetry run alembic revision -m "$(MSG)"

db-upgrade: ## Apply all pending migrations
    poetry run alembic upgrade head

db-downgrade: ## Rollback last migration
    poetry run alembic downgrade -1

db-reset: ## Reset database (WARNING: destroys all data!)
    poetry run alembic downgrade base
    poetry run alembic upgrade head

db-history: ## Show migration history
    poetry run alembic history

db-current: ## Show current migration version
    poetry run alembic current

db-init: ## Initialize database with sample data
    poetry run python scripts/create_sample_data.py

# ============================================================================
# Data Operations
# ============================================================================

parse-jmdict: ## Parse JMdict XML file
    poetry run python scripts/parse_jmdict.py

sample-data: ## Create sample data for testing
    poetry run python scripts/create_sample_data.py

# ============================================================================
# Comprehensive Checks
# ============================================================================

all-checks: lint type-check test ## Run all quality checks and tests

ci-checks: format-check lint type-check test ## Run all CI checks (non-modifying)

prod-ready: clean ci-checks ## Ensure code is production ready
    @echo "Code is production ready!"

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Clean up cache files and temporary directories
ifeq ($(OS),Windows_NT)
    @powershell -Command "Get-ChildItem -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force"
    @powershell -Command "Get-ChildItem -Recurse -File -Filter '*.pyc' -ErrorAction SilentlyContinue | Remove-Item -Force"
    @powershell -Command "Get-ChildItem -Recurse -File -Filter '*.pyo' -ErrorAction SilentlyContinue | Remove-Item -Force"
    @powershell -Command "Remove-Item -Recurse -Force .pytest_cache, .mypy_cache, .ruff_cache, htmlcov, .coverage, coverage.xml, test-results.xml -ErrorAction SilentlyContinue"
    @echo "Cleanup complete!"
else
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    find . -type d -name ".mypy_cache" -exec rm -rf {} +
    find . -type d -name ".ruff_cache" -exec rm -rf {} +
    find . -type d -name "htmlcov" -exec rm -rf {} +
    rm -f .coverage coverage.xml test-results.xml
    @echo "Cleanup complete!"
endif

clean-all: clean ## Clean everything including Poetry cache
    poetry cache clear pypi --all
    @echo "Deep cleanup complete!"

# ============================================================================
# Docker Operations (Optional)
# ============================================================================

docker-build: ## Build Docker image
    docker build -t suca-api:latest .

docker-run: ## Run Docker container
    docker run -p 8000:8000 --env-file .env suca-api:latest

docker-compose-up: ## Start services with docker-compose
    docker-compose up -d

docker-compose-down: ## Stop docker-compose services
    docker-compose down

# ============================================================================
# Development Utilities
# ============================================================================

shell: ## Open poetry shell
    poetry shell

update: ## Update all dependencies
    poetry update

update-lock: ## Update lock file only
    poetry lock --no-update

deps-tree: ## Show dependency tree
    poetry show --tree

deps-outdated: ## Show outdated dependencies
    poetry show --outdated

security: ## Check for security vulnerabilities
    poetry run pip-audit

# ============================================================================
# Environment Info
# ============================================================================

info: ## Show environment information
    @echo "=== Environment Information ==="
    @echo ""
    @echo "Python version:"
    @poetry run python --version
    @echo ""
    @echo "Poetry version:"
    @poetry --version
    @echo ""
    @echo "Installed packages:"
    @poetry show
    @echo ""
    @echo "Database URL:"
    @poetry run python -c "from src.suca.core.config import settings; print(settings.database_url)"

versions: ## Show all tool versions
    @echo "=== Tool Versions ==="
    @echo ""
    @echo "Python:"
    @poetry run python --version
    @echo ""
    @echo "Poetry:"
    @poetry --version
    @echo ""
    @echo "Ruff:"
    @poetry run ruff --version
    @echo ""
    @echo "Pytest:"
    @poetry run pytest --version
    @echo ""
    @echo "MyPy:"
    @poetry run mypy --version

# ============================================================================
# Quick Workflows
# ============================================================================

dev: dev-install all-checks ## Full development setup and checks
    @echo "Development environment ready!"

quick-test: lint-fix test ## Quick test (fix + test)

pre-commit: format lint type-check ## Run before committing
    @echo "Pre-commit checks passed!"

pre-push: clean ci-checks ## Run before pushing
    @echo "Pre-push checks passed!"

# ============================================================================
# Documentation
# ============================================================================

docs-serve: ## Serve API documentation (if using mkdocs)
    @echo "Open http://localhost:8000/docs for Swagger UI"
    @echo "Open http://localhost:8000/redoc for ReDoc"

api-docs: run ## Alias for running server to view docs

# ============================================================================
# Project Management
# ============================================================================

count-lines: ## Count lines of code
ifeq ($(OS),Windows_NT)
    @powershell -Command "Get-ChildItem -Recurse -Include *.py -Path src | Measure-Object -Line | Select-Object -ExpandProperty Lines"
else
    @find src -name "*.py" | xargs wc -l | tail -1
endif

todo: ## Show TODO comments in code
ifeq ($(OS),Windows_NT)
    @powershell -Command "Select-String -Pattern 'TODO|FIXME|XXX' -Path src/**/*.py | Format-Table -AutoSize"
else
    @grep -rn "TODO\|FIXME\|XXX" src/ || echo "No TODOs found!"
endif

# ============================================================================
# Default target
# ============================================================================

.DEFAULT_GOAL := help