"""Fix newsletter generation_date to use timestamp instead of date.

Revision ID: fix_newsletter_generation_date_timestamp
Revises: add_newsletter_progress_tracking
Create Date: 2025-08-23 21:20:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "5e8f9a2b3c4d"
down_revision = "4d07e8d47175"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Change generation_date from DATE to TIMESTAMP WITH TIME ZONE."""
    # Add new column with timestamp type
    op.add_column(
        "newsletters",
        sa.Column("generation_date_new", sa.DateTime(timezone=True), nullable=True),
    )

    # Copy data from old column to new column, setting time to created_at time
    op.execute(
        """
        UPDATE newsletters
        SET generation_date_new = DATE_TRUNC('day', created_at) +
                                 (created_at - DATE_TRUNC('day', created_at))
        WHERE generation_date_new IS NULL
    """
    )

    # Make the new column non-nullable
    op.alter_column("newsletters", "generation_date_new", nullable=False)

    # Drop the old column
    op.drop_column("newsletters", "generation_date")

    # Rename the new column to the original name
    op.alter_column(
        "newsletters", "generation_date_new", new_column_name="generation_date"
    )


def downgrade() -> None:
    """Revert generation_date back to DATE type."""
    # Add new column with date type
    op.add_column(
        "newsletters", sa.Column("generation_date_old", sa.Date(), nullable=True)
    )

    # Copy data from timestamp column to date column
    op.execute(
        """
        UPDATE newsletters
        SET generation_date_old = DATE(generation_date)
        WHERE generation_date_old IS NULL
    """
    )

    # Make the new column non-nullable
    op.alter_column("newsletters", "generation_date_old", nullable=False)

    # Drop the timestamp column
    op.drop_column("newsletters", "generation_date")

    # Rename the date column back to original name
    op.alter_column(
        "newsletters", "generation_date_old", new_column_name="generation_date"
    )
