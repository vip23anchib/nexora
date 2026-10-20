# Nexora Engineering Decisions & Architecture Trade-Offs

## 1. Architectural Style: Modular Monolith vs Microservices

**Decision:** Implement Nexora as a clean, modular monolith within Django rather than distributed microservices.
**Rationale:** Microservices introduce distributed transactions, network latency, distributed tracing overhead, and complex local development without providing tangible scalability benefits for early-to-mid stage enterprise platforms. A modular monolith with strict domain boundaries (`apps/schemas`, `apps/ingestion`, `apps/records`, `apps/workflows`) achieves clean decoupling, unified database migrations, atomic multi-table transactions, and straightforward deployments.

---

## 2. Multi-Tenancy: Shared-Database, Shared-Schema vs Separate Schemas

**Decision:** Adopt shared-database, shared-schema with logical `organization_id` column partitioning.
**Rationale:** Separate PostgreSQL schemas (`django-tenants`) create heavy migration burdens (running N migrations for N tenants), table bloat, and connection pooling complexity. Shared-schema with indexed `organization_id` foreign keys and custom QuerySet managers provides high tenant density, simple schema evolution, predictable connection pooling, and strict logical isolation enforced at the ORM layer.

---

## 3. Asynchronous Execution: Celery + Redis with Eager Fallback

**Decision:** Celery with Redis broker as the asynchronous engine, with support for synchronous eager execution (`CELERY_TASK_ALWAYS_EAGER=True`) during testing or lightweight environments.
**Rationale:** Long-running data ingestion must not block web worker HTTP threads. Celery provides battle-tested worker pools, retries, and task state tracking. Durable state remains anchored in the PostgreSQL database rather than relying solely on ephemeral task broker state.

---

## 4. Frontend: React 18 + TypeScript + Vite + TailwindCSS

**Decision:** Single-Page Application (SPA) with React 18, TypeScript, TailwindCSS, and TanStack Query.
**Rationale:** An operations and data engineering dashboard demands responsive, interactive tables, dynamic charting, and instant feedback without full-page reloads. TanStack Query handles server state caching, pagination, and background refetching cleanly.
