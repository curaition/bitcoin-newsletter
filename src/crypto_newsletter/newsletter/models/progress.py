"""Progress tracking models for newsletter generation."""

from datetime import datetime
from typing import Optional

from crypto_newsletter.shared.models.base import Base
from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, DateTime, Float, String


class NewsletterGenerationProgress(Base):
    """Track progress of newsletter generation tasks."""

    __tablename__ = "newsletter_generation_progress"

    task_id: str = Column(String, primary_key=True)
    current_step: str = Column(
        String, nullable=False
    )  # "selection", "synthesis", "writing", "storage"
    step_progress: float = Column(Float, default=0.0)  # 0.0 to 1.0
    overall_progress: float = Column(Float, default=0.0)  # 0.0 to 1.0

    # Agent quality metrics
    step_details: dict = Column(JSON, default=dict)
    intermediate_results: dict = Column(JSON, default=dict)
    quality_metrics: dict = Column(JSON, default=dict)

    # Article context
    articles_being_processed: list = Column(JSON, default=list)
    estimated_completion: datetime = Column(DateTime, nullable=True)

    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    status: str = Column(
        String, default="in_progress"
    )  # "in_progress", "complete", "failed"


# Quality validation classes for agent outputs
class SelectionQuality(BaseModel):
    """Quality metrics for story selection."""

    overall_score: float = Field(
        ge=0.0, le=1.0, description="Overall selection quality score"
    )
    urls_available: int = Field(
        ge=0, description="Number of articles with URLs available"
    )
    signal_utilization: float = Field(
        ge=0.0, le=1.0, description="Average signal strength of selected stories"
    )
    unique_insights: int = Field(
        ge=0, description="Number of unique insights identified"
    )
    coverage_breadth: float = Field(
        ge=0.0, le=1.0, description="Breadth of topic coverage"
    )


class SynthesisQuality(BaseModel):
    """Quality metrics for synthesis."""

    overall_score: float = Field(
        ge=0.0, le=1.0, description="Overall synthesis quality score"
    )
    uniqueness_score: float = Field(
        ge=0.0, le=1.0, description="Uniqueness of insights generated"
    )
    pattern_strength: float = Field(
        ge=0.0, le=1.0, description="Strength of identified patterns"
    )
    connection_count: int = Field(
        ge=0, description="Number of cross-story connections found"
    )
    theme_coherence: float = Field(
        ge=0.0, le=1.0, description="Coherence of identified themes"
    )


class WritingQuality(BaseModel):
    """Quality metrics for newsletter content."""

    word_count: int = Field(ge=0, description="Total word count of newsletter")
    citation_count: int = Field(
        ge=0, description="Number of article citations included"
    )
    overall_score: float = Field(
        ge=0.0, le=1.0, description="Overall writing quality score"
    )
    has_proper_citations: bool = Field(
        description="Whether newsletter has adequate citations"
    )
    readability_score: float = Field(
        ge=0.0, le=1.0, description="Content readability score"
    )
    actionability_score: float = Field(
        ge=0.0, le=1.0, description="How actionable the insights are"
    )


class GenerationMetrics(BaseModel):
    """Complete generation metrics for a newsletter task."""

    task_id: str = Field(description="Celery task ID")
    start_time: datetime = Field(description="Generation start time")
    end_time: Optional[datetime] = Field(description="Generation end time")
    total_duration_seconds: Optional[float] = Field(description="Total generation time")

    # Article processing metrics
    articles_processed: int = Field(ge=0, description="Number of articles processed")
    articles_selected: int = Field(ge=0, description="Number of articles selected")

    # Quality metrics
    selection_quality: Optional[SelectionQuality] = Field(
        description="Story selection quality"
    )
    synthesis_quality: Optional[SynthesisQuality] = Field(
        description="Synthesis quality"
    )
    writing_quality: Optional[WritingQuality] = Field(description="Writing quality")

    # Cost and performance
    total_cost_usd: Optional[float] = Field(description="Total API cost in USD")
    token_usage: Optional[int] = Field(description="Total tokens used")

    # Final newsletter info
    newsletter_id: Optional[int] = Field(description="Generated newsletter ID")
    final_quality_score: Optional[float] = Field(
        description="Final overall quality score"
    )
