.PHONY: help up down test seed clean

help:
	@echo "Available commands:"
	@echo "  make up       - Start all database containers (Postgres, Redis, MongoDB, Adminer)"
	@echo "  make down     - Stop all running database containers"
	@echo "  make test     - Run test suites for all modules"
	@echo "  make seed     - Populate databases with sample data"
	@echo "  make clean    - Remove cached Python bytecode and logs"

up:
	docker compose up -d

down:
	docker compose down

test:
	@echo "--- Testing 01-relational-postgres ---"
	PYTHONPATH=01-relational-postgres python3 -m unittest discover -s 01-relational-postgres/tests
	@echo "\n--- Testing 03-document-mongodb ---"
	PYTHONPATH=03-document-mongodb python3 -m unittest discover -s 03-document-mongodb/tests

seed:
	@echo "--- Seeding MongoDB ---"
	python3 03-document-mongodb/src/catalog_service.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.rdb" -delete
