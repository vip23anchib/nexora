# Nexora Ingestion Engine, Idempotency & Fault Tolerance

## 1. Pipeline Overview

The Ingestion Engine is the core data processing subsystem of Nexora. It transforms raw, untrusted CSV files into validated, structured records (`ImportedRecord`) while capturing fine-grained validation failures (`ImportRowError`) without aborting valid data.

```
       [ Upload CSV ]
             │
             ▼
   [ Stream Checksum & Size ]  ── (SHA-256 + Deduplication Check)
             │
             ▼
    [ Create ImportJob ]
    (Status: QUEUED)
             │
             ▼
  [ Celery Task / Worker ]
             │
      ┌──────┴──────┐
      │ Chunk Read  │ (Bounded Memory Generator)
      └──────┬──────┘
             │
    ┌────────▼────────┐
    │ Schema Validate │ (Type parsing, regex, constraints)
    └────────┬────────┘
             │
      ┌──────┴──────────────────────────┐
      │                                 │
 [Valid Rows]                    [Invalid Rows]
      │                                 │
 [Calculate Record Hash]          [Format ImportRowError]
      │                                 │
 [Bulk Upsert Records]            [Bulk Insert Errors]
      │                                 │
      └──────────────┬──────────────────┘
                     │
         [ Update Job Progress ]
                     │
         [ Emit Workflow Event ]
                     │
         [ Create Notification ]
```

---

## 2. Idempotency & Deduplication Strategy

1. **Job-Level Deduplication:**
   - Every file uploaded produces an SHA-256 digest calculated over the byte stream.
   - If an upload specifies an `idempotency_key` or matches a recent identical `checksum` within the organization, the system can return the existing job or reject the duplicate according to policy.
2. **Record-Level Deduplication:**
   - Each valid record computes a SHA-256 `record_hash` derived from sorted JSON keys of its payload.
   - If an `external_id` is defined on the schema, unique constraints ensure updates or skips rather than duplicate record creation.
3. **Safe Retries:**
   - When a job is retried (e.g. following worker crash or transient failure), already committed records are identified by their `(job_id, source_row_number)` or `record_hash`, preventing duplicate inserts.

---

## 3. Streaming & Memory Bounding

- Files are read using Python's `csv.reader` generator in chunks (default: 500 rows).
- Python objects are garbage-collected per chunk; large 100MB+ files consume minimal heap memory (O(chunk_size), not O(file_size)).
- Database inserts use Django's `bulk_create(batch_size=500)` with `ignore_conflicts=False` or custom conflict resolution.
