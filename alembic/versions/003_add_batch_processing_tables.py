"""Add batch processing tables

Revision ID: 003_add_batch_processing_tables
Revises: 002_ai_agent_tables
Create Date: 2025-08-19 01:20:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_add_batch_processing_tables"
down_revision: Union[str, None] = "002_ai_agent_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add batch processing tables."""
    # Create batch_processing_sessions table
    op.create_table(
        "batch_processing_sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "session_id",
            sa.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("total_articles", sa.Integer(), nullable=False),
        sa.Column("total_batches", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column(
            "actual_cost", sa.Numeric(precision=6, scale=4), nullable=True, default=0
        ),
        sa.Column("status", sa.String(length=20), nullable=False, default="INITIATED"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('INITIATED', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name="check_batch_session_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )

    # Create batch_processing_records table
    op.create_table(
        "batch_processing_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("batch_number", sa.Integer(), nullable=False),
        sa.Column("article_ids", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column(
            "actual_cost", sa.Numeric(precision=6, scale=4), nullable=True, default=0
        ),
        sa.Column("articles_processed", sa.Integer(), nullable=False, default=0),
        sa.Column("articles_failed", sa.Integer(), nullable=False, default=0),
        sa.Column("status", sa.String(length=20), nullable=False, default="PENDING"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')",
            name="check_batch_record_status",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["batch_processing_sessions.session_id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id", "batch_number", name="uq_session_batch_number"
        ),
    )

    # Create indexes for performance
    op.create_index(
        "idx_batch_sessions_status", "batch_processing_sessions", ["status"]
    )
    op.create_index(
        "idx_batch_sessions_started_at", "batch_processing_sessions", ["started_at"]
    )
    op.create_index(
        "idx_batch_records_session_id", "batch_processing_records", ["session_id"]
    )
    op.create_index("idx_batch_records_status", "batch_processing_records", ["status"])


def downgrade() -> None:
    """Remove batch processing tables."""
    # Drop indexes
    op.drop_index("idx_batch_records_status", table_name="batch_processing_records")
    op.drop_index("idx_batch_records_session_id", table_name="batch_processing_records")
    op.drop_index(
        "idx_batch_sessions_started_at", table_name="batch_processing_sessions"
    )
    op.drop_index("idx_batch_sessions_status", table_name="batch_processing_sessions")

    # Drop tables
    op.drop_table("batch_processing_records")
    op.drop_table("batch_processing_sessions")
