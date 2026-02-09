.PHONY: init reset build up down restart logs shell db-shell migrate migrate-create migrate-history migrate-downgrade seed test test-cov lint format

# ─── Setup inicial (primera vez) ───

init:
	docker compose up --build -d
	@echo "Esperando a que la base de datos este lista..."
	docker compose exec api alembic upgrade head
	@echo ""
	@echo "=== Proyecto listo ==="
	@echo "API:  http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo ""

# ─── Docker ───

build:
	docker compose up --build -d

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down && docker compose up --build -d

logs:
	docker compose logs -f api

# ─── Shells ───

shell:
	docker compose exec api bash

db-shell:
	docker compose exec db psql -U postgres -d agrobot

# ─── Alembic ───

migrate:
	docker compose exec api alembic upgrade head

migrate-create:
	docker compose exec api alembic revision --autogenerate -m "$(name)"

migrate-history:
	docker compose exec api alembic history

migrate-downgrade:
	docker compose exec api alembic downgrade -1

# ─── Seed ───

seed:
	docker compose exec api python -c "import asyncio; from app.seeds.seed_data import seed; from app.database import async_session; asyncio.run((lambda: seed(async_session()))())"

# ─── Tests ───

test:
	-docker compose exec db psql -U postgres -c "CREATE DATABASE agrobot_test;"
	docker compose exec api pytest app/tests/ -v

test-cov:
	-docker compose exec db psql -U postgres -c "CREATE DATABASE agrobot_test;"
	docker compose exec api pytest app/tests/ -v --cov=app --cov-report=term-missing

# ─── Code Quality ───

lint:
	docker compose exec api ruff check app/

format:
	docker compose exec api ruff format app/

reset:
	docker compose down -v
	docker compose up --build -d
	@echo "Esperando a que la base de datos este lista..."
	docker compose exec api alembic upgrade head
	@echo ""
	@echo "=== Proyecto reiniciado desde cero ==="
	@echo "API:  http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo ""