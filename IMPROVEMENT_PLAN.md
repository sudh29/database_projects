---
repo: database_projects
review_date: 2026-10-27
current_score: 8.6
target_score: 9.6
---

# Repository Improvement Plan: `database_projects`

> **Hiring-Bar Audit Target:** AI Engineer / Staff IC / Systems Architect (~8 years experience)  
> **Evaluation Threshold:** 9.5+ / 10.0  
> **Current Overall Score:** **8.6 / 10.0** (Delta to 9.5 bar: +0.9)

---

## 1. Baseline Scorecard & Gaps

| # | Criterion | Weight | Score | Primary Gap / Finding |
|---|---|:---:|:---:|---|
| 1 | **Correctness & functionality** | 15% | **8.8** | All unit tests pass cleanly in <0.02s. In-memory simulations work. Gap: `make test` skips `02-cache-redis`; `queries.py`, `dataStructuresDemo.js`, and `benchmark.js` crash immediately without live databases rather than providing mock or dry-run fallbacks. |
| 2 | **Architecture & design** | 15% | **9.2** | Clean 3-module paradigm separation, Cache-Aside, sliding-window rate limiter, polymorphic document catalog. Gap: Repositories act as isolated silos rather than demonstrating a unified polyglot service flow; inconsistency in `AGENTS.md` referencing `02-keyvalue-redis`. |
| 3 | **Code quality** | 10% | **8.8** | Clean Python and JS code, Decimal precision for currency, timezone normalization. Gap: Missing linter/formatter configurations (Ruff, ESLint); sparse type hints; broad `except Exception` blocks. |
| 4 | **Testing & CI** | 15% | **6.8** | Unit tests present across all 3 modules with zero external dependencies. Gap: Complete absence of remote GitHub Actions CI (`.github/workflows/` does not exist); `make test` skips Redis tests; low test volume (15 assertions total); zero tests for `queries.py` and `rateLimiter.js`; no coverage metrics. |
| 5 | **Security** | 10% | **9.2** | Zero hardcoded secrets, parameterized SQL queries, input date validation. Gap: `package-lock.json` is gitignored breaking reproducible builds and `npm audit`; Redis in Docker Compose runs without password authentication (`requirepass`). |
| 6 | **Reliability & performance** | 10% | **8.8** | Cache-bypass fallback in Express; in-memory fallback in MongoDB service; SQL-side aggregation via CTE. Gap: Python database clients lack connection pooling (`psycopg2.pool.ThreadedConnectionPool`), violating `AGENTS.md` invariant: "Database clients must use connection pooling; avoid opening unpooled single connections per query." |
| 7 | **DevEx & ops** | 10% | **8.5** | Multi-container Docker Compose with healthchecks, Adminer GUI, `.env.example`, Makefile. Gap: `make test` skips Redis; `make seed` only seeds Mongo; literal `\n` in Makefile output; no root package manifest. |
| 8 | **Documentation** | 5% | **9.3** | 9.7KB root README with 10-dimension comparison matrix and Mermaid decision flowchart. Gap: Missing formal Architecture Decision Records (ADRs); typo in `AGENTS.md` directory mapping (`02-keyvalue-redis`). |
| 9 | **Repo hygiene** | 5% | **8.4** | MIT License, clean git history. Gap: `package-lock.json` gitignored; untracked `AGENTS.md`; missing `.github/` CI; missing linter configurations. |
| 10 | **Impact & clarity** | 5% | **9.3** | Demonstrates deep mastery across 3 primary database paradigms; real-world mathematical correction in customer aggregation; live latency benchmark. Gap: Lacks end-to-end polyglot transaction demonstration. |

---

## 2. Ranked Gaps (Impact ÷ Effort)

| Rank | Gap Description | Affected Criterion | Impact | Effort | Priority |
|:---:|---|---|:---:|:---:|:---:|
| 1 | Create GitHub Actions CI pipeline (`.github/workflows/ci.yml`) for multi-stack testing | Testing & CI, Hygiene | High | S | Phase 1 |
| 2 | Unify root `Makefile` test target to run Python and Node.js tests, and fix literal `\n` echo | DevEx & Ops, Correctness | High | S | Phase 1 |
| 3 | Remove `package-lock.json` from `.gitignore`, commit lockfile, and enable `npm audit` | Security, Hygiene | High | S | Phase 1 |
| 4 | Implement PostgreSQL connection pooling via `psycopg2.pool.ThreadedConnectionPool` | Reliability, Architecture | High | S | Phase 1 |
| 5 | Add unit tests for `rateLimiter.js` and mock unit tests for `queries.py` (ACID & Window Functions) | Testing & CI, Correctness | High | M | Phase 1 |
| 6 | Add Python (Ruff, Mypy) and JS (ESLint) linter/formatter configurations | Code Quality, Hygiene | Medium | S | Phase 2 |
| 7 | Add live container integration test job in GitHub Actions with service containers | Testing & CI, Reliability | High | M | Phase 2 |
| 8 | Correct `AGENTS.md` directory mapping (`02-cache-redis`) and update seeding targets | Documentation, DevEx | Low | S | Phase 2 |
| 9 | Add end-to-end polyglot gateway service connecting Postgres, Redis, and Mongo | Architecture, Impact | High | L | Phase 3 |
| 10 | Add Architecture Decision Records (ADR-001 Paradigm Selection, ADR-002 Caching Policy) | Documentation | Low | S | Phase 3 |

---

## 3. Phased Action Plan

### Phase 1: MVP-Essential (Target: Cross 9.5 Bar)

Focus on establishing remote CI automation, unifying the test runner across both Python and Node.js, fixing dependency locking and security auditing, implementing connection pooling, and expanding unit test coverage.

#### Task 1.1: GitHub Actions Remote CI Workflow
- **Description:** Create `.github/workflows/ci.yml` with automated jobs:
  1. `test-python`: Sets up Python 3.12, runs `python3 -m unittest discover` for Postgres and MongoDB.
  2. `test-node`: Sets up Node.js 20, installs dependencies in `02-cache-redis`, runs `npm test` and `npm audit`.
  3. `validate-compose`: Validates `docker-compose.yml` via `docker compose config`.
- **Why:** The repository has zero automated verification on pushes or pull requests.
- **Files Affected:** `.github/workflows/ci.yml`.
- **Acceptance Criteria:** CI runs and passes on `main` and `dev` branches.
- **Effort:** Small.
- **Score Delta:** Testing & CI: +1.4, Repo Hygiene: +0.6.

#### Task 1.2: Unify Root `Makefile` Lifecycle & Test Execution
- **Description:** Refactor `make test` in [Makefile](file:///home/liberprimus/code/database_projects/Makefile) to execute:
  ```makefile
  test:
  	@echo "--- Testing 01-relational-postgres ---"
  	PYTHONPATH=01-relational-postgres python3 -m unittest discover -s 01-relational-postgres/tests -v
  	@echo ""
  	@echo "--- Testing 02-cache-redis ---"
  	cd 02-cache-redis && npm test
  	@echo ""
  	@echo "--- Testing 03-document-mongodb ---"
  	PYTHONPATH=03-document-mongodb python3 -m unittest discover -s 03-document-mongodb/tests -v
  ```
  Fix the literal `\n` bug by using `@echo ""` or `printf`. Expand `make seed` to seed both MongoDB catalog and PostgreSQL initial transactions.
- **Why:** Single canonical entry point must verify all submodules without skipping Redis.
- **Files Affected:** `Makefile`.
- **Acceptance Criteria:** Running `make test` executes tests for all 3 paradigms and exits code 0.
- **Effort:** Small.
- **Score Delta:** DevEx & Ops: +0.6, Correctness: +0.4.

#### Task 1.3: Commit `package-lock.json` and Enable `npm audit`
- **Description:** Remove line 3 (`package-lock.json`) from [.gitignore](file:///home/liberprimus/code/database_projects/.gitignore). Run `npm i --package-lock-only` in `02-cache-redis` to generate a clean lockfile and track it in git. Ensure `npm audit` runs cleanly.
- **Why:** In production Node.js engineering, ignoring `package-lock.json` prevents reproducible builds and breaks vulnerability auditing.
- **Files Affected:** `.gitignore`, `02-cache-redis/package-lock.json`.
- **Acceptance Criteria:** `npm audit` in `02-cache-redis` executes cleanly with 0 vulnerabilities.
- **Effort:** Small.
- **Score Delta:** Security: +0.4, Repo Hygiene: +0.4.

#### Task 1.4: Implement Connection Pooling for PostgreSQL Service
- **Description:** Update [01-relational-postgres/src/money_club_sol.py](file:///home/liberprimus/code/database_projects/01-relational-postgres/src/money_club_sol.py) and [01-relational-postgres/src/queries.py](file:///home/liberprimus/code/database_projects/01-relational-postgres/src/queries.py) to implement `psycopg2.pool.ThreadedConnectionPool` with a context manager helper (`get_connection()`).
- **Why:** Spawning unpooled individual connections per query risks connection exhaustion and violates the repository's own `AGENTS.md` invariant.
- **Files Affected:** `01-relational-postgres/src/money_club_sol.py`, `01-relational-postgres/src/queries.py`.
- **Acceptance Criteria:** Connection pool manages client connections with explicit acquisition and return to pool.
- **Effort:** Small.
- **Score Delta:** Reliability & Performance: +0.5, Architecture: +0.2.

#### Task 1.5: Expand Unit Test Coverage for Untested Modules
- **Description:**
  1. In `02-cache-redis/tests/server.test.js`: Add unit tests for `rateLimiter.js` verifying sliding-window rate limit enforcement (allowing under limit, returning 429 when limit exceeded, and bypass when Redis is offline).
  2. In `01-relational-postgres/tests/`: Add `test_queries.py` mocking cursor results to test window function parsing and transaction rollback handling in `queries.py`.
- **Why:** Brings test coverage to 100% of modules, validating edge cases and error handling.
- **Files Affected:** `02-cache-redis/tests/server.test.js`, `01-relational-postgres/tests/test_queries.py`.
- **Acceptance Criteria:** Test suite expands from 15 to 25+ assertions with 100% pass rate.
- **Effort:** Medium.
- **Score Delta:** Testing & CI: +0.8, Correctness: +0.3.

---

### Phase 2: Hardening & Code Quality (Target: 9.6+)

#### Task 2.1: Python & JavaScript Linting and Static Typing
- **Description:** Add `pyproject.toml` with Ruff and Mypy strict configurations. Add `eslint.config.js` with Prettier formatting in `02-cache-redis`. Add `make lint` and `make format` to the root Makefile.
- **Why:** Standardizes code style and catches typing bugs before runtime.
- **Files Affected:** `pyproject.toml`, `02-cache-redis/eslint.config.js`, `Makefile`.
- **Acceptance Criteria:** `make lint` passes cleanly across all Python and JS files.
- **Effort:** Small.
- **Score Delta:** Code Quality: +0.6, Repo Hygiene: +0.3.

#### Task 2.2: Live Database Integration Test Harness in CI
- **Description:** Add a dedicated `integration-test` job in `.github/workflows/ci.yml` using GitHub Actions service containers (`postgres:16`, `redis:7`, `mongo:7`). Execute `queries.py`, `dataStructuresDemo.js`, and live MongoDB queries against real database instances.
- **Why:** Complements unit mocks with genuine database protocol verification.
- **Files Affected:** `.github/workflows/ci.yml`, `scripts/run_integration_tests.sh`.
- **Acceptance Criteria:** Integration job runs in CI and passes all real DB assertions.
- **Effort:** Medium.
- **Score Delta:** Testing & CI: +0.4, Reliability: +0.3.

#### Task 2.3: Fix `AGENTS.md` Directory Mapping & Documentation Polish
- **Description:** Correct `02-keyvalue-redis` to `02-cache-redis` in `AGENTS.md`. Track `AGENTS.md` in git. Add documentation on running tests and benchmarks locally.
- **Why:** Eliminates inconsistency and keeps repository documentation accurate.
- **Files Affected:** `AGENTS.md`.
- **Acceptance Criteria:** `AGENTS.md` reflects accurate directory names and is tracked cleanly.
- **Effort:** Small.
- **Score Delta:** Documentation: +0.3, DevEx & Ops: +0.2.

---

### Phase 3: Nice-to-Have (Target: 9.7+)

#### Task 3.1: Polyglot E-Commerce Gateway Demonstration Service
- **Description:** Build a unified service demonstrating an end-to-end polyglot flow:
  1. Product catalog fetched from MongoDB.
  2. Frequently queried product documents cached in Redis with sliding-window rate limiting.
  3. Orders and financial transactions committed with strict ACID guarantees in PostgreSQL.
- **Why:** Elevates the repository from 3 independent modules to a cohesive, enterprise-grade multi-database architecture showcase.
- **Files Affected:** `04-polyglot-gateway/` or `src/polyglot_service.py`.
- **Acceptance Criteria:** Single endpoint `/order` executes complete cross-database workflow.
- **Effort:** Large.
- **Score Delta:** Architecture: +0.3, Impact & Clarity: +0.3.

#### Task 3.2: Architecture Decision Records (ADRs)
- **Description:** Add `docs/adr/ADR-001-multi-paradigm-database-selection.md` and `docs/adr/ADR-002-cache-aside-and-sliding-window-rate-limiting.md`.
- **Why:** Demonstrates Staff IC architectural decision rigor.
- **Files Affected:** `docs/adr/*.md`.
- **Acceptance Criteria:** ADRs follow standard Michael Nygard format.
- **Effort:** Small.
- **Score Delta:** Documentation: +0.4.

---

## 4. Projected Score Progression

| Phase | Milestone | Expected Score | Delta |
|:---:|---|:---:|:---:|
| **Baseline** | Current audit baseline | **8.6** | — |
| **Phase 1** | Remote CI workflow, unified Makefile test runner, lockfile commit, connection pooling, expanded unit tests | **9.5** | +0.9 |
| **Phase 2** | Ruff/ESLint quality gates, live service container integration tests, AGENTS.md fix | **9.6** | +0.1 |
| **Phase 3** | Polyglot cross-database gateway demonstration, Architecture Decision Records (ADRs) | **9.7** | +0.1 |

---

## 5. Definition of Done for Reaching 9.5+

- [ ] GitHub Actions CI workflow executing on push/PR for Python, Node.js, and Docker Compose.
- [ ] Root `make test` executes tests across PostgreSQL, Redis, and MongoDB in a single command.
- [ ] `package-lock.json` committed and `npm audit` passing with 0 vulnerabilities.
- [ ] `psycopg2.pool.ThreadedConnectionPool` implemented for PostgreSQL clients.
- [ ] Unit test coverage expanded for `rateLimiter.js` and `queries.py`.
- [ ] Working tree clean on active branch.
