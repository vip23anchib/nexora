# Nexora REST API Guide & Conventions

## 1. API Standards

All endpoints adhere to RESTful principles and are mounted under `/api/v1/`.

- **Payloads:** JSON (`application/json`) for endpoints except file uploads (`multipart/form-data`) and exports (`text/csv`).
- **Authentication:** Bearer token via `Authorization: Bearer <access_token>`.
- **Tenant Context Header (Optional Multi-Org Users):** `X-Organization-Id: <uuid>` selects the active tenant if a user belongs to multiple organizations. If omitted, the user's primary/first active organization is resolved.
- **Correlation ID:** Every response carries `X-Request-ID` for end-to-end tracing across logs, metrics, and audit events.

---

## 2. API Surface Summary

### Authentication (`/api/v1/auth/`)
- `POST /api/v1/auth/login/` - Authenticate with email/password, returns JWT pair + user info + organizations.
- `POST /api/v1/auth/token/refresh/` - Refresh expired access token.
- `GET /api/v1/auth/me/` - Retrieve current user profile, active organization, and role.
- `POST /api/v1/auth/logout/` - Blacklist refresh token and invalidate session.

### Organization & Team (`/api/v1/organization/`)
- `GET /api/v1/organization/` - Retrieve active organization details.
- `PATCH /api/v1/organization/` - Update organization profile/timezone (Admin only).
- `GET /api/v1/organization/members/` - List organization members.
- `POST /api/v1/organization/members/` - Invite/add a user with a specific role.
- `PATCH /api/v1/organization/members/{id}/` - Update membership role or status.
- `DELETE /api/v1/organization/members/{id}/` - Remove a user from the organization.

### Schemas (`/api/v1/schemas/`)
- `GET /api/v1/schemas/` - List organization schemas (supports pagination & search).
- `POST /api/v1/schemas/` - Create a new schema with fields and validation rules.
- `GET /api/v1/schemas/{id}/` - Retrieve full schema details with field definitions.
- `PATCH /api/v1/schemas/{id}/` - Update schema metadata or publish new version.
- `POST /api/v1/schemas/{id}/validate-sample/` - Test a sample CSV payload against the schema without persisting.
- `GET /api/v1/schemas/{id}/versions/` - List historical versions.

### Data Sources (`/api/v1/data-sources/`)
- `GET /api/v1/data-sources/` - List data sources.
- `POST /api/v1/data-sources/` - Register a data source.
- `GET /api/v1/data-sources/{id}/` - Retrieve data source details.
- `PATCH /api/v1/data-sources/{id}/` - Update configuration.
- `POST /api/v1/data-sources/{id}/deactivate/` - Deactivate source.

### Ingestion & Jobs (`/api/v1/ingestion/jobs/`)
- `POST /api/v1/ingestion/jobs/` - Upload CSV and trigger import job.
- `GET /api/v1/ingestion/jobs/` - List import jobs with status, counts, and duration.
- `GET /api/v1/ingestion/jobs/{id}/` - Detailed job status, metrics, and error summary.
- `GET /api/v1/ingestion/jobs/{id}/errors/` - Paginated row-level validation errors.
- `POST /api/v1/ingestion/jobs/{id}/retry/` - Safe, idempotent retry of failed/partial jobs.
- `POST /api/v1/ingestion/jobs/{id}/cancel/` - Cancel a queued or active job.

### Records Explorer (`/api/v1/records/`)
- `GET /api/v1/records/` - Query ingested records with JSON payload search and schema filtering.
- `GET /api/v1/records/{id}/` - Retrieve record details and provenance.

### Analytics (`/api/v1/analytics/`)
- `GET /api/v1/analytics/dashboard/` - High-level operational KPIs.
- `GET /api/v1/analytics/ingestion-trends/` - Historical throughput and volume trends.
- `GET /api/v1/analytics/failure-distribution/` - Breakdown of errors by code and field.
- `GET /api/v1/analytics/processing-performance/` - Average/median processing durations.
- `GET /api/v1/analytics/schema-usage/` - Dataset popularity and ingestion volumes.

### Audit & Notifications (`/api/v1/audit-events/`, `/api/v1/notifications/`)
- `GET /api/v1/audit-events/` - Immutable audit log of operational actions.
- `GET /api/v1/notifications/` - User/tenant operational notifications.
- `GET /api/v1/notifications/unread-count/` - Count of unread alerts.
- `POST /api/v1/notifications/{id}/mark-read/` - Mark notification as read.

### Exports (`/api/v1/exports/`)
- `GET /api/v1/exports/records/?schema_id={id}` - Safe CSV export of records.
- `GET /api/v1/exports/jobs/` - Safe CSV export of job logs and metrics.
