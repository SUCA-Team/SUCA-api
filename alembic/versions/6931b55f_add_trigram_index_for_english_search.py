"""add_trigram_index_for_english_search

Revision ID: 6931b55f
Revises: cad089e64ecc
Create Date: 2025-12-04 23:19:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6931b55f'
down_revision: Union[str, Sequence[str], None] = 'cad089e64ecc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add trigram extension and index for fast English text search."""
    # Enable pg_trgm extension for trigram indexing
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    
    # Create GIN trigram index on lowercased gloss text
    # This dramatically speeds up LIKE '%pattern%' queries on English glosses
    op.execute(
        'CREATE INDEX IF NOT EXISTS ix_gloss_text_trgm '
        'ON gloss USING gin (lower(text) gin_trgm_ops)'
    )


def downgrade() -> None:
    """Remove trigram index."""
    op.execute('DROP INDEX IF EXISTS ix_gloss_text_trgm')
    # Note: We don't drop the pg_trgm extension as other objects might depend on it
