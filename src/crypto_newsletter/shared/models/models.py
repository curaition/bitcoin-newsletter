"""Database models for the crypto newsletter system."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
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
