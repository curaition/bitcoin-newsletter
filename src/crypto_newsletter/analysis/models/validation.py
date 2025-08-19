"""Pydantic models for signal validation results."""

from typing import Optional

from pydantic import BaseModel, Field

from .signals import WeakSignal


class ResearchSource(BaseModel):
    """External research source used for validation."""

    source_url: str = Field(description="URL of the research source")
    source_type: str = Field(
        description="Type: news, academic, data, industry_report, social_media"
    )
    authority_level: str = Field(description="Source credibility: HIGH, MEDIUM, LOW")
    relevance: float = Field(
        ge=0.0, le=1.0, description="Relevance to signal being validated (0.0-1.0)"
    )
    key_information: str = Field(
        description="Key information extracted from this source"
    )
    publication_date: Optional[str] = Field(
        default=None, description="Publication date if available (YYYY-MM-DD format)"
    )


class ValidationResult(BaseModel):
    """Validation result for a single signal."""

    signal_id: str = Field(
        description="Reference identifier for the signal being validated"
    )
    validation_status: str = Field(
        description="VALIDATED, CONTRADICTED, INCONCLUSIVE, or INSUFFICIENT_DATA"
    )
    supporting_evidence: list[str] = Field(
        description="Specific evidence supporting the signal"
    )
    contradicting_evidence: list[str] = Field(
        description="Specific evidence contradicting the signal"
    )
    additional_context: str = Field(
        description="Additional relevant context discovered during research"
    )
    research_sources: list[ResearchSource] = Field(
        description="External sources used in validation"
    )
    confidence_adjustment: float = Field(
        ge=-1.0, le=1.0, description="Adjustment to original confidence (-1.0 to +1.0)"
    )
    research_quality: float = Field(
        ge=0.0, le=1.0, description="Quality of research sources found (0.0-1.0)"
    )


class SignalValidation(BaseModel):
    """Complete validation results for all signals."""

    validation_results: list[ValidationResult] = Field(
        description="Individual validation results for each signal"
    )
    cross_signal_insights: list[str] = Field(
        description="Insights discovered by comparing multiple signals"
    )
    additional_signals: list[WeakSignal] = Field(
        description="New signals discovered during external research"
    )
    research_cost: float = Field(description="Estimated cost of research in USD")
    research_summary: str = Field(
        description="Summary of overall research findings and methodology"
    )
