"""Newsletter generation Celery tasks."""

import logging
from datetime import datetime, timedelta
from typing import Any

from crypto_newsletter.core.storage import ArticleRepository, NewsletterRepository
from crypto_newsletter.newsletter.agents.orchestrator import NewsletterOrchestrator
from crypto_newsletter.newsletter.storage import NewsletterStorage
from crypto_newsletter.shared.celery.app import celery_app
from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.shared.models import Newsletter

logger = logging.getLogger(__name__)


async def _convert_articles_for_agents(articles, db_session):
    """Convert Article model instances to dictionary format for agent system."""
    from crypto_newsletter.shared.models import ArticleAnalysis, Publisher
    from sqlalchemy import select

    articles_for_agents = []

    for article in articles:
        # Get analysis data for this article
        analysis_query = (
            select(ArticleAnalysis)
            .where(ArticleAnalysis.article_id == article.id)
            .order_by(ArticleAnalysis.created_at.desc())
            .limit(1)
        )

        analysis_result = await db_session.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()

        # Get publisher name
        publisher_query = select(Publisher).where(Publisher.id == article.publisher_id)
        publisher_result = await db_session.execute(publisher_query)
        publisher = publisher_result.scalar_one_or_none()

        # Convert to dictionary format expected by agents
        article_dict = {
            "id": article.id,
            "title": article.title,
            "body": article.body,
            "published_on": article.published_on.isoformat()
            if article.published_on
            else None,
            "publisher": publisher.name if publisher else "Unknown",
            "url": article.url,
            # Analysis fields with defaults
            "weak_signals": analysis.weak_signals if analysis else [],
            "pattern_anomalies": analysis.pattern_anomalies if analysis else [],
            "adjacent_connections": analysis.adjacent_connections if analysis else [],
            "signal_strength": float(analysis.signal_strength)
            if analysis and analysis.signal_strength
            else 0.0,
            "uniqueness_score": float(analysis.uniqueness_score)
            if analysis and analysis.uniqueness_score
            else 0.0,
            "analysis_confidence": float(analysis.analysis_confidence)
            if analysis and analysis.analysis_confidence
            else 0.0,
            "narrative_gaps": analysis.narrative_gaps if analysis else [],
            "edge_indicators": analysis.edge_indicators if analysis else [],
        }

        articles_for_agents.append(article_dict)

    return articles_for_agents


class NewsletterGenerationException(Exception):
    """Raised when newsletter generation fails."""

    pass


@celery_app.task(
    bind=True,
    name="crypto_newsletter.newsletter.tasks.generate_daily_newsletter",
    max_retries=2,
    default_retry_delay=1800,  # 30 minutes
    queue="newsletter",
)
async def generate_daily_newsletter_task(
    self, force_generation: bool = False
) -> dict[str, Any]:
    """
    Generate daily newsletter from past 24 hours of analyzed articles.

    Args:
        force_generation: Generate even if insufficient articles

    Returns:
        Dict with generation results and metadata
    """

    async def _generate_daily_newsletter() -> dict[str, Any]:
        """Internal async function for daily newsletter generation."""

        task_start = datetime.utcnow()
        generation_metadata = {
            "task_started_at": task_start.isoformat(),
            "newsletter_type": "DAILY",
            "force_generation": force_generation,
        }

        try:
            async with get_db_session() as db:
                # Step 1: Get analyzed articles from past 24 hours
                article_repo = ArticleRepository(db)
                newsletter_repo = NewsletterRepository(db)

                # Get articles with completed analysis from last 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                daily_articles = await article_repo.get_articles_with_analysis_since(
                    since_date=cutoff_time,
                    min_signal_strength=0.5,  # Filter for quality articles
                    limit=100,
                )

                logger.info(
                    f"Found {len(daily_articles)} analyzed articles from past 24 hours"
                )
                generation_metadata["articles_found"] = len(daily_articles)

                # Step 2: Quality check - ensure sufficient content
                if len(daily_articles) < 10 and not force_generation:
                    logger.warning(
                        f"Insufficient articles for daily newsletter: {len(daily_articles)}"
                    )
                    return {
                        "status": "skipped",
                        "reason": "insufficient_content",
                        "articles_found": len(daily_articles),
                        "minimum_required": 10,
                        "generation_metadata": generation_metadata,
                    }

                # Step 3: Check if newsletter already exists for today
                today = datetime.utcnow().date()
                existing_newsletters = (
                    await newsletter_repo.get_newsletters_by_date_range(
                        start_date=today, end_date=today
                    )
                )

                daily_newsletters_today = [
                    n
                    for n in existing_newsletters
                    if n.generation_metadata
                    and n.generation_metadata.get("newsletter_type") == "DAILY"
                ]

                if daily_newsletters_today and not force_generation:
                    existing = daily_newsletters_today[0]
                    logger.info(f"Daily newsletter already exists for {today}")
                    return {
                        "status": "already_exists",
                        "newsletter_id": existing.id,
                        "publication_date": today.isoformat(),
                        "generation_metadata": generation_metadata,
                    }

                # Step 4: Convert articles to dictionary format for agent system
                articles_for_agents = await _convert_articles_for_agents(
                    daily_articles, db
                )

                # Step 5: Generate newsletter using orchestrator
                logger.info("Starting daily newsletter generation with agent system")

                orchestrator = NewsletterOrchestrator()
                generation_result = await orchestrator.generate_newsletter(
                    articles=articles_for_agents, newsletter_type="DAILY"
                )

                if not generation_result["success"]:
                    raise NewsletterGenerationException(
                        f"Agent generation failed: {generation_result.get('error', 'Unknown error')}"
                    )

                # Step 5: Store newsletter in database
                storage = NewsletterStorage(db)
                newsletter = await storage.create_newsletter(
                    newsletter_content=generation_result["newsletter_content"],
                    story_selection=generation_result["story_selection"],
                    synthesis=generation_result["synthesis"],
                    generation_metadata={
                        **generation_metadata,
                        **generation_result["generation_metadata"],
                        "newsletter_type": "DAILY",
                    },
                )

                # Step 6: Calculate processing time and costs
                processing_time = (datetime.utcnow() - task_start).total_seconds()
                generation_cost = generation_result["generation_metadata"].get(
                    "generation_cost", 0.0
                )

                logger.info(
                    f"Daily newsletter generated successfully - "
                    f"ID: {newsletter.id}, Time: {processing_time:.2f}s, "
                    f"Cost: ${generation_cost:.4f}"
                )

                return {
                    "status": "success",
                    "newsletter_id": newsletter.id,
                    "publication_date": today.isoformat(),
                    "articles_processed": len(daily_articles),
                    "stories_selected": len(
                        generation_result["story_selection"].selected_stories
                    ),
                    "generation_cost": generation_cost,
                    "processing_time_seconds": processing_time,
                    "quality_score": generation_result[
                        "newsletter_content"
                    ].editorial_quality_score,
                    "generation_metadata": generation_metadata,
                }

        except Exception as exc:
            logger.error(f"Daily newsletter generation failed: {exc}")

            # Retry logic
            if self.request.retries < self.max_retries:
                retry_delay = 1800 * (self.request.retries + 1)  # Exponential backoff
                logger.warning(
                    f"Retrying daily newsletter generation in {retry_delay} seconds"
                )
                raise self.retry(countdown=retry_delay, exc=exc)

            return {
                "status": "failed",
                "error": str(exc),
                "retries_exhausted": True,
                "generation_metadata": generation_metadata,
            }

    return await _generate_daily_newsletter()


@celery_app.task(
    bind=True,
    name="crypto_newsletter.newsletter.tasks.generate_weekly_newsletter",
    max_retries=2,
    default_retry_delay=1800,  # 30 minutes
    queue="newsletter",
)
async def generate_weekly_newsletter_task(
    self, force_generation: bool = False
) -> dict[str, Any]:
    """
    Generate weekly newsletter from past 7 days of daily newsletters.

    Args:
        force_generation: Generate even if insufficient daily newsletters

    Returns:
        Dict with generation results and metadata
    """

    async def _generate_weekly_newsletter() -> dict[str, Any]:
        """Internal async function for weekly newsletter generation."""

        task_start = datetime.utcnow()
        generation_metadata = {
            "task_started_at": task_start.isoformat(),
            "newsletter_type": "WEEKLY",
            "force_generation": force_generation,
        }

        try:
            async with get_db_session() as db:
                # Step 1: Get daily newsletters from past 7 days
                newsletter_repo = NewsletterRepository(db)

                # Get date range for past 7 days
                end_date = datetime.utcnow().date()
                start_date = end_date - timedelta(days=7)

                all_newsletters = await newsletter_repo.get_newsletters_by_date_range(
                    start_date=start_date,
                    end_date=end_date,
                    status="PUBLISHED",  # Only use published daily newsletters
                )

                # Filter for daily newsletters only
                daily_newsletters = [
                    n
                    for n in all_newsletters
                    if n.generation_metadata
                    and n.generation_metadata.get("newsletter_type") == "DAILY"
                ]

                logger.info(
                    f"Found {len(daily_newsletters)} daily newsletters from past 7 days"
                )
                generation_metadata["daily_newsletters_found"] = len(daily_newsletters)

                # Step 2: Quality check - ensure sufficient daily newsletters
                if len(daily_newsletters) < 3 and not force_generation:
                    logger.warning(
                        f"Insufficient daily newsletters for weekly newsletter: {len(daily_newsletters)}"
                    )
                    return {
                        "status": "skipped",
                        "reason": "insufficient_daily_newsletters",
                        "daily_newsletters_found": len(daily_newsletters),
                        "minimum_required": 3,
                        "generation_metadata": generation_metadata,
                    }

                # Step 3: Check if weekly newsletter already exists for this week
                # Check for existing weekly newsletters in the past 7 days
                weekly_newsletters_this_week = [
                    n
                    for n in all_newsletters
                    if n.generation_metadata
                    and n.generation_metadata.get("newsletter_type") == "WEEKLY"
                ]

                if weekly_newsletters_this_week and not force_generation:
                    existing = weekly_newsletters_this_week[0]
                    logger.info("Weekly newsletter already exists for this week")
                    return {
                        "status": "already_exists",
                        "newsletter_id": existing.id,
                        "generation_metadata": generation_metadata,
                    }

                # Step 4: Generate weekly newsletter using orchestrator
                logger.info("Starting weekly newsletter generation with agent system")

                orchestrator = NewsletterOrchestrator()
                generation_result = await orchestrator.generate_weekly_newsletter(
                    daily_newsletters=daily_newsletters
                )

                if not generation_result["success"]:
                    raise NewsletterGenerationException(
                        f"Weekly agent generation failed: {generation_result.get('error', 'Unknown error')}"
                    )

                # Step 5: Store newsletter in database
                storage = NewsletterStorage(db)
                newsletter = await storage.create_newsletter(
                    newsletter_content=generation_result["newsletter_content"],
                    story_selection=generation_result["story_selection"],
                    synthesis=generation_result["synthesis"],
                    generation_metadata={
                        **generation_metadata,
                        **generation_result["generation_metadata"],
                        "newsletter_type": "WEEKLY",
                        "source_daily_newsletters": [n.id for n in daily_newsletters],
                    },
                )

                # Step 6: Calculate processing time and costs
                processing_time = (datetime.utcnow() - task_start).total_seconds()
                generation_cost = generation_result["generation_metadata"].get(
                    "generation_cost", 0.0
                )

                logger.info(
                    f"Weekly newsletter generated successfully - "
                    f"ID: {newsletter.id}, Time: {processing_time:.2f}s, "
                    f"Cost: ${generation_cost:.4f}"
                )

                return {
                    "status": "success",
                    "newsletter_id": newsletter.id,
                    "daily_newsletters_processed": len(daily_newsletters),
                    "generation_cost": generation_cost,
                    "processing_time_seconds": processing_time,
                    "quality_score": generation_result[
                        "newsletter_content"
                    ].editorial_quality_score,
                    "generation_metadata": generation_metadata,
                }

        except Exception as exc:
            logger.error(f"Weekly newsletter generation failed: {exc}")

            # Retry logic
            if self.request.retries < self.max_retries:
                retry_delay = 1800 * (self.request.retries + 1)  # Exponential backoff
                logger.warning(
                    f"Retrying weekly newsletter generation in {retry_delay} seconds"
                )
                raise self.retry(countdown=retry_delay, exc=exc)

            return {
                "status": "failed",
                "error": str(exc),
                "retries_exhausted": True,
                "generation_metadata": generation_metadata,
            }

    return await _generate_weekly_newsletter()


@celery_app.task(
    bind=True,
    name="crypto_newsletter.newsletter.tasks.generate_newsletter_manual",
    max_retries=1,
    default_retry_delay=300,  # 5 minutes
    queue="newsletter",
)
async def generate_newsletter_manual_task(
    self, newsletter_type: str = "DAILY", force_generation: bool = True
) -> dict[str, Any]:
    """
    Manually trigger newsletter generation.

    Args:
        newsletter_type: Type of newsletter ("DAILY" or "WEEKLY")
        force_generation: Generate even if conditions not met

    Returns:
        Dict with generation results and metadata
    """
    logger.info(f"Manual newsletter generation triggered: {newsletter_type}")

    if newsletter_type.upper() == "DAILY":
        # Call the task function directly by creating a new task instance
        task_instance = generate_daily_newsletter_task
        return await task_instance(self, force_generation=force_generation)
    elif newsletter_type.upper() == "WEEKLY":
        # Call the task function directly by creating a new task instance
        task_instance = generate_weekly_newsletter_task
        return await task_instance(self, force_generation=force_generation)
    else:
        return {
            "status": "failed",
            "error": f"Invalid newsletter type: {newsletter_type}",
            "valid_types": ["DAILY", "WEEKLY"],
        }


# Ghost Publishing Integration Hooks (Future Implementation)
class GhostPublishingHooks:
    """
    Ghost publishing integration hooks for future implementation.

    Based on Ghost Admin API patterns from Context7:
    - POST /admin/posts/ to create posts
    - PUT /admin/posts/{id}/ to publish/schedule
    - Support for HTML content, tags, and scheduling
    """

    @staticmethod
    def prepare_newsletter_for_ghost(newsletter: Newsletter) -> dict[str, Any]:
        """
        Prepare newsletter content for Ghost publishing.

        Args:
            newsletter: Newsletter model instance

        Returns:
            Dict formatted for Ghost Admin API
        """
        return {
            "posts": [
                {
                    "title": newsletter.title,
                    "html": newsletter.content,
                    "custom_excerpt": newsletter.summary,
                    "status": "draft",  # Start as draft
                    "tags": ["newsletter", "bitcoin", "crypto"],
                    "meta_description": newsletter.summary,
                    "feature_image": None,  # Could add newsletter banner
                    "email_subject": newsletter.title,
                    # Ghost-specific fields for newsletter publishing
                    "newsletter": "weekly-newsletter",  # Newsletter slug
                    "email_segment": "all",  # Send to all subscribers
                }
            ]
        }

    @staticmethod
    async def publish_to_ghost(
        newsletter_id: int, ghost_config: dict[str, str]
    ) -> dict[str, Any]:
        """
        Future implementation: Publish newsletter to Ghost.

        Args:
            newsletter_id: Newsletter ID to publish
            ghost_config: Ghost API configuration

        Returns:
            Dict with publishing results
        """
        # This would implement the actual Ghost API integration
        # Using patterns from Context7 Ghost documentation
        return {
            "status": "not_implemented",
            "message": "Ghost publishing integration pending",
            "newsletter_id": newsletter_id,
            "ghost_patterns_available": True,
        }
