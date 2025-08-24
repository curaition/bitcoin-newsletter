"""Newsletter Generation Orchestrator for multi-agent workflow."""

import logging
from datetime import datetime
from typing import Any

from .newsletter_writer import newsletter_writer_agent
from .story_selection import story_selection_agent
from .synthesis import synthesis_agent

logger = logging.getLogger(__name__)


class NewsletterOrchestrator:
    """Orchestrates the multi-agent newsletter generation workflow."""

    def __init__(self):
        self.story_agent = story_selection_agent
        self.synthesis_agent = synthesis_agent
        self.writer_agent = newsletter_writer_agent

    async def generate_newsletter(
        self, articles: list[dict[str, Any]], newsletter_type: str = "DAILY"
    ) -> dict[str, Any]:
        """Generate newsletter - delegates to appropriate method based on type."""
        if newsletter_type.upper() == "DAILY":
            return await self.generate_daily_newsletter(articles, newsletter_type)
        elif newsletter_type.upper() == "WEEKLY":
            # For weekly, articles parameter should be daily newsletters
            return await self.generate_weekly_newsletter(articles)
        else:
            raise ValueError(f"Unsupported newsletter type: {newsletter_type}")

    async def generate_daily_newsletter(
        self, articles: list[dict[str, Any]], newsletter_type: str = "DAILY"
    ) -> dict[str, Any]:
        """Complete daily newsletter generation workflow."""

        try:
            # Step 1: Story Selection
            logger.info(f"Starting story selection for {len(articles)} articles")

            formatted_articles = self.format_articles_for_selection(articles)
            selection_result = await self.story_agent.run(formatted_articles)

            if len(selection_result.output.selected_stories) < 3:
                raise ValueError("Not enough quality stories selected")

            # Step 2: Synthesis
            logger.info(
                f"Synthesizing {len(selection_result.output.selected_stories)} selected stories"
            )

            synthesis_input = self.format_selection_for_synthesis(
                selection_result.output, articles
            )
            synthesis_result = await self.synthesis_agent.run(synthesis_input)

            # Step 3: Newsletter Writing
            logger.info("Generating newsletter content")

            writing_input = self.format_synthesis_for_writing(
                synthesis_result.output, selection_result.output
            )
            newsletter_result = await self.writer_agent.run(writing_input)

            # Calculate costs and metadata
            total_cost = self.calculate_generation_cost(
                [
                    selection_result.usage(),
                    synthesis_result.usage(),
                    newsletter_result.usage(),
                ]
            )

            return {
                "success": True,
                "newsletter_content": newsletter_result.output.model_dump(mode='json'),
                "story_selection": selection_result.output.model_dump(mode='json'),
                "synthesis": synthesis_result.output.model_dump(mode='json'),
                "generation_metadata": {
                    "articles_reviewed": len(articles),
                    "stories_selected": len(selection_result.output.selected_stories),
                    "generation_cost": total_cost,
                    "quality_score": float(newsletter_result.output.editorial_quality_score),
                },
            }

        except Exception as e:
            logger.error(f"Newsletter generation failed: {str(e)}")
            return {"success": False, "error": str(e), "requires_manual_review": True}

    def format_articles_for_selection(self, articles: list[dict[str, Any]]) -> str:
        """Format analyzed articles for story selection agent."""

        formatted_articles = []
        for article in articles:
            article_summary = f"""
ARTICLE ID: {article['id']}
TITLE: {article['title']}
URL: {article.get('url', 'No URL available')}
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

Please select the 5-8 most revealing stories that best demonstrate emerging
patterns and provide unique market intelligence.

ARTICLES FOR REVIEW:
{''.join(formatted_articles)}

Focus on stories with strong signals, unique insights, and cross-domain
implications that mainstream crypto media typically misses.

IMPORTANT: Remember article URLs for proper citations in the final newsletter.
"""

    def format_selection_for_synthesis(
        self, selection, full_articles: list[dict[str, Any]]
    ) -> str:
        """Format story selection results for synthesis agent."""

        selected_article_details = []
        for story in selection.selected_stories:
            # Get full article details
            full_article = next(
                (a for a in full_articles if a["id"] == story.article_id), None
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

    def format_signals_list(self, signals: list[dict[str, Any]]) -> str:
        """Format signals with correct field names and rich context."""
        if not signals:
            return "None identified"

        formatted = []
        for signal in signals[:5]:  # Show more signals
            formatted.append(
                f"- {signal.get('signal_type', 'Unknown')}: {signal.get('description', 'No description')} "
                f"(confidence: {signal.get('confidence', 0):.2f}, {signal.get('timeframe', 'unknown')})"
            )
        return "\n".join(formatted)

    def format_patterns_list(self, patterns: list[dict[str, Any]]) -> str:
        """Format patterns with correct field names and significance."""
        if not patterns:
            return "None identified"

        formatted = []
        for pattern in patterns[:3]:
            formatted.append(
                f"- Expected: {pattern.get('expected_pattern', 'Unknown')}, "
                f"Observed: {pattern.get('observed_pattern', 'Unknown')} "
                f"(significance: {pattern.get('deviation_significance', 0):.2f})"
            )
        return "\n".join(formatted)

    def format_connections_list(self, connections: list[dict[str, Any]]) -> str:
        """Format connections with correct field names and relevance."""
        if not connections:
            return "None identified"

        formatted = []
        for conn in connections[:4]:
            formatted.append(
                f"- {conn.get('crypto_element', 'Unknown')} → "
                f"{conn.get('external_domain', 'Unknown')} "
                f"({conn.get('connection_type', 'Unknown')}, "
                f"relevance: {conn.get('relevance', 0):.2f})"
            )
        return "\n".join(formatted)

    def calculate_generation_cost(self, usages: list[Any]) -> float:
        """Calculate total cost from agent usages."""
        total_cost = 0.0
        for usage in usages:
            if hasattr(usage, "total_cost") and usage.total_cost:
                total_cost += usage.total_cost
        return total_cost

    async def generate_weekly_newsletter(
        self, daily_newsletters: list[Any]
    ) -> dict[str, Any]:
        """
        Generate weekly newsletter from daily newsletters.

        Args:
            daily_newsletters: List of daily Newsletter instances

        Returns:
            Dict with generation results
        """
        try:
            logger.info(
                f"Starting weekly newsletter generation from {len(daily_newsletters)} daily newsletters"
            )

            # Extract content from daily newsletters for synthesis
            daily_contents = []
            for newsletter in daily_newsletters:
                daily_contents.append(
                    {
                        "id": newsletter.id,
                        "title": newsletter.title,
                        "content": newsletter.content,
                        "summary": newsletter.summary,
                        "generation_date": newsletter.generation_date,
                        "quality_score": newsletter.quality_score,
                    }
                )

            # Create weekly story selection (aggregate from daily newsletters)
            weekly_selection = StorySelection(
                selection_date=datetime.now(),
                total_articles_reviewed=sum(
                    n.generation_metadata.get("articles_processed", 0)
                    for n in daily_newsletters
                    if n.generation_metadata
                ),
                selected_stories=[],  # Weekly doesn't select individual stories
                rejected_highlights=[],
                selection_themes=[
                    "Weekly Synthesis",
                    "Market Trends",
                    "Pattern Analysis",
                ],
                coverage_gaps=[],
            )

            # Generate weekly synthesis from daily newsletters
            synthesis_agent = SynthesisAgent()
            weekly_synthesis = await synthesis_agent.run(
                f"Synthesize weekly insights from {len(daily_newsletters)} daily newsletters:\n\n"
                + "\n\n".join(
                    [
                        f"Day {i+1} ({content['generation_date']}):\n{content['summary']}"
                        for i, content in enumerate(daily_contents)
                    ]
                )
            )

            # Generate weekly newsletter content
            writer_agent = NewsletterWriterAgent()
            weekly_content = await writer_agent.run(
                f"Create weekly newsletter from daily newsletter synthesis:\n\n"
                f"Weekly Synthesis: {weekly_synthesis.output.market_narrative}\n\n"
                f"Key Themes: {', '.join(weekly_synthesis.output.primary_themes)}\n\n"
                f"Daily Newsletter Summaries:\n"
                + "\n".join(
                    [
                        f"• {content['title']}: {content['summary']}"
                        for content in daily_contents
                    ]
                )
            )

            # Calculate costs
            generation_cost = self.calculate_generation_cost(
                [weekly_synthesis.usage, weekly_content.usage]
            )

            logger.info(
                f"Weekly newsletter generation completed - Cost: ${generation_cost:.4f}"
            )

            return {
                "success": True,
                "newsletter_content": weekly_content.output.model_dump(mode='json'),
                "story_selection": weekly_selection,
                "synthesis": weekly_synthesis.output.model_dump(mode='json'),
                "generation_metadata": {
                    "generation_cost": generation_cost,
                    "daily_newsletters_processed": len(daily_newsletters),
                    "synthesis_confidence": float(weekly_synthesis.output.synthesis_confidence),
                    "agent_versions": {"synthesis": "1.0", "writer": "1.0"},
                },
            }

        except Exception as e:
            logger.error(f"Weekly newsletter generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "generation_metadata": {
                    "generation_cost": 0.0,
                    "daily_newsletters_processed": len(daily_newsletters),
                },
            }


# Global orchestrator instance
newsletter_orchestrator = NewsletterOrchestrator()
