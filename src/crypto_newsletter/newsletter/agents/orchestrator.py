"""Newsletter Generation Orchestrator for multi-agent workflow."""

import logging
from datetime import datetime
from typing import Any, Dict, List

from .story_selection import story_selection_agent
from .synthesis import synthesis_agent
from .newsletter_writer import newsletter_writer_agent

logger = logging.getLogger(__name__)


class NewsletterOrchestrator:
    """Orchestrates the multi-agent newsletter generation workflow."""

    def __init__(self):
        self.story_agent = story_selection_agent
        self.synthesis_agent = synthesis_agent
        self.writer_agent = newsletter_writer_agent

    async def generate_daily_newsletter(
        self,
        articles: List[Dict[str, Any]],
        newsletter_type: str = "DAILY"
    ) -> Dict[str, Any]:
        """Complete daily newsletter generation workflow."""

        try:
            # Step 1: Story Selection
            logger.info(f"Starting story selection for {len(articles)} articles")

            formatted_articles = self.format_articles_for_selection(articles)
            selection_result = await self.story_agent.run(formatted_articles)

            if len(selection_result.data.selected_stories) < 3:
                raise ValueError("Not enough quality stories selected")

            # Step 2: Synthesis
            logger.info(f"Synthesizing {len(selection_result.data.selected_stories)} selected stories")

            synthesis_input = self.format_selection_for_synthesis(
                selection_result.data, articles
            )
            synthesis_result = await self.synthesis_agent.run(synthesis_input)

            # Step 3: Newsletter Writing
            logger.info("Generating newsletter content")

            writing_input = self.format_synthesis_for_writing(
                synthesis_result.data, selection_result.data
            )
            newsletter_result = await self.writer_agent.run(writing_input)

            # Calculate costs and metadata
            total_cost = self.calculate_generation_cost([
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

    def format_articles_for_selection(self, articles: List[Dict[str, Any]]) -> str:
        """Format analyzed articles for story selection agent."""

        formatted_articles = []
        for article in articles:
            article_summary = f"""
ARTICLE ID: {article['id']}
TITLE: {article['title']}
PUBLISHER: {article.get('publisher', 'Unknown')}
PUBLISHED: {article.get('published_on', 'Unknown')}
SIGNAL STRENGTH: {article.get('signal_strength', 0):.2f}
UNIQUENESS SCORE: {article.get('uniqueness_score', 0):.2f}
ANALYSIS CONFIDENCE: {article.get('analysis_confidence', 0):.2f}

KEY SIGNALS:
{self.format_signals_list(article.get('weak_signals', []))}

PATTERN ANOMALIES:
{self.format_patterns_list(article.get('pattern_anomalies', []))}

ADJACENT CONNECTIONS:
{self.format_connections_list(article.get('adjacent_connections', []))}

CONTENT PREVIEW:
{article.get('body', '')[:500]}...

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

    def format_selection_for_synthesis(self, selection, full_articles: List[Dict[str, Any]]) -> str:
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
- Weak Signals: {self.format_signals_list(full_article.get('weak_signals', []))}
- Pattern Anomalies: {self.format_patterns_list(full_article.get('pattern_anomalies', []))}
- Adjacent Connections: {self.format_connections_list(full_article.get('adjacent_connections', []))}

Content Summary: {full_article.get('body', '')[:800]}...

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

    def format_synthesis_for_writing(self, synthesis, selection) -> str:
        """Format synthesis results for newsletter writer agent."""

        return f"""
NEWSLETTER WRITING BRIEFING
Date: {synthesis.synthesis_date.strftime('%Y-%m-%d')}
Synthesis Confidence: {synthesis.synthesis_confidence:.2f}

PRIMARY THEMES:
{chr(10).join(f"- {theme}" for theme in synthesis.primary_themes)}

MARKET NARRATIVE:
{synthesis.market_narrative}

PATTERN INSIGHTS:
{chr(10).join(f"- {insight.pattern_type}: {insight.description} (confidence: {insight.confidence:.2f})" for insight in synthesis.pattern_insights)}

CROSS-STORY CONNECTIONS:
{chr(10).join(f"- {conn.connection_type}: {conn.synthesis_insight}" for conn in synthesis.cross_story_connections)}

FORWARD INDICATORS:
{chr(10).join(f"- {indicator}" for indicator in synthesis.forward_indicators)}

ADJACENT IMPLICATIONS:
{chr(10).join(f"- {implication}" for implication in synthesis.adjacent_implications)}

SELECTED STORIES CONTEXT:
Stories: {len(selection.selected_stories)}
Selection Themes: {', '.join(selection.selection_themes)}

Please create compelling newsletter content that transforms this analysis into actionable insights for readers.
"""

    def format_signals_list(self, signals: List[Dict[str, Any]]) -> str:
        """Format signals list for display."""
        if not signals:
            return "None identified"
        return "\n".join(f"- {signal.get('signal', 'Unknown')}: {signal.get('description', 'No description')}" for signal in signals[:3])

    def format_patterns_list(self, patterns: List[Dict[str, Any]]) -> str:
        """Format patterns list for display."""
        if not patterns:
            return "None identified"
        return "\n".join(f"- {pattern.get('pattern', 'Unknown')}: {pattern.get('description', 'No description')}" for pattern in patterns[:3])

    def format_connections_list(self, connections: List[Dict[str, Any]]) -> str:
        """Format connections list for display."""
        if not connections:
            return "None identified"
        return "\n".join(f"- {conn.get('connection', 'Unknown')}: {conn.get('description', 'No description')}" for conn in connections[:3])

    def calculate_generation_cost(self, usages: List[Any]) -> float:
        """Calculate total cost from agent usages."""
        total_cost = 0.0
        for usage in usages:
            if hasattr(usage, 'total_cost') and usage.total_cost:
                total_cost += usage.total_cost
        return total_cost


# Global orchestrator instance
newsletter_orchestrator = NewsletterOrchestrator()
