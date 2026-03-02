# initial migration - creates all tables
#
# revision: 001_initial
# create date: 2026-02-28

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # enable postgres extensions we need
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # enum types
    subscription_tier = postgresql.ENUM("trial", "starter", "professional", "enterprise", name="subscription_tier_enum", create_type=False)
    subscription_status = postgresql.ENUM("active", "past_due", "canceled", name="subscription_status_enum", create_type=False)
    membership_role = postgresql.ENUM("admin", "lawyer", "paralegal", name="membership_role_enum", create_type=False)
    matter_type = postgresql.ENUM("litigation", "corporate", "real_estate", "ip", "employment", "family", "criminal", "other", name="matter_type_enum", create_type=False)
    matter_status = postgresql.ENUM("active", "pending", "closed", "archived", name="matter_status_enum", create_type=False)
    assignment_role = postgresql.ENUM("lead", "contributor", "viewer", name="assignment_role_enum", create_type=False)
    processing_status = postgresql.ENUM("pending", "processing", "completed", "failed", name="processing_status_enum", create_type=False)
    extraction_type = postgresql.ENUM("parties", "deadlines", "obligations", "key_clauses", "risk_flags", "summary", name="extraction_type_enum", create_type=False)
    task_status = postgresql.ENUM("pending", "in_progress", "completed", "canceled", name="task_status_enum", create_type=False)
    task_priority = postgresql.ENUM("low", "medium", "high", "urgent", name="task_priority_enum", create_type=False)
    task_created_by = postgresql.ENUM("ai", "manual", name="task_created_by_enum", create_type=False)
    timeline_category = postgresql.ENUM("filing", "hearing", "deadline", "correspondence", "meeting", "custom", name="timeline_category_enum", create_type=False)
    timeline_source = postgresql.ENUM("ai_extracted", "manual", "system", name="timeline_source_enum", create_type=False)
    notification_type = postgresql.ENUM("deadline_alert", "document_processed", "task_assigned", "system", name="notification_type_enum", create_type=False)

    for enum in [subscription_tier, subscription_status, membership_role, matter_type, matter_status,
                 assignment_role, processing_status, extraction_type, task_status, task_priority,
                 task_created_by, timeline_category, timeline_source, notification_type]:
        enum.create(op.get_bind(), checkfirst=True)

    # organizations table
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("subscription_tier", subscription_tier, server_default="trial"),
        sa.Column("subscription_status", subscription_status, server_default="active"),
        sa.Column("max_users", sa.Integer, server_default="5"),
        sa.Column("max_storage_mb", sa.Integer, server_default="1024"),
        sa.Column("settings", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("is_superadmin", sa.Boolean, server_default="false"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # memberships table (links users to orgs)
    op.create_table(
        "memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("role", membership_role, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_membership_user_org"),
    )

    # matters table (cases/deals)
    op.create_table(
        "matters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("case_number", sa.String(100), nullable=True),
        sa.Column("client_name", sa.String(255), nullable=True),
        sa.Column("matter_type", matter_type, nullable=False),
        sa.Column("status", matter_status, server_default="active"),
        sa.Column("jurisdiction", sa.String(255), nullable=True),
        sa.Column("opposing_party", sa.String(255), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("opened_at", sa.Date, server_default=sa.text("CURRENT_DATE")),
        sa.Column("closed_at", sa.Date, nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_matters_org_status", "matters", ["organization_id", "status"])

    # matter assignments (who's working on what)
    op.create_table(
        "matter_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("matter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matters.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", assignment_role, server_default="contributor"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint("matter_id", "user_id", name="uq_matter_assignment"),
    )

    # documents table
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("matter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matters.id"), nullable=False),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger, nullable=True),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("processing_status", processing_status, server_default="pending"),
        sa.Column("processing_error", sa.Text, nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("raw_text", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_documents_org_matter", "documents", ["organization_id", "matter_id"])

    # document extractions (ai-extracted data from docs)
    op.create_table(
        "document_extractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("extraction_type", extraction_type, nullable=False),
        sa.Column("extracted_data", postgresql.JSONB, nullable=False),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_extractions_doc_type", "document_extractions", ["document_id", "extraction_type"])

    # tasks table
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("matter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matters.id"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", task_status, server_default="pending"),
        sa.Column("priority", task_priority, server_default="medium"),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_by", task_created_by, server_default="manual"),
        sa.Column("source_extraction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_extractions.id"), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_tasks_org_matter_status", "tasks", ["organization_id", "matter_id", "status"])
    op.create_index("ix_tasks_assignee_due", "tasks", ["assigned_to_id", "due_date"])

    # timeline events
    op.create_table(
        "timeline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("matter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("matters.id"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("event_date", sa.Date, nullable=False),
        sa.Column("category", timeline_category, server_default="custom"),
        sa.Column("source", timeline_source, server_default="manual"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_timeline_org_matter_date", "timeline_events", ["organization_id", "matter_id", "event_date"])

    # embeddings table (pgvector for semantic search)
    op.create_table(
        "embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.execute("ALTER TABLE embeddings ADD COLUMN embedding vector(1536) NOT NULL")
    op.execute("CREATE INDEX ix_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")

    # audit logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB, server_default="{}"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_audit_org_created", "audit_logs", ["organization_id", sa.text("created_at DESC")])
    op.create_index("ix_audit_resource", "audit_logs", ["organization_id", "resource_type", "resource_id"])

    # notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("notification_type", notification_type, nullable=False),
        sa.Column("is_read", sa.Boolean, server_default="false"),
        sa.Column("link", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "is_read", sa.text("created_at DESC")])


def downgrade() -> None:
    tables = [
        "notifications", "audit_logs", "embeddings", "timeline_events", "tasks",
        "document_extractions", "documents", "matter_assignments", "matters",
        "memberships", "users", "organizations",
    ]
    for table in tables:
        op.drop_table(table)

    enums = [
        "notification_type_enum", "timeline_source_enum", "timeline_category_enum",
        "task_created_by_enum", "task_priority_enum", "task_status_enum",
        "extraction_type_enum", "processing_status_enum", "assignment_role_enum",
        "matter_status_enum", "matter_type_enum", "membership_role_enum",
        "subscription_status_enum", "subscription_tier_enum",
    ]
    for enum in enums:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
