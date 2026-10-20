# Nexora Architecture & System Design

## 1. Executive Overview

**Nexora** is an enterprise-grade, multi-tenant data processing, workflow orchestration, and operational reliability platform. It addresses the fundamental distributed system and backend engineering challenge:

> *How can a shared multi-tenant application process large, heterogeneous data workloads reliably, efficiently, and securely for independent organizations—guaranteeing strict data isolation, idempotency under retries, bounded memory footprint, transactional integrity, and actionable observability?*

The platform is designed as a modular monolith in Python/Django REST Framework, paired with a React 18 / TypeScript frontend, backed by PostgreSQL, Celery, and Redis.

```
                          ┌────────────────────────┐
                          │   React 18 / TS SPA    │
                          │   (Vite + TailwindCSS) │
                          └───────────┬────────────┘
                                      │ REST API / JWT
                                      ▼
               ┌──────────────────────────────────────────────┐
               │         Django REST Framework Core           │
               │                                              │
               │  ┌─────────────────┐    ┌─────────────────┐  │
               │  │  Tenant Guard   │    │ Role Permission │  │
               │  │  Context Layer  │    │   Enforcement   │  │
               │  └────────┬────────┘    └────────┬────────┘  │
               │           ▼                      ▼           │
               │  ┌────────────────────────────────────────┐  │
               │  │ Ingestion & Validation Service Engine  │  │
               │  └────────┬──────────────────────┬────────┘  │
               └───────────┼──────────────────────┼───────────┘
                           │                      │
            Enqueue Task   │                      │ Relational Queries &
                           ▼                      │ Row Locking
                 ┌──────────────────┐             ▼
                 │  Redis / Celery  │    ┌─────────────────┐
                 │  Async Workers   │───▶│   PostgreSQL    │
                 └──────────────────┘    │ Shared-Database │
                                         │  Shared-Schema  │
                                         └─────────────────┘
```

---

## 2. Multi-Tenancy Design

Nexora implements **shared-database, shared-schema multi-tenancy** with row-level logical separation enforced at every layer:

1. **Explicit Identity Anchoring:** Every tenant-scoped entity (`DatasetSchema`, `DataSource`, `ImportJob`, `ImportedRecord`, `ImportRowError`, `AuditEvent`, etc.) maintains a foreign key to `Organization`.
2. **Context Resolution:** The tenant context is extracted exclusively from the authenticated user's active membership or verified JWT payload—never from client-supplied URL query parameters or arbitrary request payloads.
3. **ORM Defense-in-Depth:**
   - Custom `TenantScopedManager` and `TenantScopedQuerySet` automatically filter queries by the tenant context.
   - Base DRF ViewSets automatically scope `get_queryset()` to `request.tenant`.
   - Serializers validate relationship integrity to ensure foreign keys (such as `dataset_schema`) belong strictly to the requesting tenant.
4. **Leak Prevention:** Requests attempting to access or manipulate foreign resources fail with `404 Not Found` rather than `403 Forbidden` to prevent object enumeration.

---

## 3. Core Engine Components

### A. Dynamic Schema & Validation Engine
Organizations define arbitrary data structures (`DatasetSchema` and `DatasetField`). Fields support primitive types (`string`, `integer`, `decimal`, `boolean`, `date`, `datetime`, `email`) along with declarative constraints (`min_length`, `max_length`, `min_value`, `max_value`, `regex`, `allowed_values`). The validator parses and validates rows in streaming chunks, never invoking dynamic code execution (`eval` or raw SQL).

### B. Ingestion & Idempotency Pipeline
CSV ingestion is handled through:
1. Streamed chunking to avoid loading unbounded files into memory.
2. Cryptographic checksumming (`SHA-256`) and idempotency keys to detect duplicate submissions.
3. Batch validation and transaction-managed persistence.
4. Structured row-level error reporting (`ImportRowError`) linked to exact row indices.
5. Deterministic retry mechanisms with bounded attempts and backoff.

### C. State Machine & Workflow Transitions
Import jobs transition through strict states:
`QUEUED` ➔ `PROCESSING` ➔ `COMPLETED` | `COMPLETED_WITH_ERRORS` | `FAILED` | `CANCELLED`.
Transitions emit auditable `WorkflowEvent` records and guarantee transactional consistency.

---

## 4. Operational Reliability & Concurrency

- **Idempotent Ingestion:** Duplicate file uploads with identical checksums within an organization are caught early, avoiding duplicate writes.
- **Race Condition Prevention:** Job status transitions and retry triggers utilize database row locking (`select_for_update()`) and atomic transactions.
- **Worker Crash Resilience:** Jobs record durable progress markers in PostgreSQL, enabling workers to resume or safely fail without leaving orphan states.
