# Nexora Testing Strategy & Verification Suite

## 1. Automated Test Pyramid

The Nexora test suite is automated via `pytest` and `pytest-django`:

```
                 / \
                /   \
               / E2E \   (Frontend + Backend Full Workflows)
              /-------\
             /  Integ  \  (Cross-tenant Security, Transactions, DB Locks)
            /-----------\
           /    Unit     \ (Validators, Schema Engines, Serializers, RBAC)
          /---------------\
```

---

## 2. Core Test Categories

1. **Multi-Tenant Security Tests:**
   - Seed two distinct organizations (`Org Alpha`, `Org Beta`).
   - Authenticate as user of Org Alpha and attempt to read, update, delete, or link resources belonging to Org Beta.
   - Assert `404 Not Found` or validation failure on all attempts.
2. **Schema Validation Tests:**
   - Test data types: string, integer, decimal, boolean, date, datetime, email.
   - Test edge cases: invalid formats, missing required fields, boundary violations, malicious strings.
3. **Ingestion & Idempotency Tests:**
   - Ingest valid CSV, invalid CSV, partial CSV.
   - Retry failed jobs and verify no duplicate records are created.
   - Submit duplicate files and verify idempotency behavior.
4. **Transaction & Concurrency Tests:**
   - Test race conditions in job status transitions and retry calls.
