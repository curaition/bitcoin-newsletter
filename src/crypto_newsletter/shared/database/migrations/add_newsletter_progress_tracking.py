"""Add newsletter generation progress tracking table.

Revision ID: add_newsletter_progress_tracking
Revises:
Create Date: 2024-12-19 12:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_newsletter_progress_tracking"
down_revision = "44078050e10e"  # Initial database schema
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add newsletter generation progress tracking table."""
    op.create_table(
        "newsletter_generation_progress",
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("current_step", sa.String(), nullable=False),
        sa.Column("step_progress", sa.Float(), nullable=True, default=0.0),
        sa.Column("overall_progress", sa.Float(), nullable=True, default=0.0),
        sa.Column(
            "step_details", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "intermediate_results",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "quality_metrics", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "articles_being_processed",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("estimated_completion", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, default=sa.func.now()),
        sa.Column("status", sa.String(), nullable=True, default="in_progress"),
        sa.PrimaryKeyConstraint("task_id"),
    )

    # Create index on status for efficient querying
    op.create_index(
        "ix_newsletter_generation_progress_status",
        "newsletter_generation_progress",
        ["status"],
    )

    # Create index on created_at for cleanup queries
    op.create_index(
        "ix_newsletter_generation_progress_created_at",
        "newsletter_generation_progress",
        ["created_at"],
    )


def downgrade() -> None:
    """Remove newsletter generation progress tracking table."""
    op.drop_index("ix_newsletter_generation_progress_created_at")
    op.drop_index("ix_newsletter_generation_progress_status")
    op.drop_table("newsletter_generation_progress")
