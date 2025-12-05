"""add fsrs fields to flashcards

Revision ID: 26bd700d10e2
Revises: 6931b55f
Create Date: 2025-01-15 12:42:58.447757

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26bd700d10e2'
down_revision: Union[str, Sequence[str], None] = '6931b55f'  # ← IMPORTANT: Change from 212a837af98d to 6931b55f
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add FSRS fields to flashcards table."""
    # Add FSRS fields to flashcards
    op.add_column('flashcards', sa.Column('difficulty', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('flashcards', sa.Column('stability', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('flashcards', sa.Column('elapsed_days', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('flashcards', sa.Column('scheduled_days', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('flashcards', sa.Column('reps', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('flashcards', sa.Column('lapses', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('flashcards', sa.Column('state', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('flashcards', sa.Column('last_review', sa.DateTime(), nullable=True))
    op.add_column('flashcards', sa.Column('due', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))


def downgrade() -> None:
    """Remove FSRS fields from flashcards table."""
    op.drop_column('flashcards', 'due')
    op.drop_column('flashcards', 'last_review')
    op.drop_column('flashcards', 'state')
    op.drop_column('flashcards', 'lapses')
    op.drop_column('flashcards', 'reps')
    op.drop_column('flashcards', 'scheduled_days')
    op.drop_column('flashcards', 'elapsed_days')
    op.drop_column('flashcards', 'stability')
    op.drop_column('flashcards', 'difficulty')