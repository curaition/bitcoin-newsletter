"""Public API endpoints for external integrations."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Security
from fastapi.security.api_key import APIKeyHeader

from crypto_newsletter.core.storage.repository import ArticleRepository
from crypto_newsletter.shared.config.settings import get_settings
from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.web.models import (
    ArticleResponse,
    PublisherResponse,
    StatsResponse,
    TaskScheduleRequest,
)

router = APIRouter()

# API Key authentication (optional for public endpoints)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: str = Security(api_key_header)) -> Optional[str]:
    """
    Validate API key for protected endpoints.

    Args:
        api_key: API key from header

    Returns:
        Validated API key or None for public access
    """
    settings = get_settings()

    # For development, allow access without API key
    if settings.railway_environment == "development":
        return api_key

    # In production, validate API key if provided
    if api_key and hasattr(settings, 'api_key') and api_key == settings.api_key:
        return api_key

    # Public endpoints don't require API key
    return None


@router.get("/articles", response_model=List[ArticleResponse])
async def get_articles(
    limit: int = Query(10, description="Maximum number of articles to return", le=100),
    offset: int = Query(0, description="Number of articles to skip"),
    publisher_id: Optional[int] = Query(None, description="Filter by publisher ID"),
    hours_back: Optional[int] = Query(None, description="Filter by hours back from now"),
    api_key: Optional[str] = Security(get_api_key),
) -> List[ArticleResponse]:
    """
    Get list of articles with optional filtering.
    
    Args:
        limit: Maximum number of articles to return
        offset: Number of articles to skip for pagination
        publisher_id: Filter by specific publisher
        hours_back: Filter by articles from last N hours
        api_key: Optional API key for authentication
        
    Returns:
        List of articles matching criteria
    """
    try:
        async with get_db_session() as db:
            repo = ArticleRepository(db)
            
            # Get articles with filters
            articles = await repo.get_recent_articles(
                limit=limit,
                offset=offset,
                publisher_id=publisher_id,
                hours_back=hours_back,
            )
            
            # Convert to response models
            return [
                ArticleResponse(
                    id=article["id"],
                    external_id=article.get("external_id", 0),
                    title=article["title"],
                    subtitle=article.get("subtitle"),
                    url=article["url"],
                    published_on=article["published_on"],
                    publisher_id=article.get("publisher_id"),
                    language=article.get("language"),
                    status=article.get("status", "ACTIVE"),
                )
                for article in articles
            ]
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch articles: {e}"
        )


@router.get("/publishers", response_model=List[PublisherResponse])
async def get_publishers(
    api_key: Optional[str] = Security(get_api_key),
) -> List[PublisherResponse]:
    """
    Get list of all publishers.
    
    Args:
        api_key: Optional API key for authentication
        
    Returns:
        List of all publishers
    """
    try:
        async with get_db_session() as db:
            repo = ArticleRepository(db)
            publishers = await repo.get_all_publishers_dict()

            return [
                PublisherResponse(
                    id=pub["id"],
                    source_id=pub["source_id"],
                    name=pub["name"],
                    source_key=pub["source_key"],
                    url=pub.get("url"),
                    lang=pub.get("lang"),
                    status=pub.get("status"),
                )
                for pub in publishers
            ]
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch publishers: {e}"
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    api_key: Optional[str] = Security(get_api_key),
) -> StatsResponse:
    """
    Get system statistics.
    
    Args:
        api_key: Optional API key for authentication
        
    Returns:
        System statistics
    """
    try:
        async with get_db_session() as db:
            repo = ArticleRepository(db)
            stats = await repo.get_article_statistics()

            return StatsResponse(
                total_articles=stats.get("total_articles", 0),
                recent_articles=stats.get("recent_articles_24h", 0),
                total_publishers=stats.get("total_publishers", 0),
                total_categories=stats.get("total_categories", 0),
                top_publishers=stats.get("top_publishers", []),
                top_categories=stats.get("top_categories", []),
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {e}"
        )


@router.get("/articles/{article_id}")
async def get_article(
    article_id: int,
    api_key: Optional[str] = Security(get_api_key),
) -> Dict[str, Any]:
    """
    Get detailed information about a specific article.
    
    Args:
        article_id: ID of the article to retrieve
        api_key: Optional API key for authentication
        
    Returns:
        Detailed article information
    """
    try:
        async with get_db_session() as db:
            repo = ArticleRepository(db)
            article = await repo.get_article_by_id(article_id)
            
            if not article:
                raise HTTPException(
                    status_code=404,
                    detail=f"Article with ID {article_id} not found"
                )
            
            return article
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch article: {e}"
        )


# Webhook endpoint for external triggers (future use)
@router.post("/webhook/trigger-ingest")
async def webhook_trigger_ingest(
    request: TaskScheduleRequest,
    api_key: Optional[str] = Security(get_api_key),
) -> Dict[str, Any]:
    """
    Webhook endpoint to trigger article ingestion.
    
    Args:
        request: Ingestion parameters
        api_key: Optional API key for authentication
        
    Returns:
        Task scheduling result
    """
    settings = get_settings()
    
    if not settings.enable_celery:
        # Run synchronously if Celery is disabled
        try:
            from crypto_newsletter.core.ingestion.pipeline import ArticleIngestionPipeline
            
            pipeline = ArticleIngestionPipeline()
            results = await pipeline.run_full_ingestion(
                limit=request.limit,
                hours_back=request.hours_back,
                categories=request.categories,
            )
            
            return {
                "success": True,
                "mode": "synchronous",
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Synchronous ingestion failed: {e}"
            )
    
    else:
        # Schedule with Celery
        try:
            from crypto_newsletter.core.scheduling.tasks import manual_ingest
            
            result = manual_ingest.delay(
                limit=request.limit,
                hours_back=request.hours_back,
                categories=request.categories,
            )
            
            return {
                "success": True,
                "mode": "asynchronous",
                "task_id": result.id,
                "status": result.status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to schedule webhook ingestion: {e}"
            )
