# Newsletter Generation Agents System
## Sub-PRD 2: PydanticAI Newsletter Creation Pipeline

### Executive Summary
Implement a comprehensive PydanticAI agent system for automated newsletter generation, including story selection, synthesis, and editorial writing agents. This system transforms analyzed articles into high-quality daily and weekly newsletters with unique insights and strategic perspectives.

---

## 1. Product Overview

### Objective
Create a multi-agent newsletter generation system that selects top stories, synthesizes patterns across articles, and produces publication-ready newsletter content with editorial quality and unique market insights.

### Agent Architecture
```
Daily Articles → Story Selection Agent → Synthesis Agent → Newsletter Writer Agent → Published Newsletter
                      ↓                    ↓                    ↓
                 Top 5-8 Stories    Cross-Story Patterns    Editorial Content
```

---

## 2. Agent Specifications

### 2.1 Story Selection Agent
```python
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from typing import List, Optional
from datetime import datetime

class StoryScore(BaseModel):
    article_id: int = Field(description="Article database ID")
    title: str = Field(description="Article title")
    publisher: str = Field(description="Publisher name")
    signal_strength: float = Field(description="Overall signal strength (0-1)")
    uniqueness_score: float = Field(description="Content uniqueness (0-1)")
    relevance_score: float = Field(description="Market relevance (0-1)")
    selection_reasoning: str = Field(description="Why this story was selected")
    key_signals: List[str] = Field(description="Primary signals detected")

class StorySelection(BaseModel):
    selection_date: datetime = Field(description="Date of story selection")
    total_articles_reviewed: int = Field(description="Total articles considered")
    selected_stories: List[StoryScore] = Field(description="Top selected stories with scores")
    rejected_highlights: List[StoryScore] = Field(description="Notable stories not selected and why")
    selection_themes: List[str] = Field(description="Common themes across selected stories")
    coverage_gaps: List[str] = Field(description="Important topics not covered in selection")

story_selection_agent = Agent(
    'gemini-2.5-flash',
    result_type=StorySelection,
    system_prompt='''You are an expert editorial curator for a crypto newsletter focused on signal detection and emerging patterns. Your role is to select the 5-8 most revealing stories from the past 24 hours that best demonstrate emerging trends and adjacent possibilities.

SELECTION CRITERIA (in priority order):
1. **Signal Strength**: Stories with strong weak signals or pattern anomalies (>0.6)
2. **Uniqueness**: Content not widely covered by mainstream crypto media (>0.7)
3. **Cross-Domain Relevance**: Stories with adjacent connections to other sectors
4. **Pattern Emergence**: Stories that reveal emerging trends or market shifts
5. **Actionable Intelligence**: Stories that provide forward-looking insights

QUALITY THRESHOLDS:
- Minimum signal_strength: 0.6
- Minimum uniqueness_score: 0.7
- Minimum analysis_confidence: 0.75
- Maximum selected stories: 8
- Minimum selected stories: 3

EDITORIAL PERSPECTIVE:
Focus on stories that help readers understand not just what happened, but what it means for the future. Prioritize stories that reveal market dynamics, regulatory shifts, technological developments, and cross-industry implications that mainstream coverage misses.

Provide clear reasoning for each selection and rejection. Identify thematic connections across selected stories and note any important coverage gaps.'''
)
```

### 2.2 Synthesis Agent
```python
class PatternInsight(BaseModel):
    pattern_type: str = Field(description="Type of pattern identified")
    confidence: float = Field(description="Confidence in pattern (0-1)")
    description: str = Field(description="Detailed pattern description")
    supporting_stories: List[int] = Field(description="Article IDs supporting this pattern")
    implications: List[str] = Field(description="What this pattern suggests")
    timeline: str = Field(description="Expected timeline for pattern development")

class CrossStoryConnection(BaseModel):
    connection_type: str = Field(description="Type of connection (causal, thematic, etc.)")
    connected_articles: List[int] = Field(description="Article IDs in this connection")
    connection_strength: float = Field(description="Strength of connection (0-1)")
    synthesis_insight: str = Field(description="Insight from connecting these stories")
    market_implications: List[str] = Field(description="Market implications of this connection")

class NewsletterSynthesis(BaseModel):
    synthesis_date: datetime = Field(description="Date of synthesis")
    primary_themes: List[str] = Field(description="3-5 major themes across all stories")
    pattern_insights: List[PatternInsight] = Field(description="Key patterns identified")
    cross_story_connections: List[CrossStoryConnection] = Field(description="Connections between stories")
    market_narrative: str = Field(description="Overarching market narrative (200-300 words)")
    adjacent_implications: List[str] = Field(description="Cross-domain implications")
    forward_indicators: List[str] = Field(description="What to watch for next")
    synthesis_confidence: float = Field(description="Overall synthesis confidence (0-1)")

synthesis_agent = Agent(
    'gemini-2.5-flash',
    result_type=NewsletterSynthesis,
    system_prompt='''You are an expert crypto market synthesist who identifies patterns and connections across multiple news stories and signal analyses. Your role is to weave together individual insights into coherent themes that reveal larger market dynamics.

SYNTHESIS APPROACH:
1. **Pattern Recognition**: Identify recurring themes, signals, and anomalies across stories
2. **Causal Analysis**: Understand how stories connect and influence each other
3. **Market Narrative**: Develop a coherent story about what's happening in the market
4. **Forward Projection**: Identify what these patterns suggest for future developments
5. **Adjacent Connections**: Find implications beyond crypto/blockchain space

ANALYTICAL FRAMEWORK:
- Look for convergent signals across different stories
- Identify contradictions or tensions that reveal market uncertainty
- Connect technical developments to regulatory, institutional, and market trends
- Find patterns that mainstream analysis typically misses
- Synthesize insights that provide unique market intelligence

OUTPUT REQUIREMENTS:
- Primary themes should be specific and actionable, not generic
- Pattern insights must be supported by evidence from multiple stories
- Market narrative should be compelling and unique
- Forward indicators should be specific and measurable
- Maintain high synthesis confidence (>0.75) by grounding insights in data

Focus on synthesis that helps readers understand the bigger picture and make better decisions.'''
)
```

### 2.3 Newsletter Writer Agent
```python
class NewsletterContent(BaseModel):
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

newsletter_writer_agent = Agent(
    'gemini-2.5-flash',
    result_type=NewsletterContent,
    system_prompt='''You are an expert crypto newsletter writer who transforms signal analysis and synthesis into compelling, actionable content. Your voice is authoritative yet accessible, providing unique insights that help readers understand not just what's happening, but what it means and what to watch for next.

EDITORIAL VOICE:
- Authoritative but not arrogant
- Analytical but accessible
- Forward-looking and strategic
- Focused on actionable intelligence
- Unique perspective that differs from mainstream crypto media

CONTENT STRUCTURE:
1. **Executive Summary**: 3-4 bullet points capturing key insights
2. **Main Analysis**: Deep dive into primary themes with supporting evidence
3. **Pattern Spotlight**: Detailed analysis of one significant pattern
4. **Adjacent Watch**: Cross-domain developments readers should monitor
5. **Signal Radar**: Weak signals worth tracking for future relevance
6. **Action Items**: Specific, actionable takeaways

QUALITY STANDARDS:
- Provide insights not available elsewhere (>85% unique content)
- Support all claims with evidence from analyzed articles
- Maintain professional tone while being engaging
- Include specific, measurable forward-looking indicators
- Ensure content is immediately actionable for readers
- Target 8-12 minute read time for busy professionals

EDITORIAL GUIDELINES:
- Lead with the most important insight
- Use data and specific examples to support arguments
- Avoid crypto jargon without explanation
- Connect developments to broader market and technology trends
- End sections with clear implications or actions
- Maintain objectivity while providing clear perspective'''
)
```

---

## 3. Agent Integration System

### 3.1 Newsletter Generation Orchestrator
```python
class NewsletterOrchestrator:
    """Orchestrates the multi-agent newsletter generation workflow."""

    def __init__(self):
        self.story_agent = story_selection_agent
        self.synthesis_agent = synthesis_agent
        self.writer_agent = newsletter_writer_agent

    async def generate_daily_newsletter(
        self,
        articles: List[Dict],
        newsletter_type: str = "DAILY"
    ) -> Dict[str, Any]:
        """Complete daily newsletter generation workflow."""

        try:
            # Step 1: Story Selection
            logger.info(f"Starting story selection for {len(articles)} articles")

            formatted_articles = format_articles_for_selection(articles)
            selection_result = await self.story_agent.run(formatted_articles)

            if len(selection_result.data.selected_stories) < 3:
                raise InsufficientContentException("Not enough quality stories selected")

            # Step 2: Synthesis
            logger.info(f"Synthesizing {len(selection_result.data.selected_stories)} selected stories")

            synthesis_input = format_selection_for_synthesis(
                selection_result.data, articles
            )
            synthesis_result = await self.synthesis_agent.run(synthesis_input)

            # Step 3: Newsletter Writing
            logger.info("Generating newsletter content")

            writing_input = format_synthesis_for_writing(
                synthesis_result.data, selection_result.data
            )
            newsletter_result = await self.writer_agent.run(writing_input)

            # Calculate costs and metadata
            total_cost = calculate_generation_cost([
                selection_result.usage(),
                synthesis_result.usage(),
                newsletter_result.usage()
            ])

            return {
                "success": True,
                "newsletter_content": newsletter_result.data,
                "story_selection": selection_result.data,
                "synthesis": synthesis_result.data,
                "generation_metadata": {
                    "articles_reviewed": len(articles),
                    "stories_selected": len(selection_result.data.selected_stories),
                    "generation_cost": total_cost,
                    "quality_score": newsletter_result.data.editorial_quality_score
                }
            }

        except Exception as e:
            logger.error(f"Newsletter generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "requires_manual_review": True
            }

# Global orchestrator instance
newsletter_orchestrator = NewsletterOrchestrator()
```

---

## 4. Data Formatting Functions

### 4.1 Article Formatting for Agents
```python
def format_articles_for_selection(articles: List[Dict]) -> str:
    """Format analyzed articles for story selection agent."""

    formatted_articles = []
    for article in articles:
        article_summary = f"""
ARTICLE ID: {article['id']}
TITLE: {article['title']}
PUBLISHER: {article['publisher']}
PUBLISHED: {article['published_at']}
SIGNAL STRENGTH: {article.get('signal_strength', 0):.2f}
UNIQUENESS SCORE: {article.get('uniqueness_score', 0):.2f}
ANALYSIS CONFIDENCE: {article.get('analysis_confidence', 0):.2f}

KEY SIGNALS:
{format_signals_list(article.get('weak_signals', []))}

PATTERN ANOMALIES:
{format_patterns_list(article.get('pattern_anomalies', []))}

ADJACENT CONNECTIONS:
{format_connections_list(article.get('adjacent_connections', []))}

CONTENT PREVIEW:
{article['body'][:500]}...

---
"""
        formatted_articles.append(article_summary)

    return f"""
STORY SELECTION BRIEFING
Date: {datetime.now().strftime('%Y-%m-%d')}
Total Articles for Review: {len(articles)}

Please select the 5-8 most revealing stories that best demonstrate emerging patterns and provide unique market intelligence.

ARTICLES FOR REVIEW:
{''.join(formatted_articles)}

Focus on stories with strong signals, unique insights, and cross-domain implications that mainstream crypto media typically misses.
"""

def format_selection_for_synthesis(
    selection: StorySelection,
    full_articles: List[Dict]
) -> str:
    """Format story selection results for synthesis agent."""

    selected_article_details = []
    for story in selection.selected_stories:
        # Get full article details
        full_article = next(
            (a for a in full_articles if a['id'] == story.article_id),
            None
        )

        if full_article:
            detail = f"""
SELECTED STORY: {story.title}
Publisher: {story.publisher}
Selection Reasoning: {story.selection_reasoning}
Key Signals: {', '.join(story.key_signals)}

Full Analysis:
- Weak Signals: {format_signals_list(full_article.get('weak_signals', []))}
- Pattern Anomalies: {format_patterns_list(full_article.get('pattern_anomalies', []))}
- Adjacent Connections: {format_connections_list(full_article.get('adjacent_connections', []))}

Content Summary: {full_article['body'][:800]}...

---
"""
            selected_article_details.append(detail)

    return f"""
SYNTHESIS BRIEFING
Date: {selection.selection_date.strftime('%Y-%m-%d')}
Stories Selected: {len(selection.selected_stories)}
Selection Themes: {', '.join(selection.selection_themes)}

SELECTED STORIES FOR SYNTHESIS:
{''.join(selected_article_details)}

EDITORIAL CONTEXT:
Coverage Gaps: {', '.join(selection.coverage_gaps)}

Please identify patterns, connections, and insights across these stories that reveal larger market dynamics and forward-looking intelligence.
"""
```

---

## 5. Implementation Timeline

### Week 1: Core Agents
- **Days 1-2**: Implement Story Selection Agent with testing
- **Days 3-4**: Build Synthesis Agent and integration
- **Days 5-7**: Create Newsletter Writer Agent and orchestrator

### Week 2: Integration & Testing
- **Days 1-3**: Build data formatting and agent integration
- **Days 4-5**: Test complete workflow with sample data
- **Days 6-7**: Optimize prompts and quality validation

### Week 3: Production Deployment
- **Days 1-2**: Deploy agents to production environment
- **Days 3-7**: Test with real analyzed articles and refine

---

## 6. Success Metrics

### Agent Performance
- **Story Selection**: >90% of selected stories meet quality thresholds
- **Synthesis Quality**: >0.75 average synthesis confidence
- **Editorial Quality**: >4.0/5.0 average editorial quality score
- **Processing Speed**: Complete workflow <15 minutes

### Content Quality
- **Uniqueness**: >85% unique content vs mainstream crypto media
- **Actionability**: >80% of readers find action items valuable
- **Accuracy**: >90% of forward-looking indicators prove relevant

---

*Sub-PRD Version: 1.0*
*Implementation Priority: Phase 2 - Core Agents*
*Dependencies: Batch article analysis completion*
*Estimated Effort: 3 weeks*
