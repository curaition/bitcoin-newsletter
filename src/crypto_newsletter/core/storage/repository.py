"""Repository pattern implementation for data access operations."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import and_, desc, func, select, text, or_, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.shared.models import Article, ArticleCategory, Category, Publisher


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
    ) -> List[Article]:
        """
        Get recent articles from the database.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of articles to return
            include_categories: Whether to include category relationships

        Returns:
            List of recent Article instances
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        query = select(Article).where(
            and_(
                Article.published_on >= cutoff_time,
                Article.status == "ACTIVE"
            )
        ).order_by(desc(Article.published_on)).limit(limit)

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

    async def get_articles_by_publisher(
        self, publisher_id: int, limit: int = 50
    ) -> List[Article]:
        """Get articles by publisher ID."""
        query = (
            select(Article)
            .where(
                and_(
                    Article.publisher_id == publisher_id,
                    Article.status == "ACTIVE"
                )
            )
            .order_by(desc(Article.published_on))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_articles_by_category(
        self, category_name: str, limit: int = 50
    ) -> List[Article]:
        """Get articles by category name."""
        query = (
            select(Article)
            .join(ArticleCategory)
            .join(Category)
            .where(
                and_(
                    Category.name == category_name,
                    Article.status == "ACTIVE"
                )
            )
            .order_by(desc(Article.published_on))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_article_statistics(self) -> Dict[str, Any]:
        """Get comprehensive article statistics."""
        # Total articles
        total_query = select(func.count(Article.id)).where(Article.status == "ACTIVE")
        total_result = await self.db.execute(total_query)
        total_articles = total_result.scalar() or 0

        # Recent articles (last 24 hours)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_query = select(func.count(Article.id)).where(
            and_(
                Article.published_on >= cutoff_time,
                Article.status == "ACTIVE"
            )
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
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def get_recent_articles(
        self,
        limit: int = 10,
        offset: int = 0,
        publisher_id: Optional[int] = None,
        hours_back: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent articles with optional filtering."""
        try:
            query = select(Article).where(Article.status == "ACTIVE")

            # Apply filters
            if publisher_id:
                query = query.where(Article.publisher_id == publisher_id)

            if hours_back:
                cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
                query = query.where(Article.published_on >= cutoff)

            # Apply pagination and ordering
            query = query.order_by(Article.published_on.desc()).offset(offset).limit(limit)

            result = await self.db.execute(query)
            articles = result.scalars().all()

            return [
                {
                    "id": article.id,
                    "external_id": article.external_id,
                    "title": article.title,
                    "subtitle": article.subtitle,
                    "url": article.url,
                    "published_on": article.published_on.isoformat() if article.published_on else None,
                    "publisher_id": article.publisher_id,
                    "language": article.language,
                    "status": article.status,
                }
                for article in articles
            ]

        except Exception as e:
            logger.error(f"Failed to get recent articles: {e}")
            raise

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
    ) -> List[Dict[str, Any]]:
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
                cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
                filters.append(Article.published_on >= cutoff)

            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    filters.append(Article.published_on >= start_dt)
                except ValueError:
                    logger.warning(f"Invalid start_date format: {start_date}")

            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    filters.append(Article.published_on <= end_dt)
                except ValueError:
                    logger.warning(f"Invalid end_date format: {end_date}")

            # Search filter
            if search_query:
                search_filter = or_(
                    Article.title.ilike(f"%{search_query}%"),
                    Article.body.ilike(f"%{search_query}%"),
                    Article.subtitle.ilike(f"%{search_query}%")
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
                    "published_on": article.published_on.isoformat() if article.published_on else None,
                    "publisher_id": article.publisher_id,
                    "language": article.language,
                    "status": article.status,
                }
                for article in articles
            ]

        except Exception as e:
            logger.error(f"Failed to get articles with filters: {e}")
            raise

    async def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed article information by ID."""
        try:
            query = select(Article).where(
                Article.id == article_id,
                Article.status == "ACTIVE"
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
                "published_on": article.published_on.isoformat() if article.published_on else None,
                "publisher_id": article.publisher_id,
                "source_id": article.source_id,
                "status": article.status,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "updated_at": article.updated_at.isoformat() if article.updated_at else None,
            }

        except Exception as e:
            logger.error(f"Failed to get article by ID {article_id}: {e}")
            raise

    async def get_all_publishers_dict(self) -> List[Dict[str, Any]]:
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

    async def get_all_publishers(self, active_only: bool = True) -> List[Publisher]:
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
            and_(
                Article.publisher_id == publisher_id,
                Article.status == "ACTIVE"
            )
        )
        result = await self.db.execute(article_count_query)
        article_count = result.scalar() or 0

        # Update publisher with current stats
        publisher_query = select(Publisher).where(Publisher.id == publisher_id)
        publisher_result = await self.db.execute(publisher_query)
        publisher = publisher_result.scalar_one_or_none()

        if publisher:
            publisher.last_updated_ts = int(datetime.now(timezone.utc).timestamp())
            # Could add article_count field to Publisher model in future
            await self.db.commit()

        logger.debug(f"Updated stats for publisher {publisher_id}: {article_count} articles")


class CategoryRepository:
    """Repository for category-related database operations."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize repository with database session."""
        self.db = db_session

    async def get_all_categories(self) -> List[Category]:
        """Get all categories from database."""
        query = select(Category).order_by(Category.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by CoinDesk category ID."""
        query = select(Category).where(Category.category_id == category_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_category_statistics(self) -> List[Dict[str, Any]]:
        """Get statistics for all categories."""
        query = (
            select(
                Category.name,
                Category.category,
                func.count(Article.id).label("article_count")
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
async def get_recent_articles_with_stats(hours: int = 24) -> Dict[str, Any]:
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
                    "published_on": article.published_on.isoformat() if article.published_on else None,
                    "publisher_id": article.publisher_id,
                }
                for article in articles
            ],
            "statistics": stats,
        }


async def run_pipeline_with_monitoring() -> Dict[str, Any]:
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
