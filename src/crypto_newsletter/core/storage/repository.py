"""Repository pattern implementation for data access operations."""

from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.shared.models import (
    Article,
    ArticleCategory,
    Category,
    Newsletter,
    NewsletterArticle,
    Publisher,
)
from loguru import logger
from sqlalchemy import and_, asc, case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ArticleRepository:
    """Repository for article-related database operations."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.db = db_session

    async def get_recent_articles(
        self,
        hours: int = 24,
        limit: int = 100,
        include_categories: bool = True,
    ) -> list[Article]:
        """
        Get recent articles from the database.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of articles to return
            include_categories: Whether to include category relationships

        Returns:
            List of recent Article instances
        """
        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)

        query = (
            select(Article)
            .where(
                and_(Article.published_on >= cutoff_time, Article.status == "ACTIVE")
            )
            .order_by(desc(Article.published_on))
            .limit(limit)
        )

        if include_categories:
            query = query.options(
                selectinload(Article.article_categories).selectinload(
                    ArticleCategory.category
                )
            )

        result = await self.db.execute(query)
        articles = result.scalars().all()

        logger.debug(f"Retrieved {len(articles)} recent articles from database")
        return list(articles)

    async def get_article_by_external_id(self, external_id: int) -> Optional[Article]:
        """Get article by CoinDesk external ID."""
        query = select(Article).where(Article.external_id == external_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_article_by_url(self, url: str) -> Optional[Article]:
        """Get article by URL."""
        query = select(Article).where(Article.url == url)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_article_by_guid(self, guid: str) -> Optional[Article]:
        """Get article by GUID."""
        query = select(Article).where(Article.guid == guid)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_articles_by_publisher(
        self, publisher_id: int, limit: int = 50
    ) -> list[Article]:
        """Get articles by publisher ID."""
        query = (
            select(Article)
            .where(
                and_(Article.publisher_id == publisher_id, Article.status == "ACTIVE")
            )
            .order_by(desc(Article.published_on))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_articles_with_analysis_since(
        self, since_date: datetime, min_signal_strength: float = 0.0, limit: int = 100
    ) -> list[Article]:
        """
        Get articles with completed analysis since a specific date.

        Args:
            since_date: Get articles analyzed since this datetime
            min_signal_strength: Minimum signal strength filter
            limit: Maximum number of articles to return

        Returns:
            List of Article instances with analysis
        """
        from crypto_newsletter.shared.models import ArticleAnalysis

        query = (
            select(Article)
            .join(ArticleAnalysis, Article.id == ArticleAnalysis.article_id)
            .where(
                and_(
                    ArticleAnalysis.created_at >= since_date,
                    ArticleAnalysis.validation_status == "COMPLETED",
                    ArticleAnalysis.signal_strength >= min_signal_strength,
                    Article.status == "ACTIVE",
                )
            )
            .order_by(desc(ArticleAnalysis.created_at))
            .limit(limit)
        )

        result = await self.db.execute(query)
        articles = result.scalars().all()

        logger.debug(
            f"Retrieved {len(articles)} articles with analysis since {since_date}"
        )
        return list(articles)

    async def get_articles_by_category(
        self, category_name: str, limit: int = 50
    ) -> list[Article]:
        """Get articles by category name."""
        query = (
            select(Article)
            .join(ArticleCategory)
            .join(Category)
            .where(and_(Category.name == category_name, Article.status == "ACTIVE"))
            .order_by(desc(Article.published_on))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_article_statistics(self) -> dict[str, Any]:
        """Get comprehensive article statistics."""
        # Total articles
        total_query = select(func.count(Article.id)).where(Article.status == "ACTIVE")
        total_result = await self.db.execute(total_query)
        total_articles = total_result.scalar() or 0

        # Recent articles (last 24 hours)
        cutoff_time = datetime.now(UTC) - timedelta(hours=24)
        recent_query = select(func.count(Article.id)).where(
            and_(Article.published_on >= cutoff_time, Article.status == "ACTIVE")
        )
        recent_result = await self.db.execute(recent_query)
        recent_articles = recent_result.scalar() or 0

        # Articles by publisher
        publisher_query = (
            select(Publisher.name, func.count(Article.id).label("article_count"))
            .join(Article, Publisher.id == Article.publisher_id)
            .where(Article.status == "ACTIVE")
            .group_by(Publisher.name)
            .order_by(desc("article_count"))
            .limit(10)
        )
        publisher_result = await self.db.execute(publisher_query)
        top_publishers = [
            {"publisher": row.name, "count": row.article_count}
            for row in publisher_result.all()
        ]

        # Articles by category
        category_query = (
            select(Category.name, func.count(Article.id).label("article_count"))
            .join(ArticleCategory, Category.id == ArticleCategory.category_id)
            .join(Article, ArticleCategory.article_id == Article.id)
            .where(Article.status == "ACTIVE")
            .group_by(Category.name)
            .order_by(desc("article_count"))
            .limit(10)
        )
        category_result = await self.db.execute(category_query)
        top_categories = [
            {"category": row.name, "count": row.article_count}
            for row in category_result.all()
        ]

        return {
            "total_articles": total_articles,
            "recent_articles_24h": recent_articles,
            "top_publishers": top_publishers,
            "top_categories": top_categories,
            "last_updated": datetime.now(UTC).isoformat(),
        }

    async def get_articles_with_filters(
        self,
        limit: int = 10,
        offset: int = 0,
        publisher_id: Optional[int] = None,
        publisher_name: Optional[str] = None,
        hours_back: Optional[int] = None,
        search_query: Optional[str] = None,
        status: Optional[str] = "ACTIVE",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        order_by: Optional[str] = "published_on",
        order: Optional[str] = "desc",
    ) -> list[dict[str, Any]]:
        """Get articles with comprehensive filtering and search."""
        try:
            query = select(Article).join(Publisher, isouter=True)

            # Base filter
            filters = []
            if status:
                filters.append(Article.status == status)

            # Publisher filters
            if publisher_id:
                filters.append(Article.publisher_id == publisher_id)
            elif publisher_name:
                filters.append(Publisher.name.ilike(f"%{publisher_name}%"))

            # Date filters
            if hours_back:
                cutoff = datetime.now(UTC) - timedelta(hours=hours_back)
                filters.append(Article.published_on >= cutoff)

            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                    filters.append(Article.published_on >= start_dt)
                except ValueError:
                    logger.warning(f"Invalid start_date format: {start_date}")

            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    filters.append(Article.published_on <= end_dt)
                except ValueError:
                    logger.warning(f"Invalid end_date format: {end_date}")

            # Search filter
            if search_query:
                search_filter = or_(
                    Article.title.ilike(f"%{search_query}%"),
                    Article.body.ilike(f"%{search_query}%"),
                    Article.subtitle.ilike(f"%{search_query}%"),
                )
                filters.append(search_filter)

            # Apply all filters
            if filters:
                query = query.where(and_(*filters))

            # Ordering
            order_column = getattr(Article, order_by, Article.published_on)
            if order.lower() == "asc":
                query = query.order_by(asc(order_column))
            else:
                query = query.order_by(desc(order_column))

            # Pagination
            query = query.offset(offset).limit(limit)

            result = await self.db.execute(query)
            articles = result.scalars().all()

            return [
                {
                    "id": article.id,
                    "external_id": article.external_id,
                    "title": article.title,
                    "subtitle": article.subtitle,
                    "url": article.url,
                    "published_on": article.published_on.isoformat()
                    if article.published_on
                    else None,
                    "publisher_id": article.publisher_id,
                    "language": article.language,
                    "status": article.status,
                }
                for article in articles
            ]

        except Exception as e:
            logger.error(f"Failed to get articles with filters: {e}")
            raise

    async def get_analysis_ready_articles(
        self,
        limit: int = 10,
        offset: int = 0,
        publisher_id: Optional[int] = None,
        min_content_length: int = 2000,
    ) -> list[dict[str, Any]]:
        """
        Get articles that are ready for signal analysis.

        Args:
            limit: Maximum number of articles to return
            offset: Number of articles to skip for pagination
            publisher_id: Filter by specific publisher
            min_content_length: Minimum content length required

        Returns:
            List of analysis-ready articles
        """
        try:
            # Quality publishers prioritized for analysis
            quality_publishers = ["NewsBTC", "CoinDesk", "Crypto Potato"]

            query = (
                select(Article)
                .join(Publisher, isouter=True)
                .where(
                    and_(
                        Article.status == "ACTIVE",
                        func.length(Article.body) >= min_content_length,
                        Article.body.is_not(None),
                        Article.body != "",
                    )
                )
            )

            # Apply publisher filter
            if publisher_id:
                query = query.where(Article.publisher_id == publisher_id)
            else:
                # Prioritize quality publishers
                query = query.order_by(
                    case((Publisher.name.in_(quality_publishers), 1), else_=2),
                    desc(Article.published_on),
                )

            # Apply pagination
            query = query.offset(offset).limit(limit)

            result = await self.db.execute(query)
            articles = result.scalars().all()

            return [
                {
                    "id": article.id,
                    "external_id": article.external_id,
                    "title": article.title,
                    "subtitle": article.subtitle,
                    "url": article.url,
                    "published_on": article.published_on.isoformat()
                    if article.published_on
                    else None,
                    "publisher_id": article.publisher_id,
                    "language": article.language,
                    "status": article.status,
                    "content_length": len(article.body) if article.body else 0,
                    "analysis_ready": True,
                }
                for article in articles
            ]

        except Exception as e:
            logger.error(f"Failed to get analysis-ready articles: {e}")
            raise

    async def get_article_by_id(self, article_id: int) -> Optional[dict[str, Any]]:
        """Get detailed article information by ID."""
        try:
            query = select(Article).where(
                Article.id == article_id, Article.status == "ACTIVE"
            )
            result = await self.db.execute(query)
            article = result.scalar_one_or_none()

            if not article:
                return None

            return {
                "id": article.id,
                "external_id": article.external_id,
                "guid": article.guid,
                "title": article.title,
                "subtitle": article.subtitle,
                "authors": article.authors,
                "url": article.url,
                "body": article.body,
                "keywords": article.keywords,
                "language": article.language,
                "image_url": article.image_url,
                "published_on": article.published_on.isoformat()
                if article.published_on
                else None,
                "publisher_id": article.publisher_id,
                "source_id": article.source_id,
                "status": article.status,
                "created_at": article.created_at.isoformat()
                if article.created_at
                else None,
                "updated_at": article.updated_at.isoformat()
                if article.updated_at
                else None,
            }

        except Exception as e:
            logger.error(f"Failed to get article by ID {article_id}: {e}")
            raise

    async def get_all_publishers_dict(self) -> list[dict[str, Any]]:
        """Get all publishers as dictionaries for API responses."""
        try:
            query = select(Publisher).order_by(Publisher.name)
            result = await self.db.execute(query)
            publishers = result.scalars().all()

            return [
                {
                    "id": pub.id,
                    "source_id": pub.source_id,
                    "source_key": pub.source_key,
                    "name": pub.name,
                    "url": pub.url,
                    "lang": pub.lang,
                    "status": pub.status,
                }
                for pub in publishers
            ]

        except Exception as e:
            logger.error(f"Failed to get all publishers: {e}")
            raise


class PublisherRepository:
    """Repository for publisher-related database operations."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.db = db_session

    async def get_all_publishers(self, active_only: bool = True) -> list[Publisher]:
        """Get all publishers from database."""
        query = select(Publisher)
        if active_only:
            query = query.where(Publisher.status == "ACTIVE")

        query = query.order_by(Publisher.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_publisher_by_source_id(self, source_id: int) -> Optional[Publisher]:
        """Get publisher by CoinDesk source ID."""
        query = select(Publisher).where(Publisher.source_id == source_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_publisher_stats(self, publisher_id: int) -> None:
        """Update publisher statistics and metadata."""
        # Count articles for this publisher
        article_count_query = select(func.count(Article.id)).where(
            and_(Article.publisher_id == publisher_id, Article.status == "ACTIVE")
        )
        result = await self.db.execute(article_count_query)
        article_count = result.scalar() or 0

        # Update publisher with current stats
        publisher_query = select(Publisher).where(Publisher.id == publisher_id)
        publisher_result = await self.db.execute(publisher_query)
        publisher = publisher_result.scalar_one_or_none()

        if publisher:
            publisher.last_updated_ts = int(datetime.now(UTC).timestamp())
            # Could add article_count field to Publisher model in future
            await self.db.commit()

        logger.debug(
            f"Updated stats for publisher {publisher_id}: {article_count} articles"
        )


class CategoryRepository:
    """Repository for category-related database operations."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.db = db_session

    async def get_all_categories(self) -> list[Category]:
        """Get all categories from database."""
        query = select(Category).order_by(Category.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by CoinDesk category ID."""
        query = select(Category).where(Category.category_id == category_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_category_statistics(self) -> list[dict[str, Any]]:
        """Get statistics for all categories."""
        query = (
            select(
                Category.name,
                Category.category,
                func.count(Article.id).label("article_count"),
            )
            .join(ArticleCategory, Category.id == ArticleCategory.category_id)
            .join(Article, ArticleCategory.article_id == Article.id)
            .where(Article.status == "ACTIVE")
            .group_by(Category.id, Category.name, Category.category)
            .order_by(desc("article_count"))
        )

        result = await self.db.execute(query)
        return [
            {
                "name": row.name,
                "category": row.category,
                "article_count": row.article_count,
            }
            for row in result.all()
        ]


# Convenience functions for common operations
async def get_recent_articles_with_stats(hours: int = 24) -> dict[str, Any]:
    """Get recent articles with comprehensive statistics."""
    async with get_db_session() as db_session:
        article_repo = ArticleRepository(db_session)

        articles = await article_repo.get_recent_articles(hours=hours)
        stats = await article_repo.get_article_statistics()

        return {
            "articles": [
                {
                    "id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "published_on": article.published_on.isoformat()
                    if article.published_on
                    else None,
                    "publisher_id": article.publisher_id,
                }
                for article in articles
            ],
            "statistics": stats,
        }


async def run_pipeline_with_monitoring() -> dict[str, Any]:
    """Run pipeline with comprehensive monitoring and logging."""
    pipeline = ArticleIngestionPipeline()

    # Run health check first
    health = await pipeline.health_check()
    if health["status"] != "healthy":
        logger.warning(f"Pipeline health check failed: {health}")
        return {"status": "failed", "reason": "health_check_failed", "health": health}

    # Run ingestion
    try:
        results = await pipeline.run_full_ingestion()
        logger.info(f"Pipeline completed successfully: {results['summary']}")
        return results
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return {"status": "failed", "reason": str(e), "health": health}


class NewsletterRepository:
    """Repository for newsletter-related database operations."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.db = db_session

    async def get_all_newsletters(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        include_articles: bool = False,
    ) -> list[Newsletter]:
        """Get all newsletters with optional filtering."""
        query = (
            select(Newsletter).order_by(desc(Newsletter.generation_date)).limit(limit)
        )

        if status:
            query = query.where(Newsletter.status == status)

        if include_articles:
            query = query.options(
                selectinload(Newsletter.newsletter_articles).selectinload(
                    NewsletterArticle.article
                )
            )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_newsletter_by_id(
        self, newsletter_id: int, include_articles: bool = False
    ) -> Optional[Newsletter]:
        """Get newsletter by ID."""
        query = select(Newsletter).where(Newsletter.id == newsletter_id)

        if include_articles:
            query = query.options(
                selectinload(Newsletter.newsletter_articles).selectinload(
                    NewsletterArticle.article
                )
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_newsletters_by_status(
        self, status: str, limit: int = 20
    ) -> list[Newsletter]:
        """Get newsletters by status."""
        query = (
            select(Newsletter)
            .where(Newsletter.status == status)
            .order_by(desc(Newsletter.generation_date))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_published_newsletters(self, limit: int = 20) -> list[Newsletter]:
        """Get published newsletters."""
        return await self.get_newsletters_by_status("PUBLISHED", limit)

    async def get_draft_newsletters(self, limit: int = 20) -> list[Newsletter]:
        """Get draft newsletters."""
        return await self.get_newsletters_by_status("DRAFT", limit)

    async def get_newsletters_with_filters(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        newsletter_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[Newsletter]:
        """Get newsletters with comprehensive filtering."""
        from datetime import datetime

        query = select(Newsletter).order_by(desc(Newsletter.generation_date))

        # Apply filters
        if status:
            query = query.where(Newsletter.status == status)

        if newsletter_type:
            # Filter by newsletter type from generation_metadata
            query = query.where(
                Newsletter.generation_metadata.op("->")("newsletter_type").astext
                == newsletter_type
            )

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00")).date()
            query = query.where(Newsletter.generation_date >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00")).date()
            query = query.where(Newsletter.generation_date <= end_dt)

        # Apply pagination
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_newsletters_with_filters(
        self,
        status: Optional[str] = None,
        newsletter_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> int:
        """Count newsletters matching filters."""
        from datetime import datetime

        query = select(func.count(Newsletter.id))

        # Apply same filters as get_newsletters_with_filters
        if status:
            query = query.where(Newsletter.status == status)

        if newsletter_type:
            query = query.where(
                Newsletter.generation_metadata.op("->")("newsletter_type").astext
                == newsletter_type
            )

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00")).date()
            query = query.where(Newsletter.generation_date >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00")).date()
            query = query.where(Newsletter.generation_date <= end_dt)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def update_newsletter(
        self,
        newsletter_id: int,
        status: Optional[str] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Optional[Newsletter]:
        """Update newsletter fields."""
        # Get existing newsletter
        newsletter = await self.get_newsletter_by_id(newsletter_id)
        if not newsletter:
            return None

        # Update fields if provided
        if status is not None:
            newsletter.status = status
            if status == "PUBLISHED" and not newsletter.published_at:
                newsletter.published_at = datetime.now(UTC)

        if title is not None:
            newsletter.title = title

        if content is not None:
            newsletter.content = content

        if summary is not None:
            newsletter.summary = summary

        # Commit changes
        await self.db.commit()
        await self.db.refresh(newsletter)

        return newsletter

    async def delete_newsletter(self, newsletter_id: int) -> bool:
        """Delete newsletter by ID."""
        newsletter = await self.get_newsletter_by_id(newsletter_id)
        if not newsletter:
            return False

        await self.db.delete(newsletter)
        await self.db.commit()

        return True
