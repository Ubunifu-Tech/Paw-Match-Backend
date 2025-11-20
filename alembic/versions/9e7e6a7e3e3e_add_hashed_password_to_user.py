
"""Add hashed_password to user

Revision ID: 9e7e6a7e3e3e
Revises: 8cd45bb1dde1
Create Date: 2025-11-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e7e6a7e3e3e'
down_revision: Union[str, Sequence[str], None] = '8cd45bb1dde1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('hashed_password', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'hashed_password')
