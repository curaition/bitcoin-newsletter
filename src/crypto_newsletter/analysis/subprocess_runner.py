#!/usr/bin/env python3
"""
Subprocess runner for article analysis.

This module runs article analysis in a separate process to completely
isolate async operations from Celery's event loop context.
"""

import json
import logging
import sys
from typing import Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_article_analysis_sync(article_id: int) -> dict[str, Any]:
    """
    Run article analysis using sync database operations.

    This function runs in a separate process and uses the original
    sync approach that was working before the async conversion.
    """
    try:
        # Import and initialize database connection in subprocess context
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crypto_newsletter.shared.settings')

        from crypto_newsletter.analysis.tasks import analyze_article_task

        # Use the original sync analysis task that was working
        result = analyze_article_task.run(article_id)
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
    result = run_article_analysis_sync(article_id)
    
    # Output result as JSON
    print(json.dumps(result))
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
