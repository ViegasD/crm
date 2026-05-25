"""backfill columns from current application models

Revision ID: 202605220003
Revises: 202605220002
Create Date: 2026-05-22
"""

from alembic import op

from app.models import Base


revision = "202605220003"
down_revision = "202605220002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'cannedvisibility') THEN
                CREATE TYPE cannedvisibility AS ENUM ('workspace', 'sector', 'user');
            END IF;
        END $$;
        """
    )

    op.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_private BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS service_reason_id UUID REFERENCES service_reasons(id) ON DELETE SET NULL")
    op.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS resolve_note VARCHAR")

    op.execute("ALTER TABLE labels ADD COLUMN IF NOT EXISTS category_id UUID REFERENCES label_categories(id) ON DELETE SET NULL")
    op.execute("ALTER TABLE labels ADD COLUMN IF NOT EXISTS description VARCHAR")

    op.execute("ALTER TABLE canned_responses ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE")
    op.execute("ALTER TABLE canned_responses ADD COLUMN IF NOT EXISTS category_id UUID REFERENCES canned_response_categories(id) ON DELETE SET NULL")
    op.execute("ALTER TABLE canned_responses ADD COLUMN IF NOT EXISTS visibility cannedvisibility NOT NULL DEFAULT 'workspace'")
    op.execute("ALTER TABLE canned_responses ADD COLUMN IF NOT EXISTS language VARCHAR(10)")
    op.execute("ALTER TABLE canned_responses ADD COLUMN IF NOT EXISTS attachments JSONB NOT NULL DEFAULT '[]'::jsonb")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_canned_shortcut_lookup "
        "ON canned_responses (workspace_id, shortcut)"
    )


def downgrade() -> None:
    pass
