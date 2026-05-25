"""stage 9 extras runtime tables

Revision ID: 202605220004
Revises: 202605220003
Create Date: 2026-05-22
"""

from alembic import op

from app.models import Base


revision = "202605220004"
down_revision = "202605220003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)

    op.execute(
        """
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS sla_policy_override_id UUID
        REFERENCES sla_policies(id) ON DELETE SET NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_conversations_sla_policy_override
        ON conversations (sla_policy_override_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_conversations_sla_policy_override")
    op.execute("ALTER TABLE conversations DROP COLUMN IF EXISTS sla_policy_override_id")
    op.execute("DROP TABLE IF EXISTS csat_surveys")
    op.execute("DROP TABLE IF EXISTS api_webhook_deliveries")
    op.execute("DROP TABLE IF EXISTS api_webhook_subscriptions")
    op.execute("DROP TABLE IF EXISTS notification_deliveries")
    op.execute("DROP TABLE IF EXISTS notification_channels")
    op.execute("DROP TABLE IF EXISTS idle_rules")
    op.execute("DROP TABLE IF EXISTS conversation_locks")
    op.execute("DROP TABLE IF EXISTS business_holidays")
