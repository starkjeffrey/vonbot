.PHONY: help install test test-unit test-integration test-security test-coverage clean lint format typecheck dev build deploy-local deploy-vps logs health

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Legacy Adapter Service - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# Development Setup
install: ## Install dependencies (production + development)
	@echo "$(BLUE)Installing dependencies...$(NC)"
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-prod: ## Install production dependencies only
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Production dependencies installed$(NC)"

# Testing
test: ## Run all tests with verbose output
	@echo "$(BLUE)Running all tests...$(NC)"
	pytest -v
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-unit: ## Run unit tests only (fast)
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest -m unit -v
	@echo "$(GREEN)✓ Unit tests passed$(NC)"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest -m integration -v
	@echo "$(GREEN)✓ Integration tests passed$(NC)"

test-security: ## Run security tests only
	@echo "$(BLUE)Running security tests...$(NC)"
	pytest -m security -v
	@echo "$(GREEN)✓ Security tests passed$(NC)"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest --cov=app --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated$(NC)"
	@echo "$(YELLOW)Open htmlcov/index.html to view detailed report$(NC)"

test-watch: ## Run tests in watch mode (requires pytest-watch)
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	ptw -- -v

# Code Quality
lint: ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(NC)"
	ruff check .
	@echo "$(GREEN)✓ Linting passed$(NC)"

lint-fix: ## Auto-fix linting issues
	@echo "$(BLUE)Auto-fixing linting issues...$(NC)"
	ruff check --fix .
	@echo "$(GREEN)✓ Linting issues fixed$(NC)"

format: ## Format code with black and ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	black .
	ruff format .
	@echo "$(GREEN)✓ Code formatted$(NC)"

typecheck: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	mypy app/
	@echo "$(GREEN)✓ Type checking passed$(NC)"

quality: lint typecheck ## Run all quality checks (lint + typecheck)
	@echo "$(GREEN)✓ All quality checks passed$(NC)"

# Pre-commit Checks
pre-commit: format lint typecheck test-unit ## Run all pre-commit checks
	@echo "$(GREEN)✓ Pre-commit checks passed - ready to commit$(NC)"

pre-push: quality test-coverage ## Run all pre-push checks
	@echo "$(GREEN)✓ Pre-push checks passed - ready to push$(NC)"

# Development
dev: ## Start development server (requires .env)
	@echo "$(BLUE)Starting development server...$(NC)"
	docker compose -f docker-compose.dev.yml up

dev-build: ## Build and start development server
	@echo "$(BLUE)Building and starting development server...$(NC)"
	docker compose -f docker-compose.dev.yml up --build

dev-stop: ## Stop development server
	@echo "$(BLUE)Stopping development server...$(NC)"
	docker compose -f docker-compose.dev.yml down

dev-logs: ## Follow development server logs
	@echo "$(BLUE)Following development logs...$(NC)"
	docker compose -f docker-compose.dev.yml logs -f

# Build
build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t legacy-adapter:latest .
	@echo "$(GREEN)✓ Docker image built$(NC)"

# Deployment
deploy-local: ## Deploy to local development (requires .env)
	@echo "$(BLUE)Deploying to local development...$(NC)"
	./scripts/test-local.sh
	@echo "$(GREEN)✓ Local deployment complete$(NC)"

deploy-vps: ## Deploy to VPS production (requires .env)
	@echo "$(BLUE)Deploying to VPS...$(NC)"
	./scripts/deploy-vps.sh
	@echo "$(GREEN)✓ VPS deployment complete$(NC)"

# Monitoring
logs: ## View production logs
	@echo "$(BLUE)Viewing production logs...$(NC)"
	docker compose -f docker-compose.vps.yml logs -f

logs-audit: ## View audit logs only
	@echo "$(BLUE)Viewing audit logs...$(NC)"
	docker compose -f docker-compose.vps.yml logs -f | grep audit

logs-errors: ## View error logs only
	@echo "$(BLUE)Viewing error logs...$(NC)"
	docker compose -f docker-compose.vps.yml logs -f | grep -i error

health: ## Check service health
	@echo "$(BLUE)Checking service health...$(NC)"
	@curl -s http://localhost:8001/health | jq . || echo "$(RED)Service not responding$(NC)"

health-monitor: ## Monitor health every 30 seconds
	@echo "$(BLUE)Monitoring service health...$(NC)"
	./scripts/monitor.sh 30

# API Testing
test-api: ## Test API endpoints (requires running service and API_KEY)
	@echo "$(BLUE)Testing API endpoints...$(NC)"
	@if [ -z "$$API_KEY" ]; then \
		echo "$(RED)ERROR: API_KEY environment variable not set$(NC)"; \
		echo "$(YELLOW)Usage: API_KEY=your-key make test-api$(NC)"; \
		exit 1; \
	fi
	./scripts/test-api.sh $$API_KEY
	@echo "$(GREEN)✓ API tests passed$(NC)"

# Database
db-test: ## Test database connection
	@echo "$(BLUE)Testing database connection...$(NC)"
	@docker compose -f docker-compose.dev.yml run --rm legacy-adapter python -c "from app.database import test_connection; exit(0 if test_connection() else 1)"
	@echo "$(GREEN)✓ Database connection successful$(NC)"

# Cleanup
clean: ## Clean up generated files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-docker: ## Clean up Docker containers and volumes
	@echo "$(BLUE)Cleaning up Docker resources...$(NC)"
	docker compose -f docker-compose.dev.yml down -v
	docker compose -f docker-compose.vps.yml down -v
	@echo "$(GREEN)✓ Docker cleanup complete$(NC)"

# Documentation
docs-serve: ## Serve documentation (requires mkdocs)
	@echo "$(BLUE)Serving documentation...$(NC)"
	@echo "$(YELLOW)Available docs:$(NC)"
	@echo "  - README.md: Project overview"
	@echo "  - TESTING.md: Testing guide"
	@echo "  - AUDIT.md: Audit controls guide"
	@echo "  - GETTING_STARTED.md: Quick start guide"

# Security
security-scan: ## Run security scan on dependencies
	@echo "$(BLUE)Running security scan...$(NC)"
	pip-audit
	@echo "$(GREEN)✓ Security scan complete$(NC)"

# Utilities
shell: ## Open Python shell in Docker container
	@echo "$(BLUE)Opening Python shell...$(NC)"
	docker compose -f docker-compose.dev.yml run --rm legacy-adapter python

shell-root: ## Open root shell in Docker container
	@echo "$(BLUE)Opening root shell...$(NC)"
	docker compose -f docker-compose.dev.yml run --rm --user root legacy-adapter /bin/sh

env-check: ## Check environment configuration
	@echo "$(BLUE)Checking environment configuration...$(NC)"
	@if [ -f .env ]; then \
		echo "$(GREEN)✓ .env file exists$(NC)"; \
		echo "$(YELLOW)Required variables:$(NC)"; \
		grep -E "^(LEGACY_DB_HOST|LEGACY_DB_USER|LEGACY_DB_PASSWORD|LEGACY_DB_NAME|API_KEY)" .env || echo "$(RED)Missing required variables$(NC)"; \
	else \
		echo "$(RED)✗ .env file not found$(NC)"; \
		echo "$(YELLOW)Copy .env.example to .env and configure$(NC)"; \
	fi

# CI/CD
ci: quality test-coverage ## Run CI pipeline (quality + coverage)
	@echo "$(GREEN)✓ CI pipeline passed$(NC)"

# Info
info: ## Show project information
	@echo "$(BLUE)Legacy Adapter Service Information$(NC)"
	@echo ""
	@echo "$(YELLOW)Version:$(NC) 1.0.0"
	@echo "$(YELLOW)Python:$(NC) $$(python --version 2>&1)"
	@echo "$(YELLOW)FastAPI:$(NC) $$(pip show fastapi 2>/dev/null | grep Version | cut -d' ' -f2)"
	@echo "$(YELLOW)Pytest:$(NC) $$(pip show pytest 2>/dev/null | grep Version | cut -d' ' -f2)"
	@echo ""
	@echo "$(YELLOW)Project Structure:$(NC)"
	@tree -L 2 -I '__pycache__|*.pyc|.pytest_cache|.ruff_cache|.mypy_cache|htmlcov' . 2>/dev/null || ls -la

.DEFAULT_GOAL := help
