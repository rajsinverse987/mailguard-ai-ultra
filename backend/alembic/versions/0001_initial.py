"""Initial schema — users, accounts, emails, notifications, voice_notes, fraud_alerts, audit_logs, briefings."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True, index=True),
        sa.Column("whatsapp_number", sa.String(32), nullable=True),
        sa.Column("role", sa.String(32), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("preferred_language", sa.String(8), nullable=False, server_default="hi"),
        sa.Column("preferred_voice", sa.String(32), nullable=False, server_default="personal_assistant"),
        sa.Column("voice_gender", sa.String(8), nullable=False, server_default="female"),
        sa.Column("morning_briefing_time", sa.String(8), nullable=False, server_default="08:00"),
        sa.Column("enable_voice_alerts", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("enable_text_alerts", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "email_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("provider", sa.String(16), nullable=False),
        sa.Column("email_address", sa.String(255), nullable=False, index=True),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("access_token", sa.String(2048), nullable=True),
        sa.Column("refresh_token", sa.String(2048), nullable=True),
        sa.Column("token_expires_at", sa.String(64), nullable=True),
        sa.Column("scope", sa.String(1024), nullable=True),
        sa.Column("history_id", sa.String(64), nullable=True),
        sa.Column("watch_expiration", sa.String(64), nullable=True),
        sa.Column("subscription_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_sync_at", sa.String(64), nullable=True),
        sa.Column("extra", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "provider", "email_address", name="uq_account_user"),
    )
    op.create_index("ix_account_user_provider", "email_accounts", ["user_id", "provider"])

    op.create_table(
        "emails",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("email_accounts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("provider_message_id", sa.String(512), nullable=False, index=True),
        sa.Column("thread_id", sa.String(512), nullable=True, index=True),
        sa.Column("subject", sa.String(1024), nullable=False),
        sa.Column("sender_email", sa.String(255), nullable=False, index=True),
        sa.Column("sender_name", sa.String(255), nullable=True),
        sa.Column("sender_company", sa.String(255), nullable=True),
        sa.Column("to_recipients", postgresql.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("cc_recipients", postgresql.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("body_text", sa.Text, nullable=False, server_default=""),
        sa.Column("body_html", sa.Text, nullable=True),
        sa.Column("snippet", sa.String(512), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("category", sa.String(64), nullable=False, server_default="personal", index=True),
        sa.Column("priority", sa.String(16), nullable=False, server_default="medium", index=True),
        sa.Column("sentiment", sa.String(16), nullable=False, server_default="neutral"),
        sa.Column("intent", sa.String(128), nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("summary_hi", sa.Text, nullable=True),
        sa.Column("action_items", postgresql.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("due_dates", postgresql.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("meeting_requests", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("tracking_numbers", postgresql.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("invoice_amounts", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("otp_codes", postgresql.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("payment_requests", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("links", postgresql.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("attachments", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'")),
        sa.Column("labels", postgresql.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_phishing", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_spam", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("threat_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("threat_reason", sa.Text, nullable=True),
        sa.Column("processed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("notified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("raw", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_emails_user_received", "emails", ["user_id", "received_at"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("email_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("emails.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued"),
        sa.Column("provider", sa.String(16), nullable=False, server_default="meta"),
        sa.Column("to_number", sa.String(32), nullable=False),
        sa.Column("payload", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("provider_response", postgresql.JSONB, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("delivered", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_user_created", "notifications", ["user_id", "created_at"])

    op.create_table(
        "voice_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("email_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("emails.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("text", sa.String(4096), nullable=False),
        sa.Column("text_hi", sa.String(4096), nullable=True),
        sa.Column("language", sa.String(8), nullable=False, server_default="hi"),
        sa.Column("voice", sa.String(64), nullable=False, server_default="personal_assistant"),
        sa.Column("gender", sa.String(8), nullable=False, server_default="female"),
        sa.Column("engine", sa.String(16), nullable=False, server_default="openai"),
        sa.Column("audio_url", sa.String(1024), nullable=True),
        sa.Column("storage_key", sa.String(512), nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("size_bytes", sa.Integer, nullable=True),
        sa.Column("mime", sa.String(32), nullable=False, server_default="audio/mpeg"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "fraud_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("email_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("emails.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("threat_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("severity", sa.String(16), nullable=False, server_default="low"),
        sa.Column("is_phishing", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_scam", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("reasons", postgresql.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("suspicious_links", postgresql.ARRAY(sa.String), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("indicators", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("reasoning", sa.Text, nullable=True),
        sa.Column("acknowledged", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fraud_user_created", "fraud_alerts", ["user_id", "created_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("actor_role", sa.String(32), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource", sa.String(128), nullable=True),
        sa.Column("resource_id", sa.String(64), nullable=True),
        sa.Column("ip", postgresql.INET, nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="success"),
        sa.Column("meta", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_user_created", "audit_logs", ["user_id", "created_at"])
    op.create_index("ix_audit_action", "audit_logs", ["action"])

    op.create_table(
        "briefings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("period_start", sa.String(64), nullable=False),
        sa.Column("period_end", sa.String(64), nullable=False),
        sa.Column("language", sa.String(8), nullable=False, server_default="hi"),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("stats", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("voice_note_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("delivered", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("important_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("briefings")
    op.drop_index("ix_audit_action", table_name="audit_logs")
    op.drop_index("ix_audit_user_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_fraud_user_created", table_name="fraud_alerts")
    op.drop_table("fraud_alerts")
    op.drop_table("voice_notes")
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_emails_user_received", table_name="emails")
    op.drop_table("emails")
    op.drop_index("ix_account_user_provider", table_name="email_accounts")
    op.drop_table("email_accounts")
    op.drop_table("users")
