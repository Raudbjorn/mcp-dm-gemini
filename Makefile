# Makefile for TTRPG Assistant development

.PHONY: help install install-dev test test-cov lint format type-check security-check clean build docs serve-docs docker-build docker-run pre-commit setup-dev

# Default target
help: ## Show this help message
	@echo "TTRPG Assistant MCP Server - Development Commands"
	@echo "=================================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install the package and dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

setup-dev: ## Complete development environment setup
	python -m venv .venv
	. .venv/bin/activate && make install-dev
	mkdir -p chroma_db pattern_cache config
	@echo "Development environment ready! Activate with: source .venv/bin/activate"

# Testing targets
test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest -m "not integration and not slow"

test-integration: ## Run integration tests only
	pytest -m integration

test-cov: ## Run tests with coverage
	pytest --cov=ttrpg_assistant --cov-report=html --cov-report=term-missing

test-slow: ## Run all tests including slow ones
	pytest -m ""

# Code quality targets
lint: ## Run linting checks
	flake8 ttrpg_assistant tests
	black --check ttrpg_assistant tests
	isort --check-only ttrpg_assistant tests

format: ## Format code with black and isort
	black ttrpg_assistant tests
	isort ttrpg_assistant tests

type-check: ## Run type checking with mypy
	mypy ttrpg_assistant

security-check: ## Run security checks with bandit
	bandit -r ttrpg_assistant -x tests

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# Quality checks combined
quality: lint type-check security-check ## Run all quality checks

# Development server targets
serve-mcp: ## Start MCP server for Claude Desktop integration
	./mcp_stdio.sh

serve-fastmcp: ## Start FastMCP server for testing
	./run_main.sh

serve-web: ## Start web UI server
	python mcp_server.py

# Documentation targets
docs: ## Build documentation
	@echo "Building documentation..."
	@echo "Documentation available in docs/ directory"

serve-docs: ## Serve documentation locally
	@echo "Serving documentation at http://localhost:8080"
	python -m http.server 8080 --directory docs

# Docker targets
docker-build: ## Build Docker image
	docker build -t ttrpg-assistant .

docker-run: ## Run Docker container
	docker-compose up

docker-dev: ## Run Docker container in development mode
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Build and packaging
build: ## Build package
	python -m build

clean: ## Clean build artifacts and cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/
	rm -rf .mypy_cache/ .tox/

clean-data: ## Clean data directories (be careful!)
	@echo "⚠️  This will delete ChromaDB data and pattern cache!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		rm -rf chroma_db/ pattern_cache/; \
		echo "Data directories cleaned."; \
	else \
		echo ""; \
		echo "Cancelled."; \
	fi

# Initialization targets
init-config: ## Initialize configuration files
	mkdir -p config
	./bootstrap.sh

bootstrap: ## Run bootstrap script
	./bootstrap.sh

# Database and data management
reset-db: clean-data init-config ## Reset database and reinitialize

# Development workflow shortcuts
dev-check: format lint type-check test ## Complete development check
	@echo "✅ All checks passed!"

dev-setup: setup-dev init-config ## Complete development setup

# Performance testing
perf-test: ## Run performance tests
	pytest -m slow --benchmark-only

# Profiling
profile: ## Profile the application
	python -m cProfile -o profile.stats main.py
	@echo "Profile saved to profile.stats"

# Git helpers
git-hooks: ## Install git hooks
	pre-commit install
	@echo "Git hooks installed"

# Release helpers
version: ## Show current version
	@python -c "import toml; print('Version:', toml.load('pyproject.toml')['project']['version'])"

# Quick development commands
quick-test: ## Quick test run (unit tests only)
	pytest tests/ -x -v --tb=short -m "not slow and not integration"

watch-test: ## Watch files and run tests on changes
	@echo "Watching for changes... (requires entr: brew install entr)"
	find . -name "*.py" | entr -c make quick-test

# Docker development
docker-shell: ## Get shell in Docker container
	docker-compose exec app bash

# File watching for development
watch-lint: ## Watch files and run linting on changes
	@echo "Watching for changes... (requires entr: brew install entr)"
	find . -name "*.py" | entr -c make lint

# Installation verification
verify-install: ## Verify installation is working
	python -c "import ttrpg_assistant; print('✅ Package imported successfully')"
	./mcp_stdio.sh --help || echo "MCP stdio script found"
	./run_main.sh --help || echo "FastMCP script found"

# Environment info
env-info: ## Show environment information
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "Virtual environment: $$VIRTUAL_ENV"
	@echo "Working directory: $$(pwd)"
	@python -c "import sys; print(f'Python path: {sys.executable}')"

# Emergency commands
fix-permissions: ## Fix file permissions
	chmod +x *.sh
	chmod +x run_main.bat
	chmod +x mcp_stdio.bat

# All-in-one commands
all: clean install test lint ## Clean, install, test, and lint
dev-all: clean install-dev test lint type-check security-check ## Full development check
ci: install test lint type-check security-check ## CI pipeline simulation