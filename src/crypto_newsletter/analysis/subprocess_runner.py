#!/usr/bin/env python3
"""
Subprocess runner for article analysis.

This module runs article analysis in a separate process to completely
isolate async operations from Celery's event loop context.
"""

import asyncio
import json
import logging
import sys
from typing import Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_article_analysis(article_id: int) -> dict[str, Any]:
    """
    Run article analysis in a clean async context.
    
    This function runs in a separate process with its own event loop,
    completely isolated from Celery's execution context.
    """
    try:
        from crypto_newsletter.shared.database.connection import get_db_session
        from crypto_newsletter.shared.models import Article
        from crypto_newsletter.analysis.agents.orchestrator import orchestrator
        from crypto_newsletter.analysis.agents.settings import analysis_settings
        from crypto_newsletter.analysis.dependencies import AnalysisDependencies, CostTracker
        
        async with get_db_session() as db:
            # Get article from database
            article = await db.get(Article, article_id)
            if not article:
                return {
                    "success": False,
                    "article_id": article_id,
                    "error": f"Article {article_id} not found",
                    "requires_manual_review": False,
                }

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
            cost_tracker = CostTracker(
                daily_budget=analysis_settings.daily_analysis_budget
            )
            
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
                from crypto_newsletter.analysis.tasks import _store_analysis_results
                await _store_analysis_results(db, article_id, result)
                await db.commit()

                logger.info(
                    f"Subprocess analysis complete for article {article_id}. "
                    f"Cost: ${result['costs']['total']:.4f}, "
                    f"Signals: {result['processing_metadata']['signals_found']}"
                )

            return result

    except Exception as e:
        logger.error(f"Subprocess analysis failed for article {article_id}: {str(e)}")
        return {
            "success": False,
            "article_id": article_id,
            "error": str(e),
            "requires_manual_review": True,
        }


def main():
    """Main entry point for subprocess execution."""
    if len(sys.argv) != 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: python -m crypto_newsletter.analysis.subprocess_runner <article_id>",
            "requires_manual_review": False,
        }))
        sys.exit(1)
    
    try:
        article_id = int(sys.argv[1])
    except ValueError:
        print(json.dumps({
            "success": False,
            "error": "Article ID must be an integer",
            "requires_manual_review": False,
        }))
        sys.exit(1)
    
    # Run the analysis
    result = asyncio.run(run_article_analysis(article_id))
    
    # Output result as JSON
    print(json.dumps(result))
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
