"""stage 3 — conversation timeline + reopen policy

Revision ID: 202605250001
Revises: 202605220004
Create Date: 2026-05-25
"""

from alembic import op

from app.models import Base


revision = "202605250001"
down_revision = "202605220004"
branch_labels = None
depends_on = None


NEW_EVENT_VALUES = (
    "message_inbound",
    "message_outbound",
    "new_protocol_created",
    "auto_resolved",
    "auto_reopened",
    "template_sent",
)


def upgrade() -> None:
    bind = op.get_bind()

    # Idempotent: relies on SQLAlchemy metadata for new tables. Anything that
    # already exists is skipped via checkfirst, so this is safe to re-run.
    Base.metadata.create_all(bind=bind, checkfirst=True)

    # Backfill new enum values into the existing conveventtype enum. ADD VALUE
    # IF NOT EXISTS is supported on Postgres >= 12 which is our baseline.
    for val in NEW_EVENT_VALUES:
        op.execute(f"ALTER TYPE conveventtype ADD VALUE IF NOT EXISTS '{val}'")

    # reopenmode enum is created automatically by create_all via the model
    # column type; for environments where Base.metadata didn't ship the enum
    # name yet, ensure it exists explicitly.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reopenmode') THEN
                CREATE TYPE reopenmode AS ENUM ('window', 'always_reopen', 'always_new');
            END IF;
        END$$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS conversation_policies")
    # Postgres does not support DROP VALUE on an enum; downgrade leaves the
    # extra event-type labels in place (harmless — no consumers if reverted).
