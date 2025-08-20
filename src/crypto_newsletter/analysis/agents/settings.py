"""Analysis agent settings and configuration."""

from typing import Optional

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class AnalysisSettings(BaseSettings):
    """Settings for analysis agents."""

    model_config = ConfigDict(extra="ignore")

    # LLM Configuration
    content_analysis_model: str = Field(
        default="gemini-2.0-flash-exp", alias="CONTENT_ANALYSIS_AGENT_MODEL"
    )
    signal_validation_model: str = Field(
        default="gemini-2.0-flash-exp", alias="SIGNAL_VALIDATION_AGENT_MODEL"
    )

    # API Keys
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")

    # MCP Configuration
    tavily_mcp_url: str = Field(
        default="https://api.tavily.com/mcp", alias="TAVILY_MCP_URL"
    )

    # Cost Management
    daily_analysis_budget: float = Field(default=50.0, alias="DAILY_ANALYSIS_BUDGET")
    max_cost_per_article: float = Field(default=0.25, alias="MAX_COST_PER_ARTICLE")
    max_searches_per_validation: int = Field(
        default=5, alias="MAX_SEARCHES_PER_VALIDATION"
    )

    # Quality Thresholds
    min_content_length: int = Field(default=2000, alias="MIN_CONTENT_LENGTH")
    min_signal_confidence: float = Field(default=0.3, alias="MIN_SIGNAL_CONFIDENCE")

    # Testing
    testing: bool = Field(default=False, alias="TESTING")


# Global settings instance
analysis_settings = AnalysisSettings()
