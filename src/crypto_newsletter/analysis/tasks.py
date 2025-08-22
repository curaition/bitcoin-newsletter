"""Celery tasks for article analysis using PydanticAI agents."""

import asyncio
import logging
from typing import Any

from crypto_newsletter.shared.celery.app import celery_app
from crypto_newsletter.shared.database.connection import (
    get_db_session,
    get_sync_db_session,
)
from crypto_newsletter.shared.models import Article, ArticleAnalysis
from sqlalchemy.ext.asyncio import AsyncSession

from .agents.orchestrator import orchestrator
from .agents.settings import analysis_settings
from .dependencies import AnalysisDependencies, CostTracker

logger = logging.getLogger(__name__)


async def analyze_article_direct(
    article_id: int, db: AsyncSession, cost_tracker: CostTracker
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
                    "error": f"Article {article_id} not found",
                }

            # Check if article meets minimum requirements
            if len(article.body or "") < analysis_settings.min_content_length:
                logger.warning(f"Article {article_id} too short for analysis")
                return {
                    "success": False,
                    "article_id": article_id,
                    "error": "Article too short for analysis",
                }

            # Check if analysis already exists
            existing_analysis = (
                db.query(ArticleAnalysis)
                .filter(ArticleAnalysis.article_id == article_id)
                .first()
            )

            if existing_analysis:
                logger.info(f"Analysis already exists for article {article_id}")
                return {
                    "success": True,
                    "article_id": article_id,
                    "analysis_id": existing_analysis.id,
                    "skipped": True,
                    "reason": "Analysis already exists",
                }

            # Run async analysis within the existing event loop context
            logger.info(f"Starting analysis for article {article_id}")

            # Since we're in an AsyncIO pool, we can use asyncio.run directly
            # without creating a new event loop
            async def run_analysis():
                # Create async database session for the orchestrator
                from crypto_newsletter.shared.database.connection import get_db_manager

                async_db_manager = get_db_manager()

                async with async_db_manager.get_session() as async_session:
                    # Create dependencies for the orchestrator
                    from crypto_newsletter.analysis.dependencies import (
                        AnalysisDependencies,
                    )

                    deps = AnalysisDependencies(
                        db_session=async_session,
                        cost_tracker=cost_tracker,
                        current_publisher=article.publisher,
                        current_article_id=article_id,
                        max_searches_per_validation=analysis_settings.max_searches_per_validation,
                        min_signal_confidence=analysis_settings.min_signal_confidence,
                    )

                    # Run the async analysis
                    return await orchestrator.analyze_article(
                        article_id=article_id,
                        title=article.title,
                        body=article.body,
                        publisher=article.publisher,
                        deps=deps,
                    )

            # Since we're in an AsyncIO pool, we can await the coroutine directly
            # by making this function async and calling it properly
            import concurrent.futures

            # Run the async function in a separate thread with proper cleanup
            def run_in_thread():
                # Create a new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    # Run the analysis
                    result = new_loop.run_until_complete(run_analysis())

                    # Give extra time for any lingering async operations (especially HTTP calls)
                    await_time = 2.0  # 2 seconds for HTTP operations to complete
                    logger.debug(f"Waiting {await_time}s for any lingering operations")
                    new_loop.run_until_complete(asyncio.sleep(await_time))

                    # Wait for any pending tasks to complete
                    pending_tasks = asyncio.all_tasks(new_loop)
                    if pending_tasks:
                        logger.debug(
                            f"Waiting for {len(pending_tasks)} pending tasks to complete"
                        )
                        new_loop.run_until_complete(
                            asyncio.gather(*pending_tasks, return_exceptions=True)
                        )

                        # Wait a bit more after task completion
                        new_loop.run_until_complete(asyncio.sleep(0.1))

                    return result
                except Exception as e:
                    logger.error(f"Error in thread analysis: {str(e)}")
                    raise
                finally:
                    # Graceful shutdown of the event loop
                    try:
                        # Wait more before cleanup to ensure all HTTP operations finish
                        new_loop.run_until_complete(asyncio.sleep(1.0))

                        # Cancel any remaining tasks
                        pending_tasks = asyncio.all_tasks(new_loop)
                        if pending_tasks:
                            logger.debug(
                                f"Cancelling {len(pending_tasks)} remaining tasks"
                            )
                            for task in pending_tasks:
                                task.cancel()

                            # Wait for cancellations to complete with timeout
                            try:
                                new_loop.run_until_complete(
                                    asyncio.wait_for(
                                        asyncio.gather(
                                            *pending_tasks, return_exceptions=True
                                        ),
                                        timeout=2.0,  # 2 second timeout for cleanup
                                    )
                                )
                            except asyncio.TimeoutError:
                                logger.warning("Timeout waiting for task cancellations")

                        # Final wait before closing
                        new_loop.run_until_complete(asyncio.sleep(0.1))

                        # Close the loop gracefully
                        if not new_loop.is_closed():
                            new_loop.close()

                    except Exception as cleanup_error:
                        logger.warning(f"Error during loop cleanup: {cleanup_error}")
                        # Force close if graceful cleanup fails
                        if not new_loop.is_closed():
                            try:
                                new_loop.close()
                            except Exception:
                                pass  # Ignore errors during force close

            # Execute in a thread to avoid event loop conflicts
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                # Add timeout to prevent hanging (5 minutes should be enough)
                try:
                    analysis_result = future.result(timeout=300)
                except concurrent.futures.TimeoutError:
                    logger.error(f"Analysis timed out for article {article_id}")
                    return {
                        "success": False,
                        "article_id": article_id,
                        "error": "Analysis timed out after 5 minutes",
                    }

            # Check if analysis was successful
            if not analysis_result.get("success", False):
                logger.error(
                    f"Analysis failed for article {article_id}: {analysis_result.get('error', 'Unknown error')}"
                )
                return analysis_result

            # The orchestrator already stored the results in the database
            # Just return the success result
            logger.info(f"Analysis completed for article {article_id}")
            return {
                "success": True,
                "article_id": article_id,
                "analysis_id": analysis_result.get("analysis_record_id"),
                "processing_cost": analysis_result.get("costs", {}).get("total", 0.0),
            }

    except Exception as e:
        logger.error(f"Sync analysis failed for article {article_id}: {str(e)}")
        return {"success": False, "article_id": article_id, "error": str(e)}


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
                        if (
                            len(article.body or "")
                            < analysis_settings.min_content_length
                        ):
                            logger.warning(
                                f"Article {article_id} too short for analysis"
                            )
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
                            logger.warning(
                                f"Insufficient budget for article {article_id}"
                            )
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
                        logger.error(
                            f"Analysis failed for article {article_id}: {str(e)}"
                        )
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
        processing_time_ms=int(
            result.get("processing_metadata", {}).get("processing_time_ms", 0)
        ),
        token_usage=result.get("usage", {}).get("total_tokens", 0),
        cost_usd=result["costs"]["total"],
    )

    db.add(analysis)


@celery_app.task(
    bind=True,
    name="crypto_newsletter.analysis.tasks.analyze_recent_articles",
    max_retries=2,
    default_retry_delay=300,  # 5 minutes
    queue="analysis",
)
def analyze_recent_articles_task(self, max_articles: int = 10) -> dict[str, Any]:
    """
    Analyze recent unanalyzed articles (scheduled task).

    This task is called by the Celery Beat scheduler every 6 hours to ensure
    new articles get analyzed for newsletter generation. It wraps the existing
    batch processing system with a focus on recent articles.

    Args:
        max_articles: Maximum number of recent articles to analyze (default: 10)

    Returns:
        Dict with analysis results and metadata
    """
    try:
        from crypto_newsletter.analysis.scheduling import analysis_scheduler
        from crypto_newsletter.newsletter.batch.tasks import initiate_batch_processing

        logger.info(f"Starting intelligent scheduled analysis (max: {max_articles})")

        # Use intelligent scheduling decision
        scheduling_decision = analysis_scheduler.should_analyze_now()

        logger.info(f"Scheduling decision: {scheduling_decision['reasoning']}")

        if not scheduling_decision["should_analyze"]:
            return {
                "success": True,
                "status": "skipped",
                "message": scheduling_decision["reasoning"],
                "scheduling_decision": scheduling_decision,
            }

        # Use recommended article count from scheduler
        recommended_count = min(
            scheduling_decision["recommended_articles"], max_articles
        )

        logger.info(f"Proceeding with analysis of up to {recommended_count} articles")

        # Get content status for reporting
        content_status = scheduling_decision.get("content_status", {})
        recent_unanalyzed_count = content_status.get("recent_unanalyzed", 0)

        # Trigger batch processing (it will handle article selection and budget limits)
        logger.info("Triggering batch processing for article analysis")
        batch_result = initiate_batch_processing.delay(force_processing=False)

        # Wait a short time for the batch processing to start
        import time

        time.sleep(2)

        # Get the result (this will be the initiation result, not the full processing result)
        try:
            initiation_result = batch_result.get(
                timeout=30
            )  # 30 second timeout for initiation
        except Exception as e:
            logger.warning(f"Could not get batch processing initiation result: {e}")
            initiation_result = {
                "status": "initiated",
                "message": "Batch processing started but result unavailable",
            }

        return {
            "success": True,
            "status": "batch_initiated",
            "recent_unanalyzed_count": recent_unanalyzed_count,
            "recommended_articles": recommended_count,
            "batch_processing_result": initiation_result,
            "scheduling_decision": scheduling_decision,
            "message": f"Intelligent analysis initiated for up to {recommended_count} articles",
        }

    except Exception as e:
        logger.error(f"Scheduled analysis failed: {str(e)}")
        # Retry the task if it's a temporary failure
        if "budget" not in str(e).lower() and "no articles" not in str(e).lower():
            raise self.retry(exc=e)

        return {
            "success": False,
            "status": "error",
            "error": str(e),
            "message": f"Scheduled analysis failed: {str(e)}",
        }
