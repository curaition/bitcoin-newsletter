"""Pydantic models for newsletter generation agents."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class StoryScore(BaseModel):
    """Score and metadata for a selected story."""
    
    article_id: int = Field(description="Article database ID")
    title: str = Field(description="Article title")
    publisher: str = Field(description="Publisher name")
    signal_strength: float = Field(description="Overall signal strength (0-1)")
    uniqueness_score: float = Field(description="Content uniqueness (0-1)")
    relevance_score: float = Field(description="Market relevance (0-1)")
    selection_reasoning: str = Field(description="Why this story was selected")
    key_signals: List[str] = Field(description="Primary signals detected")


class StorySelection(BaseModel):
    """Result of story selection agent."""
    
    selection_date: datetime = Field(description="Date of story selection")
    total_articles_reviewed: int = Field(description="Total articles considered")
    selected_stories: List[StoryScore] = Field(description="Top selected stories with scores")
    rejected_highlights: List[StoryScore] = Field(description="Notable stories not selected and why")
    selection_themes: List[str] = Field(description="Common themes across selected stories")
    coverage_gaps: List[str] = Field(description="Important topics not covered in selection")


class PatternInsight(BaseModel):
    """Identified pattern across multiple stories."""
    
    pattern_type: str = Field(description="Type of pattern identified")
    confidence: float = Field(description="Confidence in pattern (0-1)")
    description: str = Field(description="Detailed pattern description")
    supporting_stories: List[int] = Field(description="Article IDs supporting this pattern")
    implications: List[str] = Field(description="What this pattern suggests")
    timeline: str = Field(description="Expected timeline for pattern development")


class CrossStoryConnection(BaseModel):
    """Connection identified between multiple stories."""
    
    connection_type: str = Field(description="Type of connection (causal, thematic, etc.)")
    connected_articles: List[int] = Field(description="Article IDs in this connection")
    connection_strength: float = Field(description="Strength of connection (0-1)")
    synthesis_insight: str = Field(description="Insight from connecting these stories")
    market_implications: List[str] = Field(description="Market implications of this connection")


class NewsletterSynthesis(BaseModel):
    """Result of synthesis agent."""
    
    synthesis_date: datetime = Field(description="Date of synthesis")
    primary_themes: List[str] = Field(description="3-5 major themes across all stories")
    pattern_insights: List[PatternInsight] = Field(description="Key patterns identified")
    cross_story_connections: List[CrossStoryConnection] = Field(description="Connections between stories")
    market_narrative: str = Field(description="Overarching market narrative (200-300 words)")
    adjacent_implications: List[str] = Field(description="Cross-domain implications")
    forward_indicators: List[str] = Field(description="What to watch for next")
    synthesis_confidence: float = Field(description="Overall synthesis confidence (0-1)")


class NewsletterContent(BaseModel):
    """Final newsletter content from writer agent."""
    
    title: str = Field(description="Compelling newsletter title")
    executive_summary: List[str] = Field(description="3-4 key takeaways for busy readers")
    main_analysis: str = Field(description="Primary analysis section (800-1200 words)")
    pattern_spotlight: str = Field(description="Deep dive on one major pattern (300-400 words)")
    adjacent_watch: str = Field(description="Cross-domain developments to monitor (200-300 words)")
    signal_radar: str = Field(description="Weak signals for future monitoring (100-150 words)")
    action_items: List[str] = Field(description="Specific takeaways readers can act upon")
    source_citations: List[str] = Field(description="Links to original articles and key sources")
    estimated_read_time: int = Field(description="Estimated read time in minutes")
    editorial_quality_score: float = Field(description="Self-assessed quality (0-1)")
