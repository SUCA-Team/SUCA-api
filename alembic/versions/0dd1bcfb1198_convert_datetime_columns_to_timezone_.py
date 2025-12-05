"""convert_datetime_columns_to_timezone_aware

Revision ID: 0dd1bcfb1198
Revises: 26bd700d10e2
Create Date: 2025-12-05 14:49:41.917488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0dd1bcfb1198'
down_revision: Union[str, Sequence[str], None] = '26bd700d10e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert datetime columns to timestamp with time zone."""
    # Convert flashcard_decks datetime columns
    op.execute("ALTER TABLE flashcard_decks ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE flashcard_decks ALTER COLUMN updated_at TYPE timestamp with time zone USING updated_at AT TIME ZONE 'UTC'")
    
    # Convert flashcards datetime columns
    op.execute("ALTER TABLE flashcards ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE flashcards ALTER COLUMN updated_at TYPE timestamp with time zone USING updated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE flashcards ALTER COLUMN last_review TYPE timestamp with time zone USING last_review AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE flashcards ALTER COLUMN due TYPE timestamp with time zone USING due AT TIME ZONE 'UTC'")
    
    # Update default for due column
    op.execute("ALTER TABLE flashcards ALTER COLUMN due SET DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC')")


def downgrade() -> None:
    """Convert datetime columns back to timestamp without time zone."""
    # Convert flashcard_decks datetime columns back
    op.execute("ALTER TABLE flashcard_decks ALTER COLUMN created_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE flashcard_decks ALTER COLUMN updated_at TYPE timestamp without time zone")
    
    # Convert flashcards datetime columns back
    op.execute("ALTER TABLE flashcards ALTER COLUMN created_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE flashcards ALTER COLUMN updated_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE flashcards ALTER COLUMN last_review TYPE timestamp without time zone")
    op.execute("ALTER TABLE flashcards ALTER COLUMN due TYPE timestamp without time zone")
    
    # Restore original default
    op.execute("ALTER TABLE flashcards ALTER COLUMN due SET DEFAULT CURRENT_TIMESTAMP")
