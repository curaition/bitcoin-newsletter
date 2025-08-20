"""Celery tasks for article analysis using PydanticAI agents."""

import asyncio
import logging
from datetime import datetime
from typing import Any

from crypto_newsletter.shared.celery.app import celery_app
from crypto_newsletter.shared.database.connection import (
    get_db_session,
    get_sync_db_session
)
from crypto_newsletter.shared.models import Article, ArticleAnalysis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .agents.orchestrator import orchestrator
from .agents.settings import analysis_settings
from .dependencies import AnalysisDependencies, CostTracker

logger = logging.getLogger(__name__)


async def analyze_article_direct(
    article_id: int,
    db: AsyncSession,
    cost_tracker: CostTracker
) -> dict[str, Any]:
    """
    Direct async analysis function that bypasses Celery task wrapper.

    This function is designed to be called from async batch processing tasks
    to avoid event loop conflicts. It performs the same analysis as the
    original analyze_article_task but in a pure async context.

    Args:
        article_id: ID of the article to analyze
        db: Async database session
        cost_tracker: Cost tracking instance for budget monitoring

    Returns:
        Dict with analysis results and metadata
    """
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
            cost_tracker=cost_tracker,
            current_publisher=article.publisher,
            current_article_id=article_id,
            max_searches_per_validation=analysis_settings.max_searches_per_validation,
            min_signal_confidence=analysis_settings.min_signal_confidence,
        )

        # Check budget before starting
        if not cost_tracker.can_afford(analysis_settings.max_cost_per_article):
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
            # Note: Don't commit here - let the batch processing handle commits

            logger.info(
                f"Analysis complete for article {article_id}. "
                f"Cost: ${result['costs']['total']:.4f}, "
                f"Signals: {result['processing_metadata']['signals_found']}"
            )

        return result

    except Exception as e:
        logger.error(f"Direct analysis failed for article {article_id}: {str(e)}")
        return {
            "success": False,
            "article_id": article_id,
            "error": str(e),
            "requires_manual_review": True,
        }


def analyze_article_sync(article_id: int, cost_tracker: CostTracker) -> dict[str, Any]:
    """
    Sync wrapper for article analysis using sync database operations.

    This function uses sync database operations to avoid SQLAlchemy async
    issues in Celery workers, while still using async AI agents via asyncio.run().
    """
    try:
        with get_sync_db_session() as db:
            # Get article using sync database operations
            article = db.query(Article).filter(Article.id == article_id).first()
            if not article:
                logger.error(f"Article {article_id} not found")
                return {
                    "success": False,
                    "article_id": article_id,
                    "error": f"Article {article_id} not found"
                }

            # Check if article meets minimum requirements
            if len(article.body or "") < analysis_settings.min_content_length:
                logger.warning(f"Article {article_id} too short for analysis")
                return {
                    "success": False,
                    "article_id": article_id,
                    "error": "Article too short for analysis"
                }

            # Check if analysis already exists
            existing_analysis = db.query(ArticleAnalysis).filter(
                ArticleAnalysis.article_id == article_id
            ).first()

            if existing_analysis:
                logger.info(f"Analysis already exists for article {article_id}")
                return {
                    "success": True,
                    "article_id": article_id,
                    "analysis_id": existing_analysis.id,
                    "skipped": True,
                    "reason": "Analysis already exists"
                }

            # Run async analysis using asyncio.run()
            logger.info(f"Starting analysis for article {article_id}")

            # Create a new event loop for the async analysis
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Run the async analysis
                analysis_result = loop.run_until_complete(
                    orchestrator.run_async(
                        article_content=article.body,
                        article_title=article.title,
                        article_url=article.url,
                        cost_tracker=cost_tracker,
                        current_publisher=article.publisher,
                        current_article_id=article_id,
                        max_searches_per_validation=analysis_settings.max_searches_per_validation,
                        min_signal_confidence=analysis_settings.min_signal_confidence,
                    )
                )
            finally:
                loop.close()

            # Store results using sync database operations
            if analysis_result.data and hasattr(analysis_result.data, 'signals'):
                signals = analysis_result.data.signals

                # Create analysis record
                analysis = ArticleAnalysis(
                    article_id=article_id,
                    signals_detected=len(signals),
                    analysis_summary=analysis_result.data.summary,
                    confidence_score=analysis_result.data.overall_confidence,
                    processing_cost=cost_tracker.total_cost,
                    raw_analysis_data={
                        "signals": [signal.model_dump() for signal in signals],
                        "summary": analysis_result.data.summary,
                        "overall_confidence": analysis_result.data.overall_confidence,
                        "processing_metadata": {
                            "total_cost": cost_tracker.total_cost,
                            "processing_time": cost_tracker.processing_time,
                        }
                    }
                )

                db.add(analysis)
                db.commit()

                logger.info(f"Analysis completed for article {article_id}")
                return {
                    "success": True,
                    "article_id": article_id,
                    "analysis_id": analysis.id,
                    "signals_detected": len(signals),
                    "confidence_score": analysis_result.data.overall_confidence,
                    "processing_cost": cost_tracker.total_cost
                }
            else:
                logger.warning(f"No analysis data returned for article {article_id}")
                return {
                    "success": False,
                    "article_id": article_id,
                    "error": "No analysis data returned"
                }

    except Exception as e:
        logger.error(f"Sync analysis failed for article {article_id}: {str(e)}")
        return {
            "success": False,
            "article_id": article_id,
            "error": str(e)
        }


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
        # Use a more robust approach for AsyncIO/Celery integration
        return _run_analysis_sync_wrapper(article_id)
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


def _run_analysis_sync_wrapper(article_id: int) -> dict[str, Any]:
    """
    Synchronous wrapper for analysis that works with both Celery and batch processing.
    This function handles the AsyncIO/Celery integration properly.
    """
    import concurrent.futures
    import threading

    def run_in_new_thread():
        """Run the async analysis in a completely new thread with its own event loop."""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Run the async analysis function
            async def _run_analysis_internal() -> dict[str, Any]:
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

            return loop.run_until_complete(_run_analysis_internal())
        finally:
            loop.close()

    # Run in a separate thread to completely isolate from any existing event loop
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_in_new_thread)
        return future.result()


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
