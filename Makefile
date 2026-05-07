# =============================================================================
# XChange Platform — Makefile (Linux / macOS / VPS)
# For Windows, use: .\scripts\dev.ps1 <command>
# =============================================================================

.PHONY: help up down build logs ps clean migrate seed lint test

help:
	@echo ""
	@echo "XChange Platform — Available Commands"
	@echo "======================================"
	@echo "  make up       Start all services (detached)"
	@echo "  make down     Stop all services"
	@echo "  make build    Rebuild all Docker images"
	@echo "  make logs     Tail all service logs"
	@echo "  make ps       Show running containers and status"
	@echo "  make clean    Stop services and remove all volumes (WARNING: deletes local data)"
	@echo "  make migrate  Run database migrations (Alembic upgrade head)"
	@echo "  make seed     Run database seed scripts"
	@echo "  make lint     Run ruff linter on all Python services"
	@echo "  make test     Run all tests via pytest"
	@echo ""

up:
	docker compose up -d
	@echo "All services started. Run 'make ps' to check status."

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps

clean:
	@echo "WARNING: This will delete all local database data."
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] || exit 1
	docker compose down -v --remove-orphans

migrate:
	@echo "Running migrations for user-service..."
	docker compose exec user-service alembic upgrade head
	@echo "Running migrations for order-service..."
	docker compose exec order-service alembic upgrade head
	@echo "Running migrations for market-data-service..."
	docker compose exec market-data-service alembic upgrade head
	@echo "Running migrations for portfolio-service..."
	docker compose exec portfolio-service alembic upgrade head
	@echo "Running migrations for wallet-service..."
	docker compose exec wallet-service alembic upgrade head
	@echo "Running migrations for risk-service..."
	docker compose exec risk-service alembic upgrade head
	@echo "Running migrations for notification-service..."
	docker compose exec notification-service alembic upgrade head
	@echo "Running migrations for admin-service..."
	docker compose exec admin-service alembic upgrade head
	@echo "All migrations complete."

seed:
	@echo "Running seed scripts..."
	docker compose exec market-data-service python scripts/seed_trading_pairs.py
	@echo "Seed complete."

lint:
	@echo "Running ruff linter..."
	pip install ruff --quiet
	ruff check services/ --ignore E501
	@echo "Lint complete."

test:
	@echo "Running tests..."
	pip install pytest pytest-asyncio httpx --quiet
	pytest services/ -v --tb=short
