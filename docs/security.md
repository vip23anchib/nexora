# Nexora Security & Threat Model

## 1. Multi-Tenant Isolation & Guardrails

- **Shared Database, Shared Schema:** All tables contain an `organization_id` column.
- **Tenant Context Injection:** A verified tenant context (`request.tenant`) is attached to each request by `TenantContextMiddleware`.
- **Queryset Scoping:** Views override `get_queryset()` to enforce `organization=self.request.tenant`.
- **No Direct Object Reference (IDOR):** Requesting objects outside the user's organization yields `404 Not Found`.

---

## 2. API & Data Security

- **Authentication:** Standard JWT (JSON Web Tokens) with short-lived access tokens (60 min) and rotatable refresh tokens.
- **Password Storage:** Django PBKDF2 with SHA-256 and high work-factor hashing.
- **CSV Injection Prevention:** Any CSV export sanitizes fields beginning with formula characters (`=`, `+`, `-`, `@`) by prepending a single quote (`'`).
- **File Upload Security:** Files are validated by MIME type and extension, size limits are enforced before streaming, and user-supplied file paths are never used in local file systems.
- **Audit Trail:** Every state-altering action records `actor`, `action`, `resource_type`, `resource_id`, and `request_id`. Sensitive parameters (passwords, tokens) are redacted prior to audit logging.

---

## 3. Health & Readiness Probes

- `/health/live/`: Verifies process vitality.
- `/health/ready/`: Validates PostgreSQL connectivity, Redis cache response, and migration state.
