"""Pydantic models for API requests and responses."""

from typing import Any, Optional

from pydantic import BaseModel, Field


# Request models
class TaskScheduleRequest(BaseModel):
    """Request model for scheduling tasks."""

    limit: Optional[int] = Field(
        None, description="Maximum number of articles to fetch"
    )
    hours_back: int = Field(4, description="Hours back to look for articles")
    categories: Optional[list[str]] = Field(None, description="Categories to filter by")


class ManualIngestRequest(BaseModel):
    """Request model for manual ingestion."""

    limit: Optional[int] = Field(
        None, description="Maximum number of articles to fetch"
    )
    hours_back: int = Field(24, description="Hours back to look for articles")
    categories: Optional[list[str]] = Field(None, description="Categories to filter by")


# Response models
class TaskStatusResponse(BaseModel):
    """Response model for task status."""

    task_id: str
    status: str
    result: Optional[dict[str, Any]] = None
    date_done: Optional[str] = None
    traceback: Optional[str] = None


class ArticleResponse(BaseModel):
    """Response model for article data."""

    id: int
    external_id: int
    title: str
    subtitle: Optional[str] = None
    url: str
    published_on: Optional[str] = None
    publisher_id: Optional[int] = None
    language: Optional[str] = None
    status: str


class PublisherResponse(BaseModel):
    """Response model for publisher data."""

    id: int
    source_id: int
    name: str
    source_key: str
    url: Optional[str] = None
    lang: Optional[str] = None
    status: Optional[str] = None


class CategoryResponse(BaseModel):
    """Response model for category data."""

    id: int
    category_id: int
    name: str
    category: str


class StatsResponse(BaseModel):
    """Response model for statistics."""

    total_articles: int
    recent_articles: int
    total_publishers: int
    total_categories: int
    top_publishers: list[dict[str, Any]]
    top_categories: list[dict[str, Any]]


class HealthResponse(BaseModel):
    """Response model for health checks."""

    status: str
    service: str
    timestamp: str
    checks: Optional[dict[str, Any]] = None


class SystemStatusResponse(BaseModel):
    """Response model for system status."""

    timestamp: str
    service: str
    environment: str
    database: dict[str, Any]
    celery: dict[str, Any]


# Newsletter models
class NewsletterResponse(BaseModel):
    """Response model for newsletter data."""

    id: int
    title: str
    content: str
    summary: Optional[str] = None
    generation_date: str
    status: str
    quality_score: Optional[float] = None
    agent_version: Optional[str] = None
    generation_metadata: Optional[dict[str, Any]] = None
    published_at: Optional[str] = None
    created_at: str
    updated_at: str


class NewsletterListResponse(BaseModel):
    """Response model for newsletter list with pagination."""

    newsletters: list[NewsletterResponse]
    total_count: int
    page: int
    limit: int
    has_more: bool


class NewsletterGenerationRequest(BaseModel):
    """Request model for newsletter generation."""

    newsletter_type: str = Field(
        default="DAILY", description="Type of newsletter to generate (DAILY or WEEKLY)"
    )
    force_generation: bool = Field(
        default=False, description="Force generation even if conditions not met"
    )


class NewsletterUpdateRequest(BaseModel):
    """Request model for newsletter updates."""

    status: Optional[str] = Field(
        None, description="Newsletter status (DRAFT, REVIEW, PUBLISHED, ARCHIVED)"
    )
    title: Optional[str] = Field(None, description="Newsletter title")
    content: Optional[str] = Field(None, description="Newsletter content")
    summary: Optional[str] = Field(None, description="Newsletter summary")


# Admin-specific newsletter models
class NewsletterStatsResponse(BaseModel):
    """Response model for newsletter statistics."""

    period: str
    total_newsletters: int
    newsletter_types: dict[str, int]
    status_breakdown: dict[str, int]
    quality_metrics: dict[str, Any]
    cost_metrics: dict[str, Any]
    recent_newsletters: list[dict[str, Any]]
    timestamp: str


class AdminNewsletterResponse(BaseModel):
    """Response model for admin newsletter data with enhanced metadata."""

    id: int
    title: str
    status: str
    generation_date: str
    quality_score: Optional[float] = None
    agent_version: Optional[str] = None
    created_at: str
    updated_at: str
    newsletter_type: Optional[str] = None
    generation_cost: Optional[float] = None
    processing_time: Optional[float] = None
    articles_processed: Optional[int] = None


class AdminNewsletterListResponse(BaseModel):
    """Response model for admin newsletter list."""

    newsletters: list[AdminNewsletterResponse]
    count: int
    filters_applied: dict[str, Any]
    timestamp: str


class NewsletterGenerationResponse(BaseModel):
    """Response model for newsletter generation requests."""

    success: bool
    task_id: str
    newsletter_type: str
    force_generation: bool
    status: str
    message: str
    timestamp: str


class NewsletterStatusUpdateResponse(BaseModel):
    """Response model for newsletter status updates."""

    success: bool
    newsletter_id: int
    previous_status: str
    new_status: str
    updated_fields: dict[str, Any]
    published_at: Optional[str] = None
    timestamp: str


class NewsletterDeletionResponse(BaseModel):
    """Response model for newsletter deletion."""

    success: bool
    deleted_newsletter: dict[str, Any]
    message: str
    timestamp: str


# Newsletter health and monitoring models
class NewsletterHealthResponse(BaseModel):
    """Response model for newsletter system health."""

    overall_status: str
    timestamp: str
    checks: dict[str, Any]


class NewsletterGenerationMetrics(BaseModel):
    """Response model for newsletter generation metrics."""

    total_count: int
    success_count: int
    success_rate: float
    average_quality_score: float
    average_generation_cost: float
    average_processing_time: float
    last_generated: Optional[str] = None


class NewsletterPipelineMetrics(BaseModel):
    """Response model for newsletter pipeline metrics."""

    analyzed_articles_24h: int
    minimum_required: int
    pipeline_ready: bool


class NewsletterMonitoringResponse(BaseModel):
    """Response model for newsletter monitoring data."""

    status: str
    timestamp: str
    issues: list[str]
    metrics: dict[str, Any]


# Task-related newsletter models
class NewsletterTaskResponse(BaseModel):
    """Response model for newsletter task operations."""

    success: bool
    task_id: Optional[str] = None
    newsletter_id: Optional[int] = None
    status: str
    message: str
    timestamp: str
    error: Optional[str] = None


# Newsletter content and validation models
class NewsletterContentSummary(BaseModel):
    """Response model for newsletter content summary."""

    id: int
    title: str
    summary: Optional[str] = None
    newsletter_type: str
    status: str
    quality_score: Optional[float] = None
    generation_date: str
    word_count: Optional[int] = None
    estimated_read_time: Optional[int] = None


class NewsletterValidationResponse(BaseModel):
    """Response model for newsletter validation."""

    is_valid: bool
    validation_errors: list[str]
    validation_warnings: list[str]
    quality_score: Optional[float] = None
    content_metrics: dict[str, Any]
    timestamp: str


class NewsletterPreviewResponse(BaseModel):
    """Response model for newsletter preview."""

    id: int
    title: str
    executive_summary: list[str]
    content_preview: str  # First 500 characters
    status: str
    generation_date: str
    newsletter_type: str
    quality_score: Optional[float] = None
    estimated_read_time: Optional[int] = None


# Bulk operations models
class BulkNewsletterOperationRequest(BaseModel):
    """Request model for bulk newsletter operations."""

    newsletter_ids: list[int] = Field(
        description="List of newsletter IDs to operate on"
    )
    operation: str = Field(
        description="Operation to perform (delete, archive, publish)"
    )
    confirm: bool = Field(
        default=False, description="Confirmation flag for destructive operations"
    )


class BulkNewsletterOperationResponse(BaseModel):
    """Response model for bulk newsletter operations."""

    success: bool
    operation: str
    total_requested: int
    successful_operations: int
    failed_operations: int
    results: list[dict[str, Any]]
    timestamp: str


# Newsletter search and filtering models
class NewsletterSearchRequest(BaseModel):
    """Request model for newsletter search."""

    query: Optional[str] = Field(None, description="Search query for title and content")
    status: Optional[list[str]] = Field(None, description="Filter by status list")
    newsletter_type: Optional[list[str]] = Field(
        None, description="Filter by newsletter type list"
    )
    date_from: Optional[str] = Field(None, description="Filter from date (ISO 8601)")
    date_to: Optional[str] = Field(None, description="Filter to date (ISO 8601)")
    min_quality_score: Optional[float] = Field(
        None, description="Minimum quality score filter"
    )
    limit: int = Field(default=20, description="Maximum results to return")
    offset: int = Field(default=0, description="Results offset for pagination")


class NewsletterSearchResponse(BaseModel):
    """Response model for newsletter search results."""

    newsletters: list[NewsletterContentSummary]
    total_matches: int
    search_params: NewsletterSearchRequest
    facets: dict[str, dict[str, int]]  # Faceted search results
    timestamp: str


# Newsletter analytics models
class NewsletterAnalyticsResponse(BaseModel):
    """Response model for newsletter analytics."""

    period: str
    total_newsletters: int
    generation_trends: dict[str, list[dict[str, Any]]]
    quality_trends: dict[str, list[dict[str, Any]]]
    cost_trends: dict[str, list[dict[str, Any]]]
    performance_metrics: dict[str, Any]
    top_performing_newsletters: list[NewsletterContentSummary]
    timestamp: str
