# Nexora Permissions & Role-Based Access Control (RBAC)

## 1. Overview

Nexora enforces multi-tenant role-based access control at the API and service layer. Authentication verifies user identity; organization membership resolves the tenant boundary and assigns the user's role within that tenant.

---

## 2. Role Definitions

| Role | Target Persona | Scope & Capability |
| :--- | :--- | :--- |
| **Platform Admin** | Internal SRE / Platform Operator | Global operational health, tenant listing, platform metrics. **Zero direct access** to tenant customer data without audited, explicit session escalation. |
| **Org Admin** (`org_admin`) | Tenant Owner / Lead Engineer | Full administrative authority within the organization: invite members, update roles, edit schemas, manage data sources, view audit logs. |
| **Operator** (`operator`) | Operations / Data Engineer | Schema creation/updates, data source management, uploading CSVs, triggering ingestion, running retries, canceling jobs. |
| **Analyst** (`analyst`) | Business / BI Analyst | Read-only access to records, schemas, jobs, row-level errors, analytics dashboards, and data exports. |
| **Viewer** (`viewer`) | Read-Only Stakeholder | Basic dashboard access, read-only viewing of schemas and completed jobs. No export, schema modification, or ingestion triggers. |

---

## 3. Role-Permission Matrix

| Resource / Action | Platform Admin | Org Admin | Operator | Analyst | Viewer |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Manage Org Settings** | Platform-level only | Yes | No | No | No |
| **Manage Team Members** | No | Yes | No | No | No |
| **Create/Update Schemas** | No | Yes | Yes | No | No |
| **View Schemas** | No | Yes | Yes | Yes | Yes |
| **Configure Data Sources**| No | Yes | Yes | No | No |
| **Trigger Import Jobs** | No | Yes | Yes | No | No |
| **Retry / Cancel Jobs** | No | Yes | Yes | No | No |
| **View Jobs & Errors** | Health metrics | Yes | Yes | Yes | Yes |
| **View Imported Records** | No | Yes | Yes | Yes | Yes |
| **Export Records / Data**| No | Yes | Yes | Yes | No |
| **View Analytics** | Platform health | Yes | Yes | Yes | Yes |
| **View Audit Trail** | Platform audit | Yes | No | No | No |

---

## 4. Enforcement Mechanisms

1. **`IsTenantMember` Permission Class:** Validates that `request.user` has an active `OrganizationMembership` for the active organization.
2. **`HasTenantRole` Permission Class:** Checks that `request.membership.role` is included in the allowed roles for the endpoint action.
3. **Defense Against IDOR:** Querysets are filtered by `organization = request.tenant`. Attempting to access an ID belonging to another organization returns HTTP 404 (Not Found).
4. **Last Admin Protection:** Deleting or demoting the last `org_admin` of an active organization is rejected with HTTP 400.
