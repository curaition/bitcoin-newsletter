"""add_newsletter_progress_tracking

Revision ID: 4d07e8d47175
Revises: 003_add_batch_processing_tables
Create Date: 2025-08-22 00:41:05.398813

"""
from collections.abc import Sequence
from typing import Union

# revision identifiers, used by Alembic.
revision: str = "4d07e8d47175"
down_revision: Union[str, None] = "003_add_batch_processing_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    pass


def downgrade() -> None:
    """Downgrade database schema."""
    pass
