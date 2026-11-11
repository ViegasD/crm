"""stage 9 smart SLA, capacity and routing

Revision ID: 202605220001
Revises: 202605210001
Create Date: 2026-05-22
"""

from alembic import op


revision = "202605220001"
down_revision = "202605210001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing project migration uses Base.metadata.create_all, so this migration
    # is intentionally idempotent for both fresh and already-created databases.
    op.execute("ALTER TYPE userstatus ADD VALUE IF NOT EXISTS 'away'")
    op.execute("ALTER TYPE userstatus ADD VALUE IF NOT EXISTS 'in_call'")
    op.execute("ALTER TYPE userstatus ADD VALUE IF NOT EXISTS 'on_break'")
    op.execute("ALTER TYPE slaeventtype ADD VALUE IF NOT EXISTS 'next_response'")
    op.execute("ALTER TYPE slaeventtype ADD VALUE IF NOT EXISTS 'reopen_response'")
    op.execute("ALTER TYPE conveventtype ADD VALUE IF NOT EXISTS 'sla_at_risk'")
    op.execute("ALTER TYPE conveventtype ADD VALUE IF NOT EXISTS 'sla_violated'")
    op.execute("ALTER TYPE conveventtype ADD VALUE IF NOT EXISTS 'sla_escalated'")

    op.execute("ALTER TABLE agent_capacity ADD COLUMN IF NOT EXISTS max_weight DOUBLE PRECISION NOT NULL DEFAULT 10")
    op.execute("ALTER TABLE agent_capacity ADD COLUMN IF NOT EXISTS priority_weights JSONB NOT NULL DEFAULT '{}'::jsonb")

    op.execute("ALTER TABLE sla_policies ADD COLUMN IF NOT EXISTS channel_account_id UUID REFERENCES channel_accounts(id) ON DELETE CASCADE")
    op.execute("ALTER TABLE sla_policies ADD COLUMN IF NOT EXISTS priority VARCHAR(20)")
    op.execute("ALTER TABLE sla_policies ADD COLUMN IF NOT EXISTS next_response_minutes INTEGER")
    op.execute("ALTER TABLE sla_policies ADD COLUMN IF NOT EXISTS reopen_response_minutes INTEGER")
    op.execute("ALTER TABLE sla_policies ADD COLUMN IF NOT EXISTS business_hours_only BOOLEAN NOT NULL DEFAULT TRUE")
    op.execute("ALTER TABLE sla_policies ADD COLUMN IF NOT EXISTS pause_when_waiting_customer BOOLEAN NOT NULL DEFAULT TRUE")
    op.execute("ALTER TABLE sla_policies ADD COLUMN IF NOT EXISTS at_risk_threshold_pct INTEGER NOT NULL DEFAULT 80")
    op.execute("ALTER TABLE sla_policies ADD COLUMN IF NOT EXISTS steps JSONB NOT NULL DEFAULT '{}'::jsonb")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_sla_policy_scope "
        "ON sla_policies (workspace_id, sector_id, channel_account_id, priority)"
    )

    op.execute("ALTER TABLE sla_events ADD COLUMN IF NOT EXISTS status slastatus NOT NULL DEFAULT 'ok'")
    op.execute("ALTER TABLE sla_events ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_pause_reasons (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            label VARCHAR(120) NOT NULL,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            position INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (workspace_id, label)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_pause_reasons_workspace_id ON agent_pause_reasons (workspace_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_status (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status VARCHAR(32) NOT NULL DEFAULT 'offline',
            reason_id UUID REFERENCES agent_pause_reasons(id) ON DELETE SET NULL,
            note VARCHAR,
            since_at TIMESTAMPTZ NOT NULL,
            updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (workspace_id, user_id)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_status_workspace_id ON agent_status (workspace_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_status_ws_status ON agent_status (workspace_id, status)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_status_log (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status VARCHAR(32) NOT NULL,
            reason_id UUID REFERENCES agent_pause_reasons(id) ON DELETE SET NULL,
            note VARCHAR,
            changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
            changed_at TIMESTAMPTZ NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_status_log_workspace_id ON agent_status_log (workspace_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_agent_status_log_user_created "
        "ON agent_status_log (workspace_id, user_id, changed_at)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS business_hours (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            sector_id UUID REFERENCES sectors(id) ON DELETE CASCADE,
            weekday INTEGER NOT NULL,
            start_minute INTEGER NOT NULL,
            end_minute INTEGER NOT NULL,
            timezone VARCHAR(64) NOT NULL DEFAULT 'America/Sao_Paulo',
            active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_business_hours_workspace_id ON business_hours (workspace_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_business_hours_scope "
        "ON business_hours (workspace_id, sector_id, weekday)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS routing_rules (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            sector_id UUID REFERENCES sectors(id) ON DELETE CASCADE,
            strategy VARCHAR(32) NOT NULL DEFAULT 'least_busy',
            tiebreaker VARCHAR(32) NOT NULL DEFAULT 'oldest_idle',
            sticky_hours INTEGER NOT NULL DEFAULT 24,
            auto_reassign_minutes INTEGER NOT NULL DEFAULT 10,
            reopen_window_hours INTEGER NOT NULL DEFAULT 24,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (workspace_id, sector_id)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_routing_rules_workspace_id ON routing_rules (workspace_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_assignments (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            sector_id UUID REFERENCES sectors(id) ON DELETE SET NULL,
            assigned_by UUID REFERENCES users(id) ON DELETE SET NULL,
            assigned_at TIMESTAMPTZ NOT NULL,
            unassigned_at TIMESTAMPTZ,
            method VARCHAR(32) NOT NULL DEFAULT 'manual',
            reason VARCHAR
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_conversation_assignments_workspace_id ON conversation_assignments (workspace_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_assignment_conv_assigned "
        "ON conversation_assignments (conversation_id, assigned_at)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_assignment_user_active "
        "ON conversation_assignments (workspace_id, user_id, unassigned_at)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sla_escalation_chain (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            policy_id UUID NOT NULL REFERENCES sla_policies(id) ON DELETE CASCADE,
            threshold_pct INTEGER NOT NULL,
            action VARCHAR(32) NOT NULL,
            target_role VARCHAR(32),
            target_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            webhook_url VARCHAR,
            position INTEGER NOT NULL DEFAULT 0,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_sla_escalation_chain_workspace_id ON sla_escalation_chain (workspace_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_sla_escalation_policy "
        "ON sla_escalation_chain (policy_id, threshold_pct)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS auto_resolve_rules (
            id UUID PRIMARY KEY,
            workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
            sector_id UUID REFERENCES sectors(id) ON DELETE CASCADE,
            inactivity_hours INTEGER NOT NULL DEFAULT 72,
            status_from JSONB NOT NULL DEFAULT '[]'::jsonb,
            status_to VARCHAR(32) NOT NULL DEFAULT 'resolved',
            active BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (workspace_id, sector_id)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_auto_resolve_rules_workspace_id ON auto_resolve_rules (workspace_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS auto_resolve_rules")
    op.execute("DROP TABLE IF EXISTS sla_escalation_chain")
    op.execute("DROP TABLE IF EXISTS conversation_assignments")
    op.execute("DROP TABLE IF EXISTS routing_rules")
    op.execute("DROP TABLE IF EXISTS business_hours")
    op.execute("DROP TABLE IF EXISTS agent_status_log")
    op.execute("DROP TABLE IF EXISTS agent_status")
    op.execute("DROP TABLE IF EXISTS agent_pause_reasons")
