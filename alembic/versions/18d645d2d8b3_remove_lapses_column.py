"""remove_lapses_column

Revision ID: 18d645d2d8b3
Revises: 0dd1bcfb1198
Create Date: 2025-12-05 15:05:55.117047

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18d645d2d8b3'
down_revision: Union[str, Sequence[str], None] = '0dd1bcfb1198'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the lapses column from flashcards table."""
    op.drop_column('flashcards', 'lapses')


def downgrade() -> None:
    """Re-add the lapses column to flashcards table."""
    op.add_column('flashcards', sa.Column('lapses', sa.Integer(), nullable=False, server_default='0'))
    op.alter_column('flashcards', 'lapses', server_default=None)
