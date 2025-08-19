"""Database models for the crypto newsletter system."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Publisher(Base, TimestampMixin):
    """Publisher/source model mapping to CoinDesk SOURCE_DATA."""

    __tablename__ = "publishers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    source_key: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lang: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    launch_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    benchmark_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, default="ACTIVE", nullable=True)
    last_updated_ts: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_on: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    updated_on: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    articles: Mapped[list["Article"]] = relationship(
        "Article", back_populates="publisher"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="check_publisher_status"
        ),
    )


class Category(Base, TimestampMixin):
    """Category model mapping to CoinDesk CATEGORY_DATA."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    article_categories: Mapped[list["ArticleCategory"]] = relationship(
        "ArticleCategory", back_populates="category"
    )


class Article(Base, TimestampMixin):
    """Article model mapping to CoinDesk article data."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    external_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    guid: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_on: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    published_on_ns: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    upvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    downvotes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sentiment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="ACTIVE", nullable=False)
    created_on: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    updated_on: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    publisher_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("publishers.id"), nullable=True
    )
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    publisher: Mapped[Optional["Publisher"]] = relationship(
        "Publisher", back_populates="articles"
    )
    article_categories: Mapped[list["ArticleCategory"]] = relationship(
        "ArticleCategory", back_populates="article"
    )

    __table_args__ = (
        CheckConstraint(
            "sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL')",
            name="check_article_sentiment",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'DELETED')", name="check_article_status"
        ),
    )


class ArticleCategory(Base):
    """Junction table for article-category relationships."""

    __tablename__ = "article_categories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    article_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("articles.id"), nullable=True
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("categories.id"), nullable=True
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )

    # Relationships
    article: Mapped["Article"] = relationship(
        "Article", back_populates="article_categories"
    )
    category: Mapped["Category"] = relationship(
        "Category", back_populates="article_categories"
    )

    __table_args__ = (
        UniqueConstraint("article_id", "category_id", name="uq_article_category"),
    )


class ArticleAnalysis(Base, TimestampMixin):
    """Analysis results for cryptocurrency articles."""

    __tablename__ = "article_analyses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("articles.id"), nullable=False
    )
    analysis_version: Mapped[Optional[str]] = mapped_column(
        String(10), default="1.0", nullable=True
    )

    # Core Analysis Fields
    sentiment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    impact_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Signal Detection Fields (JSONB Arrays)
    weak_signals: Mapped[Optional[dict]] = mapped_column(
        JSONB, default=lambda: [], nullable=True
    )
    pattern_anomalies: Mapped[Optional[dict]] = mapped_column(
        JSONB, default=lambda: [], nullable=True
    )
    adjacent_connections: Mapped[Optional[dict]] = mapped_column(
        JSONB, default=lambda: [], nullable=True
    )
    narrative_gaps: Mapped[Optional[dict]] = mapped_column(
        JSONB, default=lambda: [], nullable=True
    )
    edge_indicators: Mapped[Optional[dict]] = mapped_column(
        JSONB, default=lambda: [], nullable=True
    )

    # Validation Fields
    verified_facts: Mapped[Optional[dict]] = mapped_column(
        JSONB, default=lambda: [], nullable=True
    )
    research_sources: Mapped[Optional[dict]] = mapped_column(
        JSONB, default=lambda: [], nullable=True
    )
    validation_status: Mapped[Optional[str]] = mapped_column(
        Text, default="PENDING", nullable=True
    )

    # Quality Metrics
    analysis_confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    signal_strength: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), nullable=True
    )
    uniqueness_score: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), nullable=True
    )

    # Processing Metadata
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[Optional[float]] = mapped_column(Numeric(6, 4), nullable=True)

    # Relationships
    article: Mapped["Article"] = relationship("Article")

    __table_args__ = (
        CheckConstraint(
            "sentiment IN ('POSITIVE', 'NEGATIVE', 'NEUTRAL', 'MIXED')",
            name="check_analysis_sentiment",
        ),
        CheckConstraint(
            "impact_score >= 0 AND impact_score <= 1",
            name="check_analysis_impact_score",
        ),
        CheckConstraint(
            "analysis_confidence >= 0 AND analysis_confidence <= 1",
            name="check_analysis_confidence",
        ),
        CheckConstraint(
            "signal_strength >= 0 AND signal_strength <= 1",
            name="check_analysis_signal_strength",
        ),
        CheckConstraint(
            "uniqueness_score >= 0 AND uniqueness_score <= 1",
            name="check_analysis_uniqueness_score",
        ),
        CheckConstraint(
            "validation_status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED')",
            name="check_analysis_validation_status",
        ),
        UniqueConstraint(
            "article_id", "analysis_version", name="uq_article_analysis_version"
        ),
    )


class BatchProcessingSession(Base, TimestampMixin):
    """Batch processing session tracking."""

    __tablename__ = "batch_processing_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        unique=True,
        nullable=False,
        server_default=func.gen_random_uuid(),
    )
    total_articles: Mapped[int] = mapped_column(Integer, nullable=False)
    total_batches: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    actual_cost: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 4), default=0, nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="INITIATED", nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    batch_records: Mapped[list["BatchProcessingRecord"]] = relationship(
        "BatchProcessingRecord", back_populates="session"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('INITIATED', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name="check_batch_session_status",
        ),
    )


class BatchProcessingRecord(Base, TimestampMixin):
    """Individual batch processing record."""

    __tablename__ = "batch_processing_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("batch_processing_sessions.session_id"),
        nullable=False,
    )
    batch_number: Mapped[int] = mapped_column(Integer, nullable=False)
    article_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    estimated_cost: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    actual_cost: Mapped[Optional[float]] = mapped_column(
        Numeric(6, 4), default=0, nullable=True
    )
    articles_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    articles_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    session: Mapped["BatchProcessingSession"] = relationship(
        "BatchProcessingSession", back_populates="batch_records"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')",
            name="check_batch_record_status",
        ),
        UniqueConstraint("session_id", "batch_number", name="uq_session_batch_number"),
    )
