"""add sticker to message type enum

Revision ID: 202605221215
Revises: c1d8e6a4f2b0
Create Date: 2026-05-22 12:15:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "202605221215"
down_revision: Union[str, Sequence[str], None] = "c1d8e6a4f2b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE messagetype ADD VALUE IF NOT EXISTS 'sticker'")


def downgrade() -> None:
    # PostgreSQL enums do not support removing a value without recreating the type.
    pass