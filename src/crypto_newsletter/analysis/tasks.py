"""Celery tasks for article analysis using PydanticAI agents."""

import asyncio
import logging
from datetime import datetime
from typing import Any

from crypto_newsletter.shared.celery.app import celery_app
from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.shared.models import Article, ArticleAnalysis
from sqlalchemy.ext.asyncio import AsyncSession

from .agents.orchestrator import orchestrator
from .agents.settings import analysis_settings
from .dependencies import AnalysisDependencies, CostTracker

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="crypto_newsletter.analysis.tasks.analyze_article",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def analyze_article_task(self, article_id: int) -> dict[str, Any]:
    """
    Analyze a single article using PydanticAI agents.

    Args:
        article_id: ID of the article to analyze

    Returns:
        Dict with analysis results and metadata
    """

    async def _run_analysis() -> dict[str, Any]:
        """Internal async function to run the analysis."""

        async with get_db_session() as db:
            try:
                # Get article from database
                article = await db.get(Article, article_id)
                if not article:
                    raise ValueError(f"Article {article_id} not found")

                # Check if article meets minimum requirements
                if len(article.body or "") < analysis_settings.min_content_length:
                    logger.warning(f"Article {article_id} too short for analysis")
                    return {
                        "success": False,
                        "article_id": article_id,
                        "error": "Article content too short for analysis",
                        "requires_manual_review": False,
                    }

                # Set up dependencies
                deps = AnalysisDependencies(
                    db_session=db,
                    cost_tracker=CostTracker(
                        daily_budget=analysis_settings.daily_analysis_budget
                    ),
                    current_publisher=article.publisher,
                    current_article_id=article_id,
                    max_searches_per_validation=analysis_settings.max_searches_per_validation,
                    min_signal_confidence=analysis_settings.min_signal_confidence,
                )

                # Check budget before starting
                if not deps.cost_tracker.can_afford(
                    analysis_settings.max_cost_per_article
                ):
                    logger.warning(f"Insufficient budget for article {article_id}")
                    return {
                        "success": False,
                        "article_id": article_id,
                        "error": "Daily analysis budget exceeded",
                        "requires_manual_review": False,
                    }

                # Run orchestrated analysis
                result = await orchestrator.analyze_article(
                    article_id=article_id,
                    title=article.title,
                    body=article.body,
                    publisher=article.publisher,
                    deps=deps,
                )

                # Store results in database if successful
                if result["success"]:
                    await _store_analysis_results(db, article_id, result)
                    await db.commit()

                    logger.info(
                        f"Analysis complete for article {article_id}. "
                        f"Cost: ${result['costs']['total']:.4f}, "
                        f"Signals: {result['processing_metadata']['signals_found']}"
                    )

                return result

            except Exception as e:
                await db.rollback()
                logger.error(f"Analysis failed for article {article_id}: {str(e)}")
                raise

    # Run the async analysis with proper event loop handling
    try:
        # Check if there's already an event loop running
        try:
            loop = asyncio.get_running_loop()
            # If we're in an event loop, we need to run in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _run_analysis())
                return future.result()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run
            return asyncio.run(_run_analysis())
    except Exception as e:
        logger.error(f"Task failed for article {article_id}: {str(e)}")
        # Don't retry on certain errors
        if "not found" in str(e).lower() or "too short" in str(e).lower():
            return {
                "success": False,
                "article_id": article_id,
                "error": str(e),
                "requires_manual_review": False,
            }
        raise


async def _store_analysis_results(
    db: AsyncSession, article_id: int, result: dict[str, Any]
) -> None:
    """Store analysis results in the database."""

    content_analysis = result["content_analysis"]
    signal_validation = result.get("signal_validation")

    # Create analysis record with correct field mappings
    analysis = ArticleAnalysis(
        article_id=article_id,
        sentiment=content_analysis.sentiment,
        impact_score=content_analysis.impact_score,
        summary=content_analysis.summary,
        context=content_analysis.context,
        weak_signals=content_analysis.weak_signals,
        pattern_anomalies=content_analysis.pattern_anomalies,
        adjacent_connections=content_analysis.adjacent_connections,
        narrative_gaps=content_analysis.narrative_gaps,
        edge_indicators=content_analysis.edge_indicators,
        analysis_confidence=content_analysis.analysis_confidence,
        signal_strength=content_analysis.signal_strength,
        uniqueness_score=content_analysis.uniqueness_score,
        # Map validation results to correct database fields
        verified_facts=signal_validation.validation_results
        if signal_validation
        else [],
        research_sources=signal_validation.cross_signal_insights
        if signal_validation
        else [],
        validation_status="COMPLETED" if signal_validation else "PENDING",
        # Map cost and processing data to correct database fields
        processing_time_ms=int(result.get("processing_metadata", {}).get("processing_time_ms", 0)),
        token_usage=result.get("usage", {}).get("total_tokens", 0),
        cost_usd=result["costs"]["total"],
    )

    db.add(analysis)


# Note: analyze_recent_articles_task removed - batch processing is handled
# by the dedicated batch processing system in crypto_newsletter.newsletter.batch
