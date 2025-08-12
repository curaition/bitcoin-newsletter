"""Add AI agent tables for signal detection and newsletter generation

Revision ID: 002
Revises: 001
Create Date: 2025-08-12 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002_ai_agent_tables'
down_revision = '4bd8b0c6ebc1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable vector extension for embeddings (Neon PostgreSQL)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Signal Detection Tables
    op.create_table('signals',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('signal_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('implications', sa.Text(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('agent_version', sa.String(50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_signal_confidence')
    )
    
    # Signal Validation Results
    op.create_table('signal_validations',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('signal_id', sa.BigInteger(), nullable=False),
        sa.Column('validation_status', sa.String(20), nullable=False),
        sa.Column('evidence_summary', sa.Text(), nullable=True),
        sa.Column('research_sources', postgresql.JSONB(), nullable=True),
        sa.Column('validation_confidence', sa.Float(), nullable=False),
        sa.Column('research_cost_usd', sa.Float(), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('agent_version', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['signal_id'], ['signals.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("validation_status IN ('CONFIRMED', 'REJECTED', 'UNCERTAIN')", name='check_validation_status'),
        sa.CheckConstraint('validation_confidence >= 0 AND validation_confidence <= 1', name='check_validation_confidence')
    )
    
    # Newsletter Generation Tables
    op.create_table('newsletters',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('generation_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='DRAFT'),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('agent_version', sa.String(50), nullable=True),
        sa.Column('generation_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("status IN ('DRAFT', 'REVIEW', 'PUBLISHED', 'ARCHIVED')", name='check_newsletter_status'),
        sa.CheckConstraint('quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)', name='check_quality_score')
    )
    
    # Newsletter-Article Relationships
    op.create_table('newsletter_articles',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('newsletter_id', sa.BigInteger(), nullable=False),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('selection_reason', sa.Text(), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['newsletter_id'], ['newsletters.id'], ),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('newsletter_id', 'article_id', name='uq_newsletter_article')
    )
    
    # Article Embeddings for Semantic Search
    op.create_table('article_embeddings',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.BigInteger(), nullable=False),
        sa.Column('embedding', postgresql.ARRAY(sa.Float()), nullable=False),  # Will be converted to vector type
        sa.Column('embedding_model', sa.String(100), nullable=False),
        sa.Column('embedding_version', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('article_id', 'embedding_model', 'embedding_version', name='uq_article_embedding')
    )
    
    # Agent Execution Logs
    op.create_table('agent_executions',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('agent_type', sa.String(100), nullable=False),
        sa.Column('execution_id', sa.String(100), nullable=False),
        sa.Column('input_data', postgresql.JSONB(), nullable=True),
        sa.Column('output_data', postgresql.JSONB(), nullable=True),
        sa.Column('execution_status', sa.String(20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('agent_version', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("execution_status IN ('RUNNING', 'SUCCESS', 'FAILED', 'TIMEOUT')", name='check_execution_status')
    )
    
    # Create indexes for performance
    op.create_index('idx_signals_article_id', 'signals', ['article_id'])
    op.create_index('idx_signals_type_confidence', 'signals', ['signal_type', 'confidence'])
    op.create_index('idx_signals_detected_at', 'signals', ['detected_at'])
    
    op.create_index('idx_signal_validations_signal_id', 'signal_validations', ['signal_id'])
    op.create_index('idx_signal_validations_status', 'signal_validations', ['validation_status'])
    
    op.create_index('idx_newsletters_generation_date', 'newsletters', ['generation_date'])
    op.create_index('idx_newsletters_status', 'newsletters', ['status'])
    
    op.create_index('idx_newsletter_articles_newsletter_id', 'newsletter_articles', ['newsletter_id'])
    op.create_index('idx_newsletter_articles_article_id', 'newsletter_articles', ['article_id'])
    
    op.create_index('idx_article_embeddings_article_id', 'article_embeddings', ['article_id'])
    
    op.create_index('idx_agent_executions_type_status', 'agent_executions', ['agent_type', 'execution_status'])
    op.create_index('idx_agent_executions_started_at', 'agent_executions', ['started_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_agent_executions_started_at')
    op.drop_index('idx_agent_executions_type_status')
    op.drop_index('idx_article_embeddings_article_id')
    op.drop_index('idx_newsletter_articles_article_id')
    op.drop_index('idx_newsletter_articles_newsletter_id')
    op.drop_index('idx_newsletters_status')
    op.drop_index('idx_newsletters_generation_date')
    op.drop_index('idx_signal_validations_status')
    op.drop_index('idx_signal_validations_signal_id')
    op.drop_index('idx_signals_detected_at')
    op.drop_index('idx_signals_type_confidence')
    op.drop_index('idx_signals_article_id')
    
    # Drop tables
    op.drop_table('agent_executions')
    op.drop_table('article_embeddings')
    op.drop_table('newsletter_articles')
    op.drop_table('newsletters')
    op.drop_table('signal_validations')
    op.drop_table('signals')
    
    # Note: We don't drop the vector extension as it might be used by other applications
