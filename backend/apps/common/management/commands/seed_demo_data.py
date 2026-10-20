from datetime import timedelta

from apps.audit.models import AuditEvent
from apps.datasources.models import DataSource
from apps.ingestion.models import ImportJob, ImportRowError
from apps.notifications.models import Notification
from apps.organizations.models import Organization, OrganizationMembership
from apps.records.models import ImportedRecord, compute_record_hash
from apps.schemas.models import DatasetField, DatasetSchema
from apps.workflows.models import WorkflowEvent
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Deterministic, rerunnable seed command for Nexora demo organizations and data."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Nexora deterministic demo data..."))

        # 1. Create Platform Admin
        platform_admin, _ = User.objects.get_or_create(
            email="platform.admin@nexora.io",
            defaults={
                "first_name": "Platform",
                "last_name": "Architect",
                "is_platform_admin": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        platform_admin.set_password("NexoraPlatform2026!")
        platform_admin.save()

        # 2. Organizations
        org_acme, _ = Organization.objects.get_or_create(
            slug="acme-logistics",
            defaults={
                "name": "Acme Logistics & Freight",
                "description": "Global freight forwarding and multimodal logistics carrier.",
                "timezone": "America/New_York",
            },
        )

        org_nova, _ = Organization.objects.get_or_create(
            slug="nova-biohealth",
            defaults={
                "name": "Nova BioHealth Labs",
                "description": "Clinical diagnostic pipelines and patient specimen tracking.",
                "timezone": "America/Los_Angeles",
            },
        )

        # 3. Users & Memberships for Acme Logistics
        acme_users = [
            # Primary Nexora personas
            ("admin@nexora.io", "Alex", "Vance", OrganizationMembership.Role.ORG_ADMIN),
            ("operator@nexora.io", "Oscar", "Perez", OrganizationMembership.Role.OPERATOR),
            ("analyst@nexora.io", "Anna", "Kim", OrganizationMembership.Role.ANALYST),
            ("viewer@nexora.io", "Victor", "Stone", OrganizationMembership.Role.VIEWER),
            # Alias Acme personas
            ("admin@acme.io", "Alice", "Vance", OrganizationMembership.Role.ORG_ADMIN),
            ("operator@acme.io", "Oscar", "Perez", OrganizationMembership.Role.OPERATOR),
            ("analyst@acme.io", "Anna", "Kim", OrganizationMembership.Role.ANALYST),
            ("viewer@acme.io", "Victor", "Stone", OrganizationMembership.Role.VIEWER),
        ]

        for email, first, last, role in acme_users:
            u, _ = User.objects.get_or_create(
                email=email,
                defaults={"first_name": first, "last_name": last},
            )
            u.set_password("NexoraSecurePass123!")
            u.save()
            OrganizationMembership.objects.update_or_create(
                organization=org_acme,
                user=u,
                defaults={"role": role, "is_active": True},
            )

        # 4. Users for Nova BioHealth
        nova_users = [
            ("admin@nova.io", "Dr. Nathan", "Drake", OrganizationMembership.Role.ORG_ADMIN),
            ("operator@nova.io", "Olivia", "Wilde", OrganizationMembership.Role.OPERATOR),
        ]
        for email, first, last, role in nova_users:
            u, _ = User.objects.get_or_create(
                email=email,
                defaults={"first_name": first, "last_name": last},
            )
            u.set_password("NexoraSecurePass123!")
            u.save()
            OrganizationMembership.objects.update_or_create(
                organization=org_nova,
                user=u,
                defaults={"role": role, "is_active": True},
            )

        acme_admin = User.objects.get(email="admin@acme.io")
        acme_operator = User.objects.get(email="operator@acme.io")

        # 5. Acme Schemas
        schema_shipments, _ = DatasetSchema.objects.get_or_create(
            organization=org_acme,
            slug="shipment-manifests",
            version=1,
            defaults={
                "name": "Shipment Manifests",
                "description": "International cargo manifests and shipment weight tracking.",
                "created_by": acme_admin,
                "status": DatasetSchema.Status.ACTIVE,
            },
        )

        shipment_fields = [
            ("tracking_number", "Tracking Number", "string", True, True, 1, {"min_length": 5}),
            ("origin_city", "Origin City", "string", True, False, 2, {}),
            ("dest_city", "Destination City", "string", True, False, 3, {}),
            ("weight_kg", "Weight (kg)", "decimal", True, False, 4, {"min_value": 0.1, "max_value": 5000.0}),
            ("is_hazmat", "Hazmat Cargo", "boolean", False, False, 5, {}),
            ("dispatch_date", "Dispatch Date", "date", True, False, 6, {}),
            ("shipper_email", "Shipper Email", "email", False, False, 7, {}),
        ]
        for fname, dname, ftype, req, uniq, pos, rules in shipment_fields:
            DatasetField.objects.update_or_create(
                dataset_schema=schema_shipments,
                field_name=fname,
                defaults={
                    "display_name": dname,
                    "field_type": ftype,
                    "is_required": req,
                    "is_unique": uniq,
                    "position": pos,
                    "validation_rules": rules,
                },
            )

        # 6. Data Source
        ds_s3, _ = DataSource.objects.get_or_create(
            organization=org_acme,
            name="Primary EDI Inbound SFTP",
            defaults={
                "source_type": DataSource.SourceType.SFTP,
                "description": "Automated warehouse scanner SFTP inbox.",
                "configuration": {"host": "sftp.acmelogistics.com", "port": 2222, "folder": "/manifests"},
                "created_by": acme_operator,
            },
        )

        # 7. Ingestion Jobs & Records
        now = timezone.now()

        # Job 1: Completed Cleanly
        job1, _ = ImportJob.objects.get_or_create(
            organization=org_acme,
            dataset_schema=schema_shipments,
            file_name="shipments_east_20261019.csv",
            defaults={
                "schema_version": 1,
                "data_source": ds_s3,
                "created_by": acme_operator,
                "file_size": 2048,
                "checksum": "3b299e525f05df4f84cfa88b630e6bc4882e379469e320f78d9101f6813b185b",
                "idempotency_key": "acme-manifest-20261019",
                "status": ImportJob.Status.COMPLETED,
                "total_rows": 5,
                "processed_rows": 5,
                "successful_rows": 5,
                "failed_rows": 0,
                "started_at": now - timedelta(hours=5),
                "completed_at": now - timedelta(hours=5, seconds=-12),
            },
        )

        records_data = [
            ("TRK-7701", "New York", "London", 320.5, False, "2026-10-18", "cargo@ny.com"),
            ("TRK-7702", "Chicago", "Frankfurt", 1250.0, False, "2026-10-18", "logistics@ord.com"),
            ("TRK-7703", "Miami", "Sao Paulo", 85.2, True, "2026-10-19", "ops@mia.com"),
            ("TRK-7704", "Atlanta", "Tokyo", 640.0, False, "2026-10-19", "dispatch@atl.com"),
            ("TRK-7705", "Boston", "Rotterdam", 412.8, False, "2026-10-19", "freight@bos.com"),
        ]

        for idx, (trk, orig, dest, wt, haz, ddate, semail) in enumerate(records_data, start=1):
            payload = {
                "tracking_number": trk,
                "origin_city": orig,
                "dest_city": dest,
                "weight_kg": wt,
                "is_hazmat": haz,
                "dispatch_date": ddate,
                "shipper_email": semail,
            }
            ImportedRecord.objects.get_or_create(
                organization=org_acme,
                dataset_schema=schema_shipments,
                source_job=job1,
                source_row_number=idx,
                external_id=trk,
                defaults={"payload": payload, "record_hash": compute_record_hash(payload)},
            )

        # Job 2: Completed with Errors
        job2, _ = ImportJob.objects.get_or_create(
            organization=org_acme,
            dataset_schema=schema_shipments,
            file_name="shipments_west_batch02.csv",
            defaults={
                "schema_version": 1,
                "data_source": ds_s3,
                "created_by": acme_operator,
                "file_size": 1540,
                "checksum": "8f8b871239c09d5e381676f4c9c1b489069d511ea636a0e6e9b422a16d80efaa",
                "status": ImportJob.Status.COMPLETED_WITH_ERRORS,
                "total_rows": 4,
                "processed_rows": 4,
                "successful_rows": 2,
                "failed_rows": 2,
                "started_at": now - timedelta(hours=2),
                "completed_at": now - timedelta(hours=2, seconds=-8),
                "error_summary": "Encountered 2 validation errors: weight exceeding maximum and invalid date format.",
            },
        )

        ImportRowError.objects.get_or_create(
            organization=org_acme,
            import_job=job2,
            row_number=2,
            defaults={
                "field_name": "weight_kg",
                "error_code": "NUMBER_TOO_LARGE",
                "error_message": "Value 99999.0 exceeds allowed maximum 5000.0.",
            },
        )
        ImportRowError.objects.get_or_create(
            organization=org_acme,
            import_job=job2,
            row_number=4,
            defaults={
                "field_name": "dispatch_date",
                "error_code": "INVALID_DATE",
                "error_message": "'not-a-date' is not a valid date format (expected YYYY-MM-DD).",
            },
        )

        # 8. Workflow Events
        WorkflowEvent.objects.get_or_create(
            organization=org_acme,
            import_job=job1,
            event_type="PROCESSING_COMPLETED",
            defaults={
                "previous_state": "processing",
                "new_state": "completed",
                "metadata": {"successful_rows": 5, "duration_seconds": 12},
            },
        )

        # 9. Audit Events
        AuditEvent.objects.get_or_create(
            organization=org_acme,
            action="SCHEMA_CREATED",
            resource_type="DatasetSchema",
            resource_id=str(schema_shipments.id),
            defaults={
                "actor": acme_admin,
                "request_id": "req-init-seed-001",
                "metadata": {"schema_name": "Shipment Manifests", "version": 1},
            },
        )

        # 10. Notifications
        Notification.objects.get_or_create(
            organization=org_acme,
            title="Import Job Completed Successfully",
            defaults={
                "user": acme_operator,
                "message": "File 'shipments_east_20261019.csv' was ingested with 5 valid records.",
                "notification_type": Notification.NotificationType.JOB_COMPLETED,
                "is_read": False,
                "link": f"/jobs/{job1.id}",
            },
        )
        Notification.objects.get_or_create(
            organization=org_acme,
            title="Ingestion Alert: Partial Success with Errors",
            defaults={
                "user": acme_operator,
                "message": "File 'shipments_west_batch02.csv' had 2 validation failures.",
                "notification_type": Notification.NotificationType.JOB_FAILED,
                "is_read": False,
                "link": f"/jobs/{job2.id}",
            },
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded deterministic demo data!"))
        self.stdout.write(
            "Demo Accounts:\n"
            "  - Acme Logistics Admin: admin@acme.io (Password: NexoraAdmin2026!)\n"
            "  - Acme Logistics Operator: operator@acme.io (Password: NexoraDemo2026!)\n"
            "  - Acme Logistics Analyst: analyst@acme.io (Password: NexoraDemo2026!)\n"
            "  - Acme Logistics Viewer: viewer@acme.io (Password: NexoraDemo2026!)\n"
            "  - Nova BioHealth Admin: admin@nova.io (Password: NexoraAdmin2026!)\n"
            "  - Platform Administrator: platform.admin@nexora.io (Password: NexoraPlatform2026!)\n"
        )
