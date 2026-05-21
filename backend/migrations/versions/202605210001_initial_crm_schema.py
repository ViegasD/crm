"""initial CRM schema

Revision ID: 202605210001
Revises:
Create Date: 2026-05-21
"""

from alembic import op

from app.models import Base


revision = "202605210001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, checkfirst=True)
