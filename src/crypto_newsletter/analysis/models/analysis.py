"""Pydantic models for content analysis results."""


from pydantic import BaseModel, Field

from .signals import AdjacentConnection, PatternAnomaly, WeakSignal


class ContentAnalysis(BaseModel):
    """Complete analysis result for a cryptocurrency article."""

    # Core Analysis
    sentiment: str = Field(
        description="Overall market sentiment: POSITIVE, NEGATIVE, NEUTRAL, or MIXED"
    )
    impact_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Potential market impact of this article's content (0.0-1.0)",
    )
    summary: str = Field(
        description="Concise 2-3 sentence summary of key insights and implications"
    )
    context: str = Field(
        description="Important contextual information for understanding the analysis"
    )

    # Signal Detection Results
    weak_signals: list[WeakSignal] = Field(
        description="Subtle market indicators detected in the content"
    )
    pattern_anomalies: list[PatternAnomaly] = Field(
        description="Deviations from expected market patterns"
    )
    adjacent_connections: list[AdjacentConnection] = Field(
        description="Connections between crypto and external domains"
    )
    narrative_gaps: list[str] = Field(
        description="Missing perspectives or overlooked angles in the coverage"
    )
    edge_indicators: list[str] = Field(
        description="Outlier behaviors or unusual market signals noted"
    )

    # Quality Metrics
    analysis_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall confidence in the analysis quality (0.0-1.0)",
    )
    signal_strength: float = Field(
        ge=0.0, le=1.0, description="Overall strength of detected signals (0.0-1.0)"
    )
    uniqueness_score: float = Field(
        ge=0.0,
        le=1.0,
        description="How unique these insights are vs mainstream coverage (0.0-1.0)",
    )
