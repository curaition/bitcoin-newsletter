"""Pydantic models for signal detection."""


from pydantic import BaseModel, Field


class WeakSignal(BaseModel):
    """A subtle market indicator not explicitly stated in mainstream coverage."""

    signal_type: str = Field(
        description="Category of weak signal (e.g., 'institutional_behavior', 'regulatory_shift', 'technology_adoption')"
    )
    description: str = Field(
        description="Clear, specific description of the signal detected"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in signal validity (0.0-1.0)"
    )
    implications: str = Field(
        description="Specific potential market implications and timeframe"
    )
    evidence: list[str] = Field(
        min_items=1,
        description="Direct quotes or specific facts from article supporting this signal",
    )
    timeframe: str = Field(
        description="Expected development timeframe (immediate/short-term/medium-term/long-term)"
    )


class PatternAnomaly(BaseModel):
    """Deviation from expected cryptocurrency market patterns."""

    expected_pattern: str = Field(
        description="What pattern was historically expected in this scenario"
    )
    observed_pattern: str = Field(
        description="What was actually observed in the article content"
    )
    deviation_significance: float = Field(
        ge=0.0, le=1.0, description="How significant this deviation is (0.0-1.0)"
    )
    historical_context: str = Field(
        description="Brief context of how this compares to historical patterns"
    )
    potential_causes: list[str] = Field(
        description="Possible explanations for why this anomaly occurred"
    )


class AdjacentConnection(BaseModel):
    """Connection between crypto elements and external domains."""

    crypto_element: str = Field(
        description="The specific crypto element being connected (coin, protocol, concept)"
    )
    external_domain: str = Field(
        description="External domain (technology, finance, culture, politics, regulation)"
    )
    connection_type: str = Field(
        description="Nature of the connection (adoption, integration, influence, correlation)"
    )
    relevance: float = Field(
        ge=0.0,
        le=1.0,
        description="How relevant this connection is to crypto markets (0.0-1.0)",
    )
    opportunity_description: str = Field(
        description="Specific opportunity or risk this connection suggests"
    )
    development_indicators: list[str] = Field(
        description="Key indicators to watch for further development of this connection"
    )
