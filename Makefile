.PHONY: help up down test seed clean lint

help:
	@echo "Available commands:"
	@echo "  make up       - Start all database containers (Postgres, Redis, MongoDB, Adminer)"
	@echo "  make down     - Stop all running database containers"
	@echo "  make test     - Run test suites for all modules (Postgres, Redis, MongoDB)"
	@echo "  make lint     - Run code quality linters (Ruff, ESLint)"
	@echo "  make seed     - Populate databases with sample data"
	@echo "  make clean    - Remove cached Python bytecode, lockfiles, and logs"

up:
	docker compose up -d

down:
	docker compose down

test:
	@echo "--- Testing 01-relational-postgres ---"
	PYTHONPATH=01-relational-postgres python3 -m unittest discover -s 01-relational-postgres/tests -v
	@echo ""
	@echo "--- Testing 02-cache-redis ---"
	npm --prefix 02-cache-redis test
	@echo ""
	@echo "--- Testing 03-document-mongodb ---"
	PYTHONPATH=03-document-mongodb python3 -m unittest discover -s 03-document-mongodb/tests -v

seed:
	@echo "--- Seeding MongoDB ---"
	python3 03-document-mongodb/src/catalog_service.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.rdb" -delete
