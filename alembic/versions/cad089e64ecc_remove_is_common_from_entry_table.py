"""remove_is_common_from_entry_table

Revision ID: cad089e64ecc
Revises: 212a837af98d
Create Date: 2025-12-04 21:52:27.984375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cad089e64ecc'
down_revision: Union[str, Sequence[str], None] = '212a837af98d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove is_common column from entry table."""
    # Drop the index first
    op.drop_index('ix_entry_is_common', table_name='entry')
    # Drop the column
    op.drop_column('entry', 'is_common')


def downgrade() -> None:
    """Restore is_common column to entry table."""
    # Add the column back
    op.add_column('entry', sa.Column('is_common', sa.Boolean(), nullable=True))
    # Create the index
    op.create_index('ix_entry_is_common', 'entry', ['is_common'])
