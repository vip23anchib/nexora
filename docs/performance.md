# Nexora Performance Engineering & Benchmark Experiment

## 1. Relational Database Indexing Strategy

To support high-throughput multi-tenant querying, compound indexes are placed on common access patterns:

1. `(organization_id, dataset_schema_id, created_at DESC)`: Powering the record explorer and timeline views.
2. `(organization_id, status, created_at DESC)`: Optimizing active job queues and filtering in the jobs dashboard.
3. `(organization_id, actor_id, created_at DESC)`: Accelerating audit log searches by security teams.
4. `(import_job_id, row_number)`: Enabling sub-millisecond retrieval of row-level errors for a specific job.

---

## 2. Ingestion Batching & N+1 Query Elimination

- **Bulk Inserts:** Instead of invoking `Model.save()` per record, rows are batched in groups of 500 using `bulk_create`.
- **Query Optimization:** API viewsets utilize `select_related('organization', 'dataset_schema', 'created_by')` and `prefetch_related('fields')` to eliminate N+1 queries.
- **Aggregations:** Ingestion metrics and dashboard statistics execute single-pass SQL aggregations (`Count`, `Sum`, `Avg`, `Q` filters) rather than loading rows into Python memory.

---

## 3. Reproducible Query Experiment

A dedicated performance test harness measures query execution times for tenant-scoped records before and after applying composite indexes. The benchmark is automated via management commands or scripts in `scripts/performance_bench.py`.
