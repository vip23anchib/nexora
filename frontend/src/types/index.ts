export type TenantRole = 'org_admin' | 'operator' | 'analyst' | 'viewer';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_platform_admin: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  role?: TenantRole;
  membership_id?: string;
}

export interface OrganizationMembership {
  id: string;
  organization: string;
  organization_name?: string;
  user: User;
  role: TenantRole;
  is_active: boolean;
  created_at: string;
}

export type FieldType = 'string' | 'integer' | 'decimal' | 'boolean' | 'date' | 'datetime' | 'email';

export interface DatasetField {
  id?: string;
  field_name?: string;
  name?: string;
  field_type: FieldType;
  is_required: boolean;
  is_unique: boolean;
  position?: number;
  order?: number;
  validation_rules?: {
    min_length?: number;
    max_length?: number;
    min_value?: number;
    max_value?: number;
    regex?: string;
  };
}

export interface DatasetSchema {
  id: string;
  name: string;
  slug: string;
  description: string;
  version: number;
  status: 'draft' | 'active' | 'deprecated';
  is_active?: boolean;
  fields: DatasetField[];
  created_at: string;
  updated_at: string;
}

export interface DataSource {
  id: string;
  name: string;
  source_type: string;
  is_active: boolean;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export type JobStatus =
  | 'queued'
  | 'processing'
  | 'completed'
  | 'completed_with_errors'
  | 'failed'
  | 'cancelled'
  | 'QUEUED'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'COMPLETED_WITH_ERRORS'
  | 'FAILED'
  | 'CANCELLED';

export interface IngestionJob {
  id: string;
  organization: string;
  dataset_schema: string;
  schema?: string;
  schema_name?: string;
  schema_version?: number;
  data_source?: string;
  data_source_name?: string;
  created_by?: string;
  created_by_email?: string;
  file_name: string;
  file_size?: number;
  file_size_bytes?: number;
  checksum?: string;
  idempotency_key?: string;
  status: JobStatus;
  total_rows: number;
  processed_rows: number;
  successful_rows: number;
  failed_rows: number;
  error_rows?: number;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  error_summary?: string;
  created_at: string;
  updated_at?: string;
}

export interface ImportRowError {
  id: string;
  row_number: number;
  field_name: string;
  error_code: string;
  error_message: string;
  raw_value?: string;
  created_at?: string;
}

export interface ImportedRecord {
  id: string;
  external_id: string;
  dataset_schema?: string;
  schema?: string;
  schema_name?: string;
  source_job?: string;
  source_row_number?: number;
  payload: Record<string, any>;
  data?: Record<string, any>;
  record_hash: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  actor_email?: string;
  actor?: {
    email?: string;
    first_name?: string;
    last_name?: string;
  };
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, any>;
  ip_address: string;
  created_at: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  notification_type: 'info' | 'success' | 'warning' | 'error';
  is_read: boolean;
  created_at: string;
}

export interface DashboardMetrics {
  total_jobs: number;
  successful_jobs: number;
  failed_jobs: number;
  partial_jobs: number;
  processing_jobs: number;
  total_records: number;
  successful_records: number;
  failed_records: number;
  validation_failure_rate: number;
  avg_duration_seconds: number;
  active_schemas_count: number;
  recent_jobs: IngestionJob[];
  // Fallbacks / aliases
  success_rate_percent?: number;
  error_rows_count?: number;
}

export interface IngestionTrendItem {
  date: string;
  jobs_count: number;
  successful_records: number;
  failed_records: number;
  // Aliases for chart
  successful_rows?: number;
  error_rows?: number;
}
