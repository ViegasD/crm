"""merge canned responses heads

Revision ID: c1d8e6a4f2b0
Revises: 202605210001, 7a4d2f9c1b3e
Create Date: 2026-05-21 23:55:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = 'c1d8e6a4f2b0'
down_revision: Union[str, Sequence[str], None] = ('202605210001', '7a4d2f9c1b3e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass