<div align="center">

# NEXORA

### Enterprise Multi-Tenant Data Processing, Workflow Orchestration & Reliability Platform

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django 6.0](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

<p align="center">
  <b>A fault-tolerant distributed system engineered for streaming CSV ingestion, declarative typed schema validation, cryptographic idempotency, pessimistic row-level concurrency locks, and strict multi-tenant isolation.</b>
</p>

[The Complete Guide (From Scratch) →](PROJECT_EXPLAINED_FROM_SCRATCH.md) • [Architecture Docs →](docs/architecture.md) • [API Guide →](docs/api-guide.md) • [Performance Benchmarks →](docs/performance.md)

</div>

---

## 1. Executive Summary & Problem Statement

Modern enterprise SaaS platforms ingest high-volume, variable datasets from external business units and partners. In distributed production environments, naive data ingestion pipelines fail consistently:

- **Memory Exhaustion (OOM):** Loading large files into memory (e.g. `pandas.read_csv()`) triggers worker crashes under concurrent load.
- **Data Corruption via Retries:** Transient network timeouts cause worker retries that duplicate database records.
- **Multi-Tenant Leakage:** Flawed query scoping leads to Insecure Direct Object References (IDOR), exposing private records across tenants.
- **State Machine Concurrency Bugs:** Multiple worker threads updating pipeline status simultaneously introduce race conditions.

**Nexora** is a production-grade platform built to solve these exact distributed systems challenges with mathematical and transactional guarantees.

---

## 2. System Architecture

```
                       +-----------------------------------+
                       |       React 18 + Vite SPA         |
                       |   (TypeScript, Tailwind CSS, UI)  |
                       +-----------------+-----------------+
                                         |  HTTP/REST (Bearer JWT + X-Organization-Id)
                                         v
                       +-----------------+-----------------+
                       |          Nginx Alpine             |
                       |  (Static Assets & Reverse Proxy)  |
                       +-----------------+-----------------+
                                         |  /api/v1/
                                         v
                       +-----------------+-----------------+
                       |       Gunicorn / Django           |
                       |  (Tenant Context, DRF, Security)  |
                       +--------+-----------------+--------+
                                |                 |
                    SQL Queries |                 | Celery Task Dispatch
                                v                 v
             +------------------+----+     +------+------------------+
             |  PostgreSQL 16 DB     |     |   Redis 7 (Broker/Cache)|
             |  (Composite Indexes,  |     +------+------------------+
             |   Row Locks, Cascades)|            |
             +-----------------------+            v
                                           +------+------------------+
                                           |   Celery Workers        |
                                           |   (Async Chunked Parser)|
                                           +-------------------------+
```

---

## 3. Core Architectural Highlights

| Feature | Production Implementation | Benefit |
| :--- | :--- | :--- |
| **Multi-Tenant Isolation** | Shared-database, shared-schema pattern with `TenantScopedModel` and `TenantJWTAuthentication`. | Absolute data isolation with zero cross-tenant query contamination. |
| **Chunked Streaming Parser** | Memory-bounded generator processing CSV rows in 500-item chunks committed in atomic transactions. | Constant $O(1)$ RAM usage; ingests 500MB+ files without memory spikes. |
| **Cryptographic Idempotency** | SHA-256 file checksums + `idempotency_key` headers + row-level deterministic `record_hash`. | Safe, deduplicated worker retries with zero duplicate database entries. |
| **Pessimistic Concurrency** | State transitions wrapped in `transaction.atomic()` with `select_for_update()` row locks. | Race-condition-free workflow progression (`QUEUED` $\to$ `PROCESSING` $\to$ `COMPLETED`). |
| **Declarative Validation** | Dynamic schema engine supporting string, integer, decimal, boolean, date, datetime, and email. | Zero `eval()` / `exec()` execution; safe parsing of untrusted inputs. |
| **Formula Injection Defense** | Automated prepending of single quotes (`'`) to strings starting with `=`, `+`, `-`, `@`, `\t`, `\r`. | Neutralizes CSV Formula Injection attacks (CWE-1236) upon export. |
| **Last-Admin Protection** | Relational constraint checking active admin counts before deletion or role demotion. | Guarantees an organization workspace cannot be orphaned. |

---

## 4. Quantitative Performance Benchmarks

Measured using the reproducible benchmark harness ([`scripts/performance_bench.py`](scripts/performance_bench.py)):

| Performance Experiment | Naive / Unoptimized | Nexora Optimized Pattern | Result & Impact |
| :--- | :--- | :--- | :--- |
| **Ingestion Throughput** | 293.67 ms (100 rows iterative `.save()`) | **34.51 ms** (`bulk_create` batch size 500) | **42.6x Speedup** (~14,490 rows/sec) |
| **Point Query Lookup** | Full table scan ($O(N)$) | B-tree index on `(org, schema, external_id)` | **0.542 ms** latency |
| **$N+1$ Query Cascades** | 11 SQL queries for 10 error records | `select_related('import_job')` | **1 single SQL query** (Constant $O(1)$) |

---

## 5. Quick Start & Local Execution

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- PostgreSQL & Redis (optional; SQLite fallback and eager execution are built-in for local dev)

### Seeded Demo Personas (1-Click Launch on Login Screen)
| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Operator** | `operator@nexora.io` | `NexoraSecurePass123!` | Upload CSVs, execute pipelines, inspect errors, retry jobs. |
| **Org Admin** | `admin@nexora.io` | `NexoraSecurePass123!` | Full workspace administration, manage team roles, create schemas. |
| **Analyst** | `analyst@nexora.io` | `NexoraSecurePass123!` | Query records, view analytics dashboards, export sanitized CSVs. |

### 1. Backend Setup
```bash
# Copy environment variables
cp .env.example .env

# Run database migrations
python backend/manage.py migrate

# Seed deterministic demo data (organizations, users, schemas, records)
python backend/manage.py seed_demo_data

# Start the Django API server
python backend/manage.py runserver 0.0.0.0:8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

---

## 6. Docker Compose Deployment

Run the complete production stack (PostgreSQL, Redis, Django, Celery Worker, Celery Beat, Nginx & React Frontend) with a single command:

```bash
docker compose up --build -d
```
Access endpoints:
- **Frontend SPA:** [http://localhost:3000](http://localhost:3000)
- **API Documentation (Swagger UI):** [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/)
- **API Schema (ReDoc):** [http://localhost:8000/api/schema/redoc/](http://localhost:8000/api/schema/redoc/)

---

## 7. Verification & Quality Test Suite

```bash
# 1. Run the entire Pytest suite (31 unit & integration tests)
pytest backend/tests/ -v --tb=short

# 2. Run the performance benchmark suite
python scripts/performance_bench.py

# 3. Check code formatting with Ruff
ruff check backend/
ruff format --check backend/

# 4. Type check and build frontend production bundle
cd frontend
npx tsc --noEmit
npm run build
```

---

## 8. Complete Documentation Index

- **[Master Educational Guide (From Scratch) →](PROJECT_EXPLAINED_FROM_SCRATCH.md)** (Every concept, every app, and 25+ senior interview Q&As explained simply)
- **[System Architecture & Design →](docs/architecture.md)**
- **[Database Schema & Indexing →](docs/database-design.md)**
- **[REST API Guide & Endpoints →](docs/api-guide.md)**
- **[Multi-Tenancy & Permissions →](docs/permissions.md)**
- **[Ingestion Pipeline & Retries →](docs/ingestion-design.md)**
- **[Security & Threat Model →](docs/security.md)**
- **[Performance Engineering & Benchmarks →](docs/performance.md)**
- **[Testing Strategy & Verification →](docs/testing.md)**
- **[Engineering Decisions & Trade-Offs →](docs/engineering-decisions.md)**

---

## 9. License
Distributed under the MIT License. See `LICENSE` for more information.
