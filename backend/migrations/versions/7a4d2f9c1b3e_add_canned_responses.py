"""add_canned_responses

Revision ID: 7a4d2f9c1b3e
Revises: 59812f788a67
Create Date: 2026-05-21 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a4d2f9c1b3e'
down_revision: Union[str, None] = '59812f788a67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'canned_responses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('sector_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('shortcut', sa.String(length=100), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['sector_id'], ['sectors.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id', 'shortcut'),
    )
    op.create_index(op.f('ix_canned_responses_workspace_id'), 'canned_responses', ['workspace_id'], unique=False)
    op.create_index('ix_canned_ws_active', 'canned_responses', ['workspace_id', 'active'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_canned_ws_active', table_name='canned_responses')
    op.drop_index(op.f('ix_canned_responses_workspace_id'), table_name='canned_responses')
    op.drop_table('canned_responses')