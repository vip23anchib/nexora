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
  name: string;
  field_type: FieldType;
  is_required: boolean;
  is_unique: boolean;
  validation_rules?: {
    min_length?: number;
    max_length?: number;
    min_value?: number;
    max_value?: number;
    regex?: string;
  };
  order: number;
}

export interface DatasetSchema {
  id: string;
  name: string;
  description: string;
  version: number;
  is_active: boolean;
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

export type JobStatus = 'QUEUED' | 'PROCESSING' | 'COMPLETED' | 'COMPLETED_WITH_ERRORS' | 'FAILED' | 'CANCELLED';

export interface IngestionJob {
  id: string;
  organization: string;
  schema: string;
  schema_name?: string;
  data_source?: string;
  data_source_name?: string;
  file_name: string;
  file_size_bytes: number;
  status: JobStatus;
  idempotency_key: string;
  total_rows: number;
  processed_rows: number;
  successful_rows: number;
  error_rows: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_summary?: string;
}

export interface ImportRowError {
  id: string;
  row_number: number;
  field_name: string;
  error_code: string;
  error_message: string;
  raw_value: string;
}

export interface ImportedRecord {
  id: string;
  external_id: string;
  schema: string;
  schema_name?: string;
  payload: Record<string, any>;
  record_hash: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  actor_email: string;
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
  total_records: number;
  total_jobs: number;
  success_rate_percent: number;
  error_rows_count: number;
  active_schemas_count: number;
  recent_jobs: IngestionJob[];
}

export interface IngestionTrendItem {
  date: string;
  total_jobs: number;
  successful_rows: number;
  error_rows: number;
}
