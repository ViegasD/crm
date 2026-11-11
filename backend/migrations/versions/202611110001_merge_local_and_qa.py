"""Merge the local media/sticker history and upstream Stage 3/4/9 history.

Preserve webhook payloads from either schema while making raw_payload the
shared storage for initial dispatch and operational retry.
"""
from alembic import op

revision = "202611110001"
down_revision = ("202605221215", "202605250001")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE webhook_events ADD COLUMN IF NOT EXISTS raw_payload JSONB")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'webhook_events' AND column_name = 'payload'
            ) THEN
                UPDATE webhook_events SET raw_payload = payload
                WHERE raw_payload IS NULL;
                -- Current writers persist only raw_payload. Keep the legacy
                -- column and historical values without requiring two payloads
                -- on every new insert.
                ALTER TABLE webhook_events ALTER COLUMN payload DROP NOT NULL;
            END IF;
        END $$;
        """
    )
    op.execute("UPDATE webhook_events SET raw_payload = '{}'::jsonb WHERE raw_payload IS NULL")
    op.execute("ALTER TABLE webhook_events ALTER COLUMN raw_payload SET NOT NULL")
    op.execute("ALTER TABLE webhook_events ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()")
    # Also cover environments where the upstream backfill was already applied.
    op.execute("ALTER TABLE webhook_events ADD COLUMN IF NOT EXISTS signature_hash VARCHAR(128)")
    op.execute("ALTER TABLE webhook_events ADD COLUMN IF NOT EXISTS headers JSONB NOT NULL DEFAULT '{}'::jsonb")
    with op.get_context().autocommit_block():
        for value in ("ignored", "dead_letter"):
            op.execute(f"ALTER TYPE webhookeventstatus ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # Keep stored payloads and audit metadata; this merge has no safe destructive
    # inverse because either parent may contain production webhook history.
    pass
