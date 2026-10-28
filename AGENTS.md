# AGENTS.md — Universal Agent Operating Standard: database_projects

> **Repository:** `/home/liberprimus/code/database_projects`  
> **Workspace Authority:** `sudh29` (`liberprimus`)  
> **Tier:** Tier B (Multi-Paradigm Database Engineering & Systems Showcase)  
> **Active Branch:** `dev`  
> **Applicable Agents:** Antigravity, Claude Code, Cursor, Gemini, Codex


---

## 1. Repository Purpose & Architecture

- **Overview:** `database_projects` demonstrates production-ready patterns across multi-paradigm database systems. It includes relational schema modeling with PostgreSQL 16, high-speed in-memory caching and session management with Redis 7, and flexible document catalog storage with MongoDB 7, complete with automated unittests and Docker Compose infrastructure.
- **Key Directory Map:**
  - `01-relational-postgres/`: PostgreSQL schemas, indexing strategies, transactions, and Python unittest suites.
  - `02-cache-redis/`: Redis caching layers, pub/sub queues, and rate-limiting patterns.
  - `03-document-mongodb/`: MongoDB document schemas, aggregation pipelines, and catalog services.
  - `docker-compose.yml`: Multi-container database definitions.
  - `Makefile`: Canonical lifecycle commands.
- **Architectural Invariants:**
  - **Schema Isolation:** Each paradigm module is self-contained with its own models and tests.
  - **Transaction Rigor:** Relational operations must demonstrate ACID compliance with explicit rollback on error.
  - **Connection Pooling:** Database clients must use connection pooling; avoid opening unpooled single connections per query.

### Key Architecture & Entry Points

- **Build Orchestration:** [`Makefile`](file:///home/liberprimus/code/database_projects/Makefile)
- **Container Setup:** [`docker-compose.yml`](file:///home/liberprimus/code/database_projects/docker-compose.yml)
- **Postgres Module:** `01-relational-postgres/`
- **Redis Module:** `02-cache-redis/`
- **MongoDB Module:** `03-document-mongodb/`

---

## 2. Coding Style & Engineering Conventions

- Modular Python structure with clear separation of schemas, repository layers, and tests.
- Always handle connection teardown and transaction commits/rollbacks explicitly.

---

## 3. Toolchain & Environment Matrix

- **Services:** Docker, Docker Compose (Postgres 16, Redis 7, MongoDB 7)
- **Runtime:** Python 3.12+ (unittest, psycopg/SQLAlchemy, pymongo, redis-py)
- **Build System:** GNU Make

### Canonical Commands
All commands run from `/home/liberprimus/code/database_projects`:

| Action | Command | Purpose |
|:---|:---|:---|
| **Start Containers** | `make up` | Launch all database containers in background |
| **Stop Containers**  | `make down` | Stop all running database containers |
| **Run Test Suites**  | `make test` | Execute unit tests across Postgres and MongoDB modules |
| **Seed Test Data**   | `make seed` | Populate catalog collections with initial sample data |
| **Clean Bytecode**   | `make clean` | Remove `__pycache__`, `.pyc`, and `.rdb` files |

### Quick-Start Workflow

```bash
# Infrastructure Lifecycle
make up                     # Launch Postgres, Redis, MongoDB containers
make down                   # Tear down database containers

# Testing & Seeding
make test                   # Run unit test suites for Postgres & Mongo
make seed                   # Populate MongoDB catalog with sample data
make clean                  # Clean Python cache and dump files
```

---

## 4. Operational Safety & Agent Boundaries

1. **Blast Radius Containment:** Strictly confine edits to `/home/liberprimus/code/database_projects`.
2. **Verification Mandate:** Run `make test` against local or mock database fixtures before concluding tasks.
3. **Branch Discipline:** Active working branch is `dev`.
4. **Secret Hygiene:** Database credentials in `docker-compose.yml` are local development defaults; never commit production passwords.

---

## 5. Definition of Done
- [ ] Database schemas and Python clients execute cleanly.
- [ ] Test suites pass (`make test`).
- [ ] Docker compose definitions are syntactically valid.
- [ ] Working tree is clean.
