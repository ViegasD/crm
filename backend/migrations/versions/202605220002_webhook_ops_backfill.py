"""backfill webhook ops schema

Revision ID: 202605220002
Revises: 202605220001
Create Date: 2026-05-22
"""

from alembic import op


revision = "202605220002"
down_revision = "202605220001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'webhookeventstatus') THEN
                CREATE TYPE webhookeventstatus AS ENUM ('received', 'processing', 'processed', 'failed', 'ignored', 'dead_letter');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'circuitstate') THEN
                CREATE TYPE circuitstate AS ENUM ('closed', 'open', 'half_open');
            END IF;
        END $$;
        """
    )

    op.execute("ALTER TABLE channel_credentials ADD COLUMN IF NOT EXISTS previous_payload VARCHAR")
    op.execute("ALTER TABLE channel_credentials ADD COLUMN IF NOT EXISTS grace_until TIMESTAMPTZ")
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'channel_credentials'
                  AND column_name = 'rotated_at'
                  AND data_type = 'character varying'
            ) THEN
                ALTER TABLE channel_credentials ADD COLUMN IF NOT EXISTS rotated_at_tmp TIMESTAMPTZ;
                UPDATE channel_credentials
                SET rotated_at_tmp = NULLIF(rotated_at, '')::timestamptz
                WHERE rotated_at_tmp IS NULL
                  AND rotated_at IS NOT NULL
                  AND rotated_at <> '';
                ALTER TABLE channel_credentials DROP COLUMN rotated_at;
                ALTER TABLE channel_credentials RENAME COLUMN rotated_at_tmp TO rotated_at;
            ELSIF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'channel_credentials'
                  AND column_name = 'rotated_at'
            ) THEN
                ALTER TABLE channel_credentials ADD COLUMN rotated_at TIMESTAMPTZ;
            END IF;
        END $$;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS webhook_events (
            id UUID PRIMARY KEY,
            workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
            channel_account_id UUID REFERENCES channel_accounts(id) ON DELETE SET NULL,
            provider VARCHAR(50) NOT NULL,
            signature_hash VARCHAR(128),
            status webhookeventstatus NOT NULL DEFAULT 'received',
            headers JSONB NOT NULL DEFAULT '{}'::jsonb,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            error_message TEXT,
            attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 8,
            next_retry_at TIMESTAMPTZ,
            last_error_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            processed_at TIMESTAMPTZ
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_webhook_events_workspace_id ON webhook_events (workspace_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_webhook_events_created_at ON webhook_events (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_webhook_events_next_retry_at ON webhook_events (next_retry_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_webhook_status_created ON webhook_events (status, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_webhook_provider_signature ON webhook_events (provider, signature_hash)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS webhook_ip_allowlist (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            provider VARCHAR(50) NOT NULL,
            cidr VARCHAR(100) NOT NULL,
            description VARCHAR,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (workspace_id, provider, cidr)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_webhook_allow_lookup ON webhook_ip_allowlist (workspace_id, provider)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS channel_circuit_state (
            id UUID PRIMARY KEY,
            channel_account_id UUID NOT NULL UNIQUE REFERENCES channel_accounts(id) ON DELETE CASCADE,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            state circuitstate NOT NULL DEFAULT 'closed',
            failure_count INTEGER NOT NULL DEFAULT 0,
            last_failure_at TIMESTAMPTZ,
            opened_at TIMESTAMPTZ,
            next_probe_at TIMESTAMPTZ,
            last_error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS webhook_event_attempts (
            id UUID PRIMARY KEY,
            webhook_event_id UUID NOT NULL REFERENCES webhook_events(id) ON DELETE CASCADE,
            attempt INTEGER NOT NULL,
            payload_hash VARCHAR(128) NOT NULL,
            payload_snapshot JSONB NOT NULL,
            status VARCHAR(50) NOT NULL,
            error_message TEXT,
            latency_ms INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_webhook_attempt_event ON webhook_event_attempts (webhook_event_id, attempt)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS webhook_event_attempts")
    op.execute("DROP TABLE IF EXISTS channel_circuit_state")
    op.execute("DROP TABLE IF EXISTS webhook_ip_allowlist")
    op.execute("DROP TABLE IF EXISTS webhook_events")
