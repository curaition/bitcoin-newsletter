"""Pydantic models for API requests and responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Request models
class TaskScheduleRequest(BaseModel):
    """Request model for scheduling tasks."""
    limit: Optional[int] = Field(None, description="Maximum number of articles to fetch")
    hours_back: int = Field(4, description="Hours back to look for articles")
    categories: Optional[List[str]] = Field(None, description="Categories to filter by")


class ManualIngestRequest(BaseModel):
    """Request model for manual ingestion."""
    limit: Optional[int] = Field(None, description="Maximum number of articles to fetch")
    hours_back: int = Field(24, description="Hours back to look for articles")
    categories: Optional[List[str]] = Field(None, description="Categories to filter by")


# Response models
class TaskStatusResponse(BaseModel):
    """Response model for task status."""
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
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
    top_publishers: List[Dict[str, Any]]
    top_categories: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str
    service: str
    timestamp: str
    checks: Optional[Dict[str, Any]] = None


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    timestamp: str
    service: str
    environment: str
    database: Dict[str, Any]
    celery: Dict[str, Any]
