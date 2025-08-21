"""Public API endpoints for external integrations."""

from datetime import UTC, datetime
from typing import Any, Optional

from crypto_newsletter.core.storage.repository import (
    ArticleRepository,
    NewsletterRepository,
)
from crypto_newsletter.newsletter.tasks import generate_newsletter_manual_task
from crypto_newsletter.shared.config.settings import get_settings
from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.web.models import (
    ArticleResponse,
    NewsletterGenerationRequest,
    NewsletterListResponse,
    NewsletterResponse,
    NewsletterUpdateRequest,
    PublisherResponse,
    StatsResponse,
    TaskScheduleRequest,
)
from fastapi import APIRouter, HTTPException, Query, Security
from fastapi.security.api_key import APIKeyHeader

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
    if api_key and hasattr(settings, "api_key") and api_key == settings.api_key:
        return api_key

    # Public endpoints don't require API key
    return None


@router.get("/articles", response_model=list[ArticleResponse])
async def get_articles(
    limit: int = Query(10, description="Maximum number of articles to return", le=100),
    offset: int = Query(0, description="Number of articles to skip"),
    publisher_id: Optional[int] = Query(None, description="Filter by publisher ID"),
    publisher: Optional[str] = Query(None, description="Filter by publisher name"),
    hours_back: Optional[int] = Query(
        None, description="Filter by hours back from now"
    ),
    search: Optional[str] = Query(None, description="Search in title and content"),
    status: Optional[str] = Query("ACTIVE", description="Filter by article status"),
    start_date: Optional[str] = Query(
        None, description="Filter by start date (ISO 8601)"
    ),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO 8601)"),
    order_by: Optional[str] = Query("published_on", description="Order by field"),
    order: Optional[str] = Query("desc", description="Order direction (asc/desc)"),
    api_key: Optional[str] = Security(get_api_key),
) -> list[ArticleResponse]:
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
            articles = await repo.get_articles_with_filters(
                limit=limit,
                offset=offset,
                publisher_id=publisher_id,
                publisher_name=publisher,
                hours_back=hours_back,
                search_query=search,
                status=status,
                start_date=start_date,
                end_date=end_date,
                order_by=order_by,
                order=order,
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
                    body_length=article.get("body_length", 0),
                )
                for article in articles
            ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch articles: {e}")


@router.get("/publishers", response_model=list[PublisherResponse])
async def get_publishers(
    api_key: Optional[str] = Security(get_api_key),
) -> list[PublisherResponse]:
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch publishers: {e}")


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
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {e}")


@router.get("/articles/analysis-ready", response_model=list[ArticleResponse])
async def get_analysis_ready_articles(
    limit: int = Query(10, description="Maximum number of articles to return", le=100),
    offset: int = Query(0, description="Number of articles to skip"),
    publisher_id: Optional[int] = Query(None, description="Filter by publisher ID"),
    min_length: int = Query(2000, description="Minimum content length for analysis"),
    api_key: Optional[str] = Security(get_api_key),
) -> list[ArticleResponse]:
    """
    Get articles that are ready for signal analysis (sufficient content length).

    Args:
        limit: Maximum number of articles to return
        offset: Number of articles to skip for pagination
        publisher_id: Filter by specific publisher
        min_length: Minimum content length required
        api_key: Optional API key for authentication

    Returns:
        List of analysis-ready articles
    """
    try:
        async with get_db_session() as db:
            repo = ArticleRepository(db)

            # Get analysis-ready articles
            articles = await repo.get_analysis_ready_articles(
                limit=limit,
                offset=offset,
                publisher_id=publisher_id,
                min_content_length=min_length,
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
                    body_length=article.get("body_length", 0),
                )
                for article in articles
            ]

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch analysis-ready articles: {e}"
        )


@router.get("/articles/{article_id}")
async def get_article(
    article_id: int,
    api_key: Optional[str] = Security(get_api_key),
) -> dict[str, Any]:
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
                    status_code=404, detail=f"Article with ID {article_id} not found"
                )

            return article

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch article: {e}")


# Webhook endpoint for external triggers (future use)
@router.post("/webhook/trigger-ingest")
async def webhook_trigger_ingest(
    request: TaskScheduleRequest,
    api_key: Optional[str] = Security(get_api_key),
) -> dict[str, Any]:
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
            from crypto_newsletter.core.ingestion.pipeline import (
                ArticleIngestionPipeline,
            )

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
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Synchronous ingestion failed: {e}"
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
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to schedule webhook ingestion: {e}"
            )


# Newsletter endpoints
@router.get("/newsletters", response_model=NewsletterListResponse)
async def get_newsletters(
    limit: int = Query(
        10, description="Maximum number of newsletters to return", le=100
    ),
    offset: int = Query(0, description="Number of newsletters to skip"),
    status: Optional[str] = Query(None, description="Filter by newsletter status"),
    newsletter_type: Optional[str] = Query(
        None, description="Filter by newsletter type (DAILY/WEEKLY)"
    ),
    start_date: Optional[str] = Query(
        None, description="Filter by start date (ISO 8601)"
    ),
    end_date: Optional[str] = Query(None, description="Filter by end date (ISO 8601)"),
    api_key: Optional[str] = Security(get_api_key),
) -> NewsletterListResponse:
    """
    Get list of newsletters with optional filtering.

    Args:
        limit: Maximum number of newsletters to return
        offset: Number of newsletters to skip for pagination
        status: Filter by newsletter status (DRAFT, REVIEW, PUBLISHED, ARCHIVED)
        newsletter_type: Filter by newsletter type (DAILY, WEEKLY)
        start_date: Filter by generation date start (ISO 8601)
        end_date: Filter by generation date end (ISO 8601)
        api_key: Optional API key for authentication

    Returns:
        List of newsletters matching criteria with pagination info
    """
    try:
        async with get_db_session() as db:
            newsletter_repo = NewsletterRepository(db)

            # Get newsletters with filters
            newsletters = await newsletter_repo.get_newsletters_with_filters(
                limit=limit,
                offset=offset,
                status=status,
                newsletter_type=newsletter_type,
                start_date=start_date,
                end_date=end_date,
            )

            # Get total count for pagination
            total_count = await newsletter_repo.count_newsletters_with_filters(
                status=status,
                newsletter_type=newsletter_type,
                start_date=start_date,
                end_date=end_date,
            )

            # Convert to response models
            newsletter_responses = []
            for newsletter in newsletters:
                newsletter_responses.append(
                    NewsletterResponse(
                        id=newsletter.id,
                        title=newsletter.title,
                        content=newsletter.content,
                        summary=newsletter.summary,
                        generation_date=newsletter.generation_date.isoformat(),
                        status=newsletter.status,
                        quality_score=newsletter.quality_score,
                        agent_version=newsletter.agent_version,
                        generation_metadata=newsletter.generation_metadata,
                        published_at=newsletter.published_at.isoformat()
                        if newsletter.published_at
                        else None,
                        created_at=newsletter.created_at.isoformat(),
                        updated_at=newsletter.updated_at.isoformat(),
                    )
                )

            return NewsletterListResponse(
                newsletters=newsletter_responses,
                total_count=total_count,
                page=offset // limit + 1,
                limit=limit,
                has_more=(offset + limit) < total_count,
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve newsletters: {e}"
        )


@router.get("/newsletters/{newsletter_id}", response_model=NewsletterResponse)
async def get_newsletter(
    newsletter_id: int,
    api_key: Optional[str] = Security(get_api_key),
) -> NewsletterResponse:
    """
    Get specific newsletter by ID.

    Args:
        newsletter_id: Newsletter ID to retrieve
        api_key: Optional API key for authentication

    Returns:
        Newsletter details
    """
    try:
        async with get_db_session() as db:
            newsletter_repo = NewsletterRepository(db)

            newsletter = await newsletter_repo.get_newsletter_by_id(newsletter_id)
            if not newsletter:
                raise HTTPException(
                    status_code=404,
                    detail=f"Newsletter with ID {newsletter_id} not found",
                )

            return NewsletterResponse(
                id=newsletter.id,
                title=newsletter.title,
                content=newsletter.content,
                summary=newsletter.summary,
                generation_date=newsletter.generation_date.isoformat(),
                status=newsletter.status,
                quality_score=newsletter.quality_score,
                agent_version=newsletter.agent_version,
                generation_metadata=newsletter.generation_metadata,
                published_at=newsletter.published_at.isoformat()
                if newsletter.published_at
                else None,
                created_at=newsletter.created_at.isoformat(),
                updated_at=newsletter.updated_at.isoformat(),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve newsletter: {e}"
        )


@router.post("/newsletters/generate")
async def generate_newsletter(
    request: NewsletterGenerationRequest,
    api_key: Optional[str] = Security(get_api_key),
) -> dict[str, Any]:
    """
    Trigger newsletter generation.

    Args:
        request: Newsletter generation parameters
        api_key: Optional API key for authentication

    Returns:
        Generation task information
    """
    try:
        # Validate newsletter type
        if request.newsletter_type.upper() not in ["DAILY", "WEEKLY"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid newsletter type: {request.newsletter_type}. Must be DAILY or WEEKLY",
            )

        # Trigger newsletter generation task
        result = generate_newsletter_manual_task.delay(
            newsletter_type=request.newsletter_type.upper(),
            force_generation=request.force_generation,
        )

        return {
            "success": True,
            "task_id": result.id,
            "newsletter_type": request.newsletter_type.upper(),
            "force_generation": request.force_generation,
            "status": "queued",
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger newsletter generation: {e}"
        )


@router.put("/newsletters/{newsletter_id}/status")
async def update_newsletter_status(
    newsletter_id: int,
    request: NewsletterUpdateRequest,
    api_key: Optional[str] = Security(get_api_key),
) -> dict[str, Any]:
    """
    Update newsletter status and other fields.

    Args:
        newsletter_id: Newsletter ID to update
        request: Newsletter update parameters
        api_key: Optional API key for authentication

    Returns:
        Update confirmation
    """
    try:
        async with get_db_session() as db:
            newsletter_repo = NewsletterRepository(db)

            # Check if newsletter exists
            newsletter = await newsletter_repo.get_newsletter_by_id(newsletter_id)
            if not newsletter:
                raise HTTPException(
                    status_code=404,
                    detail=f"Newsletter with ID {newsletter_id} not found",
                )

            # Validate status if provided
            if request.status and request.status not in [
                "DRAFT",
                "REVIEW",
                "PUBLISHED",
                "ARCHIVED",
            ]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {request.status}. Must be DRAFT, REVIEW, PUBLISHED, or ARCHIVED",
                )

            # Update newsletter
            updated_newsletter = await newsletter_repo.update_newsletter(
                newsletter_id=newsletter_id,
                status=request.status,
                title=request.title,
                content=request.content,
                summary=request.summary,
            )

            return {
                "success": True,
                "newsletter_id": newsletter_id,
                "updated_fields": {
                    k: v
                    for k, v in {
                        "status": request.status,
                        "title": request.title,
                        "content": request.content,
                        "summary": request.summary,
                    }.items()
                    if v is not None
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update newsletter: {e}")


@router.delete("/newsletters/{newsletter_id}")
async def delete_newsletter(
    newsletter_id: int,
    api_key: Optional[str] = Security(get_api_key),
) -> dict[str, Any]:
    """
    Delete newsletter by ID.

    Args:
        newsletter_id: Newsletter ID to delete
        api_key: Optional API key for authentication

    Returns:
        Deletion confirmation
    """
    try:
        async with get_db_session() as db:
            newsletter_repo = NewsletterRepository(db)

            # Check if newsletter exists
            newsletter = await newsletter_repo.get_newsletter_by_id(newsletter_id)
            if not newsletter:
                raise HTTPException(
                    status_code=404,
                    detail=f"Newsletter with ID {newsletter_id} not found",
                )

            # Delete newsletter
            await newsletter_repo.delete_newsletter(newsletter_id)

            return {
                "success": True,
                "newsletter_id": newsletter_id,
                "message": "Newsletter deleted successfully",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete newsletter: {e}")
