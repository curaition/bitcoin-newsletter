# Newsletter Database Schema Enhancement
## Sub-PRD 3: Enhanced Newsletter Storage & Tracking System

### Executive Summary
Extend the existing newsletter database schema to support comprehensive newsletter generation, quality tracking, performance metrics, and multi-format publishing. This enhanced schema enables sophisticated newsletter management and analytics for both daily and weekly publications.

---

## 1. Product Overview

### Objective
Create a robust database schema that supports the complete newsletter lifecycle from generation through publishing, with comprehensive tracking of quality metrics, performance data, and reader engagement.

### Schema Extensions Required
- Enhanced newsletter content storage with synthesis fields
- Newsletter performance and engagement tracking
- Multi-format content support (HTML, text, PDF)
- Quality metrics and editorial scoring
- Weekly newsletter synthesis capabilities

---

## 2. Enhanced Newsletter Schema

### 2.1 Core Newsletter Table Enhancement
```sql
-- Enhanced newsletters table (extends existing)
ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS newsletter_type VARCHAR(20) DEFAULT 'DAILY' CHECK (newsletter_type IN ('DAILY', 'WEEKLY'));

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS publication_date DATE;

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS content_html TEXT;

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS content_text TEXT;

-- Story Selection Fields
ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS selected_articles INTEGER[];

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS selection_reasoning JSONB;

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS total_articles_reviewed INTEGER;

-- Synthesis Results
ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS synthesis_themes JSONB;

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS pattern_insights JSONB;

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS cross_story_connections JSONB;

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS signal_highlights JSONB;

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS adjacent_implications JSONB;

-- Quality Metrics
ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS editorial_quality_score DECIMAL(3,2);

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS signal_coherence_score DECIMAL(3,2);

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS uniqueness_score DECIMAL(3,2);

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS synthesis_confidence DECIMAL(3,2);

-- Performance Metrics
ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS generation_time_ms INTEGER;

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS token_usage INTEGER;

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS generation_cost_usd DECIMAL(6,4);

-- Publishing Data
ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS publish_status VARCHAR(20) DEFAULT 'DRAFT' CHECK (publish_status IN ('DRAFT', 'REVIEW', 'PUBLISHED', 'ARCHIVED'));

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS email_sent_at TIMESTAMPTZ;

ALTER TABLE newsletters
ADD COLUMN IF NOT EXISTS web_published_at TIMESTAMPTZ;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_newsletters_publication_date ON newsletters(publication_date);
CREATE INDEX IF NOT EXISTS idx_newsletters_type_status ON newsletters(newsletter_type, publish_status);
CREATE INDEX IF NOT EXISTS idx_newsletters_quality_score ON newsletters(editorial_quality_score);
```

### 2.2 Newsletter Performance Tracking
```sql
-- Newsletter engagement and performance metrics
CREATE TABLE IF NOT EXISTS newsletter_metrics (
    id BIGSERIAL PRIMARY KEY,
    newsletter_id BIGINT REFERENCES newsletters(id) NOT NULL,

    -- Email Distribution Metrics
    emails_sent INTEGER DEFAULT 0,
    emails_delivered INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_bounced INTEGER DEFAULT 0,
    emails_unsubscribed INTEGER DEFAULT 0,

    -- Engagement Metrics
    links_clicked INTEGER DEFAULT 0,
    unique_clicks INTEGER DEFAULT 0,
    click_through_rate DECIMAL(5,2),
    open_rate DECIMAL(5,2),

    -- Content Performance
    read_time_avg_seconds INTEGER,
    scroll_depth_avg DECIMAL(3,2),
    social_shares INTEGER DEFAULT 0,

    -- Reader Feedback
    feedback_ratings JSONB DEFAULT '[]',
    avg_rating DECIMAL(3,2),
    feedback_count INTEGER DEFAULT 0,

    -- Web Analytics
    web_views INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    time_on_page_avg_seconds INTEGER,

    -- Tracking Metadata
    measured_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(newsletter_id)
);

CREATE INDEX idx_newsletter_metrics_newsletter_id ON newsletter_metrics(newsletter_id);
CREATE INDEX idx_newsletter_metrics_measured_at ON newsletter_metrics(measured_at);
```

### 2.3 Newsletter Content Versions
```sql
-- Support for multiple content formats and versions
CREATE TABLE IF NOT EXISTS newsletter_content_versions (
    id BIGSERIAL PRIMARY KEY,
    newsletter_id BIGINT REFERENCES newsletters(id) NOT NULL,

    -- Content Format
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('HTML', 'TEXT', 'PDF', 'JSON')),
    content_data TEXT NOT NULL,

    -- Version Control
    version_number INTEGER NOT NULL DEFAULT 1,
    is_current BOOLEAN DEFAULT TRUE,

    -- Generation Metadata
    generated_by VARCHAR(50), -- Agent or system that generated this version
    generation_parameters JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(newsletter_id, content_type, version_number)
);

CREATE INDEX idx_newsletter_versions_newsletter_id ON newsletter_content_versions(newsletter_id);
CREATE INDEX idx_newsletter_versions_current ON newsletter_content_versions(newsletter_id, is_current) WHERE is_current = TRUE;
```

### 2.4 Weekly Newsletter Synthesis Tracking
```sql
-- Track weekly newsletter synthesis from daily newsletters
CREATE TABLE IF NOT EXISTS weekly_newsletter_synthesis (
    id BIGSERIAL PRIMARY KEY,
    weekly_newsletter_id BIGINT REFERENCES newsletters(id) NOT NULL,

    -- Source Daily Newsletters
    daily_newsletter_ids INTEGER[] NOT NULL,
    synthesis_period_start DATE NOT NULL,
    synthesis_period_end DATE NOT NULL,

    -- Synthesis Analysis
    weekly_themes JSONB,
    pattern_evolution JSONB,
    trend_analysis JSONB,
    strategic_insights JSONB,

    -- Quality Metrics
    synthesis_quality_score DECIMAL(3,2),
    daily_newsletters_included INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(weekly_newsletter_id)
);

CREATE INDEX idx_weekly_synthesis_newsletter_id ON weekly_newsletter_synthesis(weekly_newsletter_id);
CREATE INDEX idx_weekly_synthesis_period ON weekly_newsletter_synthesis(synthesis_period_start, synthesis_period_end);
```

---

## 3. Database Models (SQLAlchemy)

### 3.1 Enhanced Newsletter Model
```python
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, DECIMAL, ARRAY
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from crypto_newsletter.shared.models.base import Base

class Newsletter(Base):
    __tablename__ = 'newsletters'

    id = Column(Integer, primary_key=True)

    # Basic Information
    title = Column(String(200), nullable=False)
    newsletter_type = Column(String(20), default='DAILY', nullable=False)
    publication_date = Column(Date, nullable=False)

    # Content Storage
    content = Column(Text, nullable=False)  # Legacy field
    content_html = Column(Text)
    content_text = Column(Text)
    summary = Column(Text)

    # Story Selection Data
    selected_articles = Column(ARRAY(Integer))
    selection_reasoning = Column(JSONB)
    total_articles_reviewed = Column(Integer)

    # Synthesis Results
    synthesis_themes = Column(JSONB)
    pattern_insights = Column(JSONB)
    cross_story_connections = Column(JSONB)
    signal_highlights = Column(JSONB)
    adjacent_implications = Column(JSONB)

    # Quality Metrics
    editorial_quality_score = Column(DECIMAL(3,2))
    signal_coherence_score = Column(DECIMAL(3,2))
    uniqueness_score = Column(DECIMAL(3,2))
    synthesis_confidence = Column(DECIMAL(3,2))

    # Performance Metrics
    generation_time_ms = Column(Integer)
    token_usage = Column(Integer)
    generation_cost_usd = Column(DECIMAL(6,4))

    # Publishing Status
    publish_status = Column(String(20), default='DRAFT')
    published_at = Column(DateTime(timezone=True))
    email_sent_at = Column(DateTime(timezone=True))
    web_published_at = Column(DateTime(timezone=True))

    # Legacy Fields
    quality_score = Column(DECIMAL(3,2))  # Keep for backward compatibility
    agent_version = Column(String(50))
    generation_metadata = Column(JSONB)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    metrics = relationship("NewsletterMetrics", back_populates="newsletter", uselist=False)
    content_versions = relationship("NewsletterContentVersion", back_populates="newsletter")
    weekly_synthesis = relationship("WeeklyNewsletterSynthesis", back_populates="newsletter", uselist=False)

class NewsletterMetrics(Base):
    __tablename__ = 'newsletter_metrics'

    id = Column(Integer, primary_key=True)
    newsletter_id = Column(Integer, ForeignKey('newsletters.id'), nullable=False)

    # Email Metrics
    emails_sent = Column(Integer, default=0)
    emails_delivered = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_bounced = Column(Integer, default=0)
    emails_unsubscribed = Column(Integer, default=0)

    # Engagement Metrics
    links_clicked = Column(Integer, default=0)
    unique_clicks = Column(Integer, default=0)
    click_through_rate = Column(DECIMAL(5,2))
    open_rate = Column(DECIMAL(5,2))

    # Content Performance
    read_time_avg_seconds = Column(Integer)
    scroll_depth_avg = Column(DECIMAL(3,2))
    social_shares = Column(Integer, default=0)

    # Reader Feedback
    feedback_ratings = Column(JSONB, default=list)
    avg_rating = Column(DECIMAL(3,2))
    feedback_count = Column(Integer, default=0)

    # Web Analytics
    web_views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    time_on_page_avg_seconds = Column(Integer)

    # Timestamps
    measured_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    newsletter = relationship("Newsletter", back_populates="metrics")
```

---

## 4. Database Migration Scripts

### 4.1 Alembic Migration
```python
"""Enhanced newsletter schema

Revision ID: 003_enhanced_newsletter_schema
Revises: 002_add_ai_agent_tables
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003_enhanced_newsletter_schema'
down_revision = '002_add_ai_agent_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to newsletters table
    op.add_column('newsletters', sa.Column('newsletter_type', sa.String(20), server_default='DAILY'))
    op.add_column('newsletters', sa.Column('publication_date', sa.Date()))
    op.add_column('newsletters', sa.Column('content_html', sa.Text()))
    op.add_column('newsletters', sa.Column('content_text', sa.Text()))

    # Story selection fields
    op.add_column('newsletters', sa.Column('selected_articles', postgresql.ARRAY(sa.Integer())))
    op.add_column('newsletters', sa.Column('selection_reasoning', postgresql.JSONB()))
    op.add_column('newsletters', sa.Column('total_articles_reviewed', sa.Integer()))

    # Synthesis fields
    op.add_column('newsletters', sa.Column('synthesis_themes', postgresql.JSONB()))
    op.add_column('newsletters', sa.Column('pattern_insights', postgresql.JSONB()))
    op.add_column('newsletters', sa.Column('cross_story_connections', postgresql.JSONB()))
    op.add_column('newsletters', sa.Column('signal_highlights', postgresql.JSONB()))
    op.add_column('newsletters', sa.Column('adjacent_implications', postgresql.JSONB()))

    # Quality metrics
    op.add_column('newsletters', sa.Column('editorial_quality_score', sa.DECIMAL(3,2)))
    op.add_column('newsletters', sa.Column('signal_coherence_score', sa.DECIMAL(3,2)))
    op.add_column('newsletters', sa.Column('uniqueness_score', sa.DECIMAL(3,2)))
    op.add_column('newsletters', sa.Column('synthesis_confidence', sa.DECIMAL(3,2)))

    # Performance metrics
    op.add_column('newsletters', sa.Column('generation_time_ms', sa.Integer()))
    op.add_column('newsletters', sa.Column('token_usage', sa.Integer()))
    op.add_column('newsletters', sa.Column('generation_cost_usd', sa.DECIMAL(6,4)))

    # Publishing fields
    op.add_column('newsletters', sa.Column('publish_status', sa.String(20), server_default='DRAFT'))
    op.add_column('newsletters', sa.Column('email_sent_at', sa.DateTime(timezone=True)))
    op.add_column('newsletters', sa.Column('web_published_at', sa.DateTime(timezone=True)))

    # Create newsletter_metrics table
    op.create_table('newsletter_metrics',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('newsletter_id', sa.BigInteger(), nullable=False),
        sa.Column('emails_sent', sa.Integer(), server_default='0'),
        sa.Column('emails_delivered', sa.Integer(), server_default='0'),
        sa.Column('emails_opened', sa.Integer(), server_default='0'),
        sa.Column('emails_bounced', sa.Integer(), server_default='0'),
        sa.Column('emails_unsubscribed', sa.Integer(), server_default='0'),
        sa.Column('links_clicked', sa.Integer(), server_default='0'),
        sa.Column('unique_clicks', sa.Integer(), server_default='0'),
        sa.Column('click_through_rate', sa.DECIMAL(5,2)),
        sa.Column('open_rate', sa.DECIMAL(5,2)),
        sa.Column('read_time_avg_seconds', sa.Integer()),
        sa.Column('scroll_depth_avg', sa.DECIMAL(3,2)),
        sa.Column('social_shares', sa.Integer(), server_default='0'),
        sa.Column('feedback_ratings', postgresql.JSONB(), server_default='[]'),
        sa.Column('avg_rating', sa.DECIMAL(3,2)),
        sa.Column('feedback_count', sa.Integer(), server_default='0'),
        sa.Column('web_views', sa.Integer(), server_default='0'),
        sa.Column('unique_visitors', sa.Integer(), server_default='0'),
        sa.Column('time_on_page_avg_seconds', sa.Integer()),
        sa.Column('measured_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['newsletter_id'], ['newsletters.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('newsletter_id')
    )

    # Create indexes
    op.create_index('idx_newsletters_publication_date', 'newsletters', ['publication_date'])
    op.create_index('idx_newsletters_type_status', 'newsletters', ['newsletter_type', 'publish_status'])
    op.create_index('idx_newsletter_metrics_newsletter_id', 'newsletter_metrics', ['newsletter_id'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_newsletter_metrics_newsletter_id')
    op.drop_index('idx_newsletters_type_status')
    op.drop_index('idx_newsletters_publication_date')

    # Drop tables
    op.drop_table('newsletter_metrics')

    # Remove columns from newsletters table
    columns_to_remove = [
        'newsletter_type', 'publication_date', 'content_html', 'content_text',
        'selected_articles', 'selection_reasoning', 'total_articles_reviewed',
        'synthesis_themes', 'pattern_insights', 'cross_story_connections',
        'signal_highlights', 'adjacent_implications', 'editorial_quality_score',
        'signal_coherence_score', 'uniqueness_score', 'synthesis_confidence',
        'generation_time_ms', 'token_usage', 'generation_cost_usd',
        'publish_status', 'email_sent_at', 'web_published_at'
    ]

    for column in columns_to_remove:
        op.drop_column('newsletters', column)
```

---

## 5. Implementation Timeline

### Week 1: Schema Design & Migration
- **Days 1-2**: Finalize enhanced schema design
- **Days 3-4**: Create Alembic migration scripts
- **Days 5-7**: Test migrations and create SQLAlchemy models

### Week 2: Integration & Testing
- **Days 1-3**: Update existing code to use enhanced schema
- **Days 4-5**: Test newsletter storage and retrieval
- **Days 6-7**: Performance testing and optimization

---

## 6. Success Metrics

### Schema Performance
- **Query Performance**: <100ms for newsletter retrieval
- **Storage Efficiency**: Optimized JSONB storage for synthesis data
- **Index Effectiveness**: >95% index usage for common queries

### Data Integrity
- **Migration Success**: 100% data preservation during migration
- **Constraint Validation**: All data quality constraints enforced
- **Backup Recovery**: Full backup and recovery procedures tested

---

*Sub-PRD Version: 1.0*
*Implementation Priority: Phase 3 - Data Foundation*
*Dependencies: Newsletter agents system*
*Estimated Effort: 2 weeks*
