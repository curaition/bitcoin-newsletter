"""Batch article identification system for newsletter processing."""

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BatchArticleIdentifier:
    """Identifies articles suitable for batch processing."""

    def __init__(self, min_content_length: int = 1000):
        self.min_content_length = min_content_length

    async def get_analyzable_articles(
        self, db: AsyncSession, limit: int = 200
    ) -> list[int]:
        """
        Get article IDs for batch processing.

        Returns articles that:
        - Have not been analyzed yet
        - Have substantial content (>1000 characters)
        - Are not empty or null

        Args:
            db: Database session
            limit: Maximum number of articles to return

        Returns:
            List of article IDs suitable for batch processing
        """
        try:
            query = text(
                """
                SELECT a.id
                FROM articles a
                LEFT JOIN article_analyses aa ON a.id = aa.article_id
                WHERE aa.id IS NULL  -- Not yet analyzed
                  AND LENGTH(a.body) > :min_length  -- Substantial content
                  AND a.body IS NOT NULL
                  AND a.body != ''
                  AND a.status = 'ACTIVE'  -- Only active articles
                ORDER BY a.published_on DESC
                LIMIT :limit
            """
            )

            result = await db.execute(
                query, {"min_length": self.min_content_length, "limit": limit}
            )

            article_ids = [row[0] for row in result.fetchall()]

            logger.info(
                f"Found {len(article_ids)} analyzable articles "
                f"(min_length: {self.min_content_length}, limit: {limit})"
            )

            return article_ids

        except Exception as e:
            logger.error(f"Failed to get analyzable articles: {e}")
            raise

    async def get_article_details(
        self, db: AsyncSession, article_ids: list[int]
    ) -> list[dict[str, Any]]:
        """
        Get detailed information about articles for batch processing.

        Args:
            db: Database session
            article_ids: List of article IDs to get details for

        Returns:
            List of article details with metadata
        """
        if not article_ids:
            return []

        try:
            # Use IN clause instead of ANY for better compatibility
            ids_placeholder = ",".join([f":id_{i}" for i in range(len(article_ids))])
            params = {f"id_{i}": article_id for i, article_id in enumerate(article_ids)}

            query = text(
                f"""
                SELECT
                    a.id,
                    a.title,
                    a.url,
                    a.published_on,
                    a.body,
                    LENGTH(a.body) as content_length,
                    p.name as publisher_name,
                    p.id as publisher_id
                FROM articles a
                JOIN publishers p ON a.publisher_id = p.id
                WHERE a.id IN ({ids_placeholder})
                ORDER BY a.published_on DESC
            """
            )

            result = await db.execute(query, params)
            rows = result.fetchall()

            articles = []
            for row in rows:
                articles.append(
                    {
                        "id": row.id,
                        "title": row.title,
                        "url": row.url,
                        "published_on": row.published_on.isoformat()
                        if row.published_on
                        else None,
                        "content_length": row.content_length,
                        "publisher_name": row.publisher_name,
                        "publisher_id": row.publisher_id,
                        "body_preview": row.body[:200] + "..."
                        if len(row.body) > 200
                        else row.body,
                    }
                )

            logger.info(f"Retrieved details for {len(articles)} articles")
            return articles

        except Exception as e:
            logger.error(f"Failed to get article details: {e}")
            raise

    async def validate_articles_for_processing(
        self, db: AsyncSession, article_ids: list[int]
    ) -> dict[str, Any]:
        """
        Validate that articles are suitable for batch processing.

        Args:
            db: Database session
            article_ids: List of article IDs to validate

        Returns:
            Validation results with statistics
        """
        if not article_ids:
            return {
                "valid_articles": [],
                "invalid_articles": [],
                "validation_summary": {
                    "total_articles": 0,
                    "valid_count": 0,
                    "invalid_count": 0,
                    "validation_passed": False,
                },
            }

        try:
            # Get article details
            articles = await self.get_article_details(db, article_ids)

            valid_articles = []
            invalid_articles = []

            for article in articles:
                # Validation criteria
                is_valid = True
                validation_issues = []

                # Check content length
                if article["content_length"] < self.min_content_length:
                    is_valid = False
                    validation_issues.append(
                        f"Content too short: {article['content_length']} chars"
                    )

                # Check if already analyzed (double-check)
                already_analyzed = await self._check_if_analyzed(db, article["id"])
                if already_analyzed:
                    is_valid = False
                    validation_issues.append("Already analyzed")

                if is_valid:
                    valid_articles.append(article)
                else:
                    article["validation_issues"] = validation_issues
                    invalid_articles.append(article)

            validation_summary = {
                "total_articles": len(articles),
                "valid_count": len(valid_articles),
                "invalid_count": len(invalid_articles),
                "validation_passed": len(valid_articles)
                >= 3,  # Minimum 3 articles needed
                "min_articles_required": 3,
            }

            logger.info(
                f"Validation complete: {validation_summary['valid_count']}/{validation_summary['total_articles']} articles valid"
            )

            return {
                "valid_articles": valid_articles,
                "invalid_articles": invalid_articles,
                "validation_summary": validation_summary,
            }

        except Exception as e:
            logger.error(f"Failed to validate articles: {e}")
            raise

    async def _check_if_analyzed(self, db: AsyncSession, article_id: int) -> bool:
        """Check if an article has already been analyzed."""
        try:
            query = text(
                "SELECT 1 FROM article_analyses WHERE article_id = :article_id LIMIT 1"
            )
            result = await db.execute(query, {"article_id": article_id})
            return result.fetchone() is not None
        except Exception:
            return False

    # Synchronous versions for Celery tasks
    def get_analyzable_articles_sync(self, db: Session, limit: int = 200) -> list[int]:
        """
        Get article IDs for batch processing (synchronous version).

        Returns articles that:
        - Have not been analyzed yet
        - Have substantial content (>1000 characters)
        - Are not empty or null

        Args:
            db: Database session
            limit: Maximum number of articles to return

        Returns:
            List of article IDs suitable for batch processing
        """
        try:
            query = text(
                """
                SELECT a.id
                FROM articles a
                LEFT JOIN article_analyses aa ON a.id = aa.article_id
                WHERE aa.id IS NULL  -- Not yet analyzed
                  AND LENGTH(a.body) > :min_length  -- Substantial content
                  AND a.body IS NOT NULL
                  AND a.body != ''
                  AND a.status = 'ACTIVE'  -- Only active articles
                ORDER BY a.published_on DESC
                LIMIT :limit
            """
            )

            result = db.execute(
                query, {"min_length": self.min_content_length, "limit": limit}
            )

            article_ids = [row[0] for row in result.fetchall()]

            logger.info(
                f"Found {len(article_ids)} analyzable articles "
                f"(min_length: {self.min_content_length}, limit: {limit})"
            )

            return article_ids

        except Exception as e:
            logger.error(f"Failed to get analyzable articles: {e}")
            raise

    def get_article_details_sync(
        self, db: Session, article_ids: list[int]
    ) -> list[dict[str, Any]]:
        """
        Get detailed information about articles for batch processing (synchronous version).

        Args:
            db: Database session
            article_ids: List of article IDs to get details for

        Returns:
            List of article details with metadata
        """
        if not article_ids:
            return []

        try:
            # Use IN clause instead of ANY for better compatibility
            ids_placeholder = ",".join([f":id_{i}" for i in range(len(article_ids))])
            params = {f"id_{i}": article_id for i, article_id in enumerate(article_ids)}

            query = text(
                f"""
                SELECT
                    a.id,
                    a.title,
                    a.url,
                    a.published_on,
                    a.body,
                    LENGTH(a.body) as content_length,
                    p.name as publisher_name,
                    p.id as publisher_id
                FROM articles a
                JOIN publishers p ON a.publisher_id = p.id
                WHERE a.id IN ({ids_placeholder})
                ORDER BY a.published_on DESC
            """
            )

            result = db.execute(query, params)
            rows = result.fetchall()

            articles = []
            for row in rows:
                articles.append(
                    {
                        "id": row.id,
                        "title": row.title,
                        "url": row.url,
                        "published_on": row.published_on.isoformat()
                        if row.published_on
                        else None,
                        "content_length": row.content_length,
                        "publisher_name": row.publisher_name,
                        "publisher_id": row.publisher_id,
                        "body_preview": row.body[:200] + "..."
                        if len(row.body) > 200
                        else row.body,
                    }
                )

            logger.info(f"Retrieved details for {len(articles)} articles")
            return articles

        except Exception as e:
            logger.error(f"Failed to get article details: {e}")
            raise

    def validate_articles_for_processing_sync(
        self, db: Session, article_ids: list[int]
    ) -> dict[str, Any]:
        """
        Validate that articles are suitable for batch processing (synchronous version).

        Args:
            db: Database session
            article_ids: List of article IDs to validate

        Returns:
            Validation results with statistics
        """
        if not article_ids:
            return {
                "valid_articles": [],
                "invalid_articles": [],
                "validation_summary": {
                    "total_articles": 0,
                    "valid_count": 0,
                    "invalid_count": 0,
                    "validation_passed": False,
                },
            }

        try:
            # Get article details
            articles = self.get_article_details_sync(db, article_ids)

            valid_articles = []
            invalid_articles = []

            for article in articles:
                # Validation criteria
                is_valid = True
                validation_issues = []

                # Check content length
                if article["content_length"] < self.min_content_length:
                    is_valid = False
                    validation_issues.append(
                        f"Content too short: {article['content_length']} chars"
                    )

                # Check if already analyzed (double-check)
                already_analyzed = self._check_if_analyzed_sync(db, article["id"])
                if already_analyzed:
                    is_valid = False
                    validation_issues.append("Already analyzed")

                if is_valid:
                    valid_articles.append(article)
                else:
                    article["validation_issues"] = validation_issues
                    invalid_articles.append(article)

            validation_summary = {
                "total_articles": len(articles),
                "valid_count": len(valid_articles),
                "invalid_count": len(invalid_articles),
                "validation_passed": len(valid_articles)
                >= 3,  # Minimum 3 articles needed
                "min_articles_required": 3,
            }

            logger.info(
                f"Validation complete: {validation_summary['valid_count']}/{validation_summary['total_articles']} articles valid"
            )

            return {
                "valid_articles": valid_articles,
                "invalid_articles": invalid_articles,
                "validation_summary": validation_summary,
            }

        except Exception as e:
            logger.error(f"Failed to validate articles: {e}")
            raise

    def _check_if_analyzed_sync(self, db: Session, article_id: int) -> bool:
        """Check if an article has already been analyzed (synchronous version)."""
        try:
            query = text(
                "SELECT 1 FROM article_analyses WHERE article_id = :article_id LIMIT 1"
            )
            result = db.execute(query, {"article_id": article_id})
            return result.fetchone() is not None
        except Exception:
            return False

    def get_recent_analyzable_articles_sync(
        self, db: Session, hours_back: int = 24, limit: int = 50
    ) -> list[int]:
        """
        Get recent unanalyzed article IDs for priority processing.

        This method prioritizes articles from the last N hours to ensure
        timely analysis for newsletter generation.

        Args:
            db: Database session
            hours_back: How many hours back to look for articles (default: 24)
            limit: Maximum number of articles to return (default: 50)

        Returns:
            List of recent article IDs suitable for analysis
        """
        try:
            query = text(
                """
                SELECT a.id
                FROM articles a
                LEFT JOIN article_analyses aa ON a.id = aa.article_id
                WHERE aa.id IS NULL  -- Not yet analyzed
                  AND LENGTH(a.body) > :min_length  -- Substantial content
                  AND a.body IS NOT NULL
                  AND a.body != ''
                  AND a.status = 'ACTIVE'  -- Only active articles
                  AND a.created_at >= NOW() - (:hours_back || ' hours')::INTERVAL  -- Recent articles
                ORDER BY a.created_at DESC, a.published_on DESC
                LIMIT :limit
                """
            )

            result = db.execute(
                query,
                {
                    "min_length": self.min_content_length,
                    "hours_back": hours_back,
                    "limit": limit,
                },
            )

            article_ids = [row[0] for row in result.fetchall()]

            logger.info(
                f"Found {len(article_ids)} recent analyzable articles "
                f"(last {hours_back}h, min_length: {self.min_content_length})"
            )

            return article_ids

        except Exception as e:
            logger.error(f"Failed to get recent analyzable articles: {str(e)}")
            return []

    def get_priority_analyzable_articles_sync(
        self, db: Session, limit: int = 200, prioritize_recent: bool = True
    ) -> list[int]:
        """
        Get article IDs with intelligent prioritization for batch processing.

        This method implements smart article selection:
        1. Recent articles (last 24 hours) get highest priority
        2. Quality publishers get preference
        3. Longer articles get preference (more content to analyze)

        Args:
            db: Database session
            limit: Maximum number of articles to return
            prioritize_recent: Whether to prioritize recent articles

        Returns:
            List of prioritized article IDs for analysis
        """
        try:
            # Quality publishers that typically have better content
            quality_publishers = [
                "CoinDesk",
                "NewsBTC",
                "Crypto Potato",
                "CoinTelegraph",
            ]

            if prioritize_recent:
                # First try to get recent articles (last 24 hours)
                recent_articles = self.get_recent_analyzable_articles_sync(
                    db, hours_back=24, limit=min(limit, 30)
                )

                if len(recent_articles) >= 10:  # If we have enough recent articles
                    logger.info(
                        f"Using {len(recent_articles)} recent articles for priority processing"
                    )
                    return recent_articles

                # If not enough recent articles, supplement with older ones
                remaining_limit = limit - len(recent_articles)
                if remaining_limit > 0:
                    older_articles = self._get_older_quality_articles_sync(
                        db, limit=remaining_limit, exclude_ids=recent_articles
                    )
                    combined = recent_articles + older_articles
                    logger.info(
                        f"Combined {len(recent_articles)} recent + {len(older_articles)} "
                        f"older articles for processing"
                    )
                    return combined

                return recent_articles
            else:
                # Use the standard method for non-priority processing
                return self.get_analyzable_articles_sync(db, limit=limit)

        except Exception as e:
            logger.error(f"Failed to get priority analyzable articles: {str(e)}")
            # Fallback to standard method
            return self.get_analyzable_articles_sync(db, limit=limit)

    def _get_older_quality_articles_sync(
        self, db: Session, limit: int = 100, exclude_ids: list[int] = None
    ) -> list[int]:
        """Get older articles with quality prioritization."""
        try:
            exclude_clause = ""
            params = {"min_length": self.min_content_length, "limit": limit}

            if exclude_ids:
                exclude_placeholder = ",".join(
                    [f":exclude_{i}" for i in range(len(exclude_ids))]
                )
                exclude_clause = f"AND a.id NOT IN ({exclude_placeholder})"
                for i, article_id in enumerate(exclude_ids):
                    params[f"exclude_{i}"] = article_id

            query = text(
                f"""
                SELECT a.id
                FROM articles a
                LEFT JOIN article_analyses aa ON a.id = aa.article_id
                LEFT JOIN publishers p ON a.publisher_id = p.id
                WHERE aa.id IS NULL  -- Not yet analyzed
                  AND LENGTH(a.body) > :min_length  -- Substantial content
                  AND a.body IS NOT NULL
                  AND a.body != ''
                  AND a.status = 'ACTIVE'  -- Only active articles
                  {exclude_clause}
                ORDER BY
                  CASE WHEN p.name IN ('CoinDesk', 'NewsBTC', 'Crypto Potato', 'CoinTelegraph')
                       THEN 1 ELSE 2 END,  -- Quality publishers first
                  LENGTH(a.body) DESC,  -- Longer articles preferred
                  a.published_on DESC   -- Newer articles preferred
                LIMIT :limit
                """
            )

            result = db.execute(query, params)
            article_ids = [row[0] for row in result.fetchall()]

            logger.info(
                f"Found {len(article_ids)} older quality articles for supplemental processing"
            )
            return article_ids

        except Exception as e:
            logger.error(f"Failed to get older quality articles: {str(e)}")
            return []
