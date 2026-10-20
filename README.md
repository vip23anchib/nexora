# Nexora

> **Enterprise Multi-Tenant Data Processing, Workflow Orchestration & Operational Reliability Platform**

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django 6.0](https://img.shields.io/badge/Django-6.0-green.svg)](https://www.djangoproject.com/)
[![React 18](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue.svg)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-blue.svg)](https://www.postgresql.org/)
[![Celery](https://img.shields.io/badge/Celery-5-green.svg)](https://docs.celeryq.dev/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)

---

## 1. Overview & Problem Statement

Modern enterprise applications ingest large, variable data files from diverse partners and internal business units. The core distributed system challenge is:

> **How can a shared backend process heterogeneous data reliably, efficiently, and securely for independent organizations—guaranteeing strict multi-tenant isolation, idempotency during network retries, bounded memory footprint, transactional integrity, and actionable operational observability?**

**Nexora** is a production-grade SaaS platform built to solve this problem. Organizations can dynamically declare dataset schemas, upload CSV payloads, stream validation across records, safely retry failed batches without duplicating side effects, and monitor operations via real-time analytics.

---

## 2. Core Features

- **Multi-Tenant Isolation:** Shared-database, shared-schema architecture strictly scoped by organization at the ORM, view, and serializer layers.
- **Dynamic Dataset Schemas:** Configurable data schemas supporting primitive types (`string`, `integer`, `decimal`, `boolean`, `date`, `datetime`, `email`) and constraint rules.
- **Robust Ingestion Pipeline:** Streamed CSV processing with SHA-256 deduplication, row-level validation, structured error reporting, and bounded memory usage.
- **Idempotency & Safe Retries:** Cryptographic checksums and state machine controls prevent duplicate record insertion under worker retries.
- **Asynchronous Processing:** Celery + Redis background job execution with resilient database state synchronization.
- **Operational Analytics:** Real-time metrics on ingestion throughput, failure code distributions, and schema utilization.
- **Security & Auditability:** Role-Based Access Control (Platform Admin, Org Admin, Operator, Analyst, Viewer), immutable audit logs, sanitized CSV exports, and security headers.
- **Enterprise UI:** Polished, responsive React 18 + TypeScript SPA with deep navy sidebar, clean typography, dynamic Recharts visualizations, and TanStack Query state caching.

---

## 3. Technology Stack

- **Backend:** Python 3.12, Django 6.0, Django REST Framework, Simple JWT, django-filter, drf-spectacular.
- **Database:** PostgreSQL 16 (with automated fallback to SQLite for local lightweight development).
- **Asynchronous Task Queue:** Celery 5, Redis 7.
- **Testing & Quality:** pytest, pytest-django, factory_boy, ruff.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide React, Axios, Recharts.
- **Infrastructure & CI:** Docker, Docker Compose, GitHub Actions.

---

## 4. Quick Start (Local Development)

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- PostgreSQL & Redis (optional; SQLite and eager tasks are supported for local dev)

### Seed Demo Personas
| Role | Email | Password |
| :--- | :--- | :--- |
| **Org Admin** | `admin@nexora.io` | `NexoraSecurePass123!` |
| **Operator** | `operator@nexora.io` | `NexoraSecurePass123!` |
| **Analyst** | `analyst@nexora.io` | `NexoraSecurePass123!` |

### Backend Setup
```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Run database migrations
python backend/manage.py migrate

# 3. Seed deterministic demo data (2 organizations, multiple roles, schemas, sample records)
python backend/manage.py seed_demo_data

# 4. Start the Django development server
python backend/manage.py runserver 0.0.0.0:8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 5. Docker Compose Deployment

Run the entire production stack (PostgreSQL, Redis, Django, Celery Worker, Celery Beat, Nginx & React Frontend) with a single command:

```bash
docker compose up --build -d
```
The application will be accessible at:
- **Frontend SPA:** [http://localhost:3000](http://localhost:3000)
- **API Documentation (Swagger):** [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/)

---

## 6. Performance Benchmarks

Run the automated database query and throughput benchmark suite:

```bash
python scripts/performance_bench.py
```
- **Batched Ingestion:** ~14,490 rows/sec (42.6x faster than iterative `.save()`)
- **Indexed Point Lookups:** 0.542 ms latency
- **N+1 Query Elimination:** 10 redundant queries eliminated (100% constant $O(1)$)

---

## 7. Documentation Directory

- [Architecture & System Design](docs/architecture.md)
- [Database Schema & Models](docs/database-design.md)
- [REST API Guide](docs/api-guide.md)
- [Role-Based Access Control & Permissions](docs/permissions.md)
- [Data Ingestion & Fault Tolerance](docs/ingestion-design.md)
- [Security & Threat Model](docs/security.md)
- [Performance Engineering & Indexing](docs/performance.md)
- [Testing Strategy & Verification](docs/testing.md)
- [Engineering Decisions & Trade-Offs](docs/engineering-decisions.md)

---

## 8. License
MIT License.
