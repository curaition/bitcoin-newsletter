"""Newsletter storage and database operations."""

import logging
import re
from datetime import date, datetime
from typing import Any, Optional

import markdown
from jinja2 import Template

from crypto_newsletter.newsletter.models.newsletter import (
    NewsletterContent,
    NewsletterSynthesis,
    StorySelection,
)
from crypto_newsletter.shared.models import Newsletter, NewsletterArticle
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class NewsletterStorage:
    """Storage class for newsletter database operations."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize storage with database session."""
        self.db = db_session

    async def create_newsletter(
        self,
        newsletter_content: NewsletterContent,
        story_selection: StorySelection,
        synthesis: NewsletterSynthesis,
        generation_metadata: Optional[dict[str, Any]] = None,
    ) -> Newsletter:
        """
        Create a new newsletter in the database.

        Args:
            newsletter_content: Generated newsletter content
            story_selection: Story selection results
            synthesis: Synthesis results
            generation_metadata: Additional metadata about generation

        Returns:
            Created Newsletter instance
        """
        try:
            # Create newsletter record
            newsletter = Newsletter(
                title=newsletter_content.title,
                content=self._format_newsletter_content(newsletter_content),
                summary="\n".join(newsletter_content.executive_summary),
                generation_date=datetime.now(),  # Use current datetime
                status="DRAFT",
                quality_score=newsletter_content.editorial_quality_score,
                agent_version="1.0",
                generation_metadata={
                    "generation_metadata": generation_metadata or {},
                    "story_selection": {
                        "total_articles_reviewed": story_selection.total_articles_reviewed,
                        "selected_count": len(story_selection.selected_stories),
                        "selection_themes": story_selection.selection_themes,
                        "coverage_gaps": story_selection.coverage_gaps,
                    },
                    "synthesis": {
                        "primary_themes": synthesis.primary_themes,
                        "synthesis_confidence": synthesis.synthesis_confidence,
                        "pattern_insights_count": len(synthesis.pattern_insights),
                        "cross_story_connections_count": len(
                            synthesis.cross_story_connections
                        ),
                    },
                    "content": {
                        "estimated_read_time": newsletter_content.estimated_read_time,
                        "action_items_count": len(newsletter_content.action_items),
                        "source_citations_count": len(
                            newsletter_content.source_citations
                        ),
                    },
                },
            )

            self.db.add(newsletter)
            await self.db.flush()  # Get the newsletter ID

            # Create newsletter-article relationships
            for story in story_selection.selected_stories:
                newsletter_article = NewsletterArticle(
                    newsletter_id=newsletter.id,
                    article_id=story.article_id,
                    selection_reason=story.selection_reasoning,
                    importance_score=story.signal_strength,
                )
                self.db.add(newsletter_article)

            await self.db.commit()
            await self.db.refresh(newsletter)

            logger.info(f"Created newsletter {newsletter.id}: {newsletter.title}")
            return newsletter

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create newsletter: {e}")
            raise

    async def get_newsletter_by_id(
        self, newsletter_id: int, include_articles: bool = True
    ) -> Optional[Newsletter]:
        """
        Get newsletter by ID.

        Args:
            newsletter_id: Newsletter ID
            include_articles: Whether to include related articles

        Returns:
            Newsletter instance or None
        """
        query = select(Newsletter).where(Newsletter.id == newsletter_id)

        if include_articles:
            query = query.options(
                selectinload(Newsletter.newsletter_articles).selectinload(
                    NewsletterArticle.article
                )
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_newsletters_by_date_range(
        self,
        start_date: date,
        end_date: date,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[Newsletter]:
        """
        Get newsletters within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            status: Optional status filter
            limit: Maximum number of newsletters to return

        Returns:
            List of Newsletter instances
        """
        query = (
            select(Newsletter)
            .where(
                and_(
                    Newsletter.generation_date >= start_date,
                    Newsletter.generation_date <= end_date,
                )
            )
            .order_by(desc(Newsletter.generation_date))
            .limit(limit)
        )

        if status:
            query = query.where(Newsletter.status == status)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent_newsletters(
        self, days: int = 30, status: Optional[str] = None, limit: int = 20
    ) -> list[Newsletter]:
        """
        Get recent newsletters.

        Args:
            days: Number of days to look back
            status: Optional status filter
            limit: Maximum number of newsletters to return

        Returns:
            List of Newsletter instances
        """
        from datetime import timedelta

        start_date = date.today() - timedelta(days=days)
        end_date = date.today()

        return await self.get_newsletters_by_date_range(
            start_date=start_date, end_date=end_date, status=status, limit=limit
        )

    async def update_newsletter_status(
        self, newsletter_id: int, status: str, published_at: Optional[datetime] = None
    ) -> Optional[Newsletter]:
        """
        Update newsletter status.

        Args:
            newsletter_id: Newsletter ID
            status: New status
            published_at: Optional publication timestamp

        Returns:
            Updated Newsletter instance or None
        """
        newsletter = await self.get_newsletter_by_id(
            newsletter_id, include_articles=False
        )
        if not newsletter:
            return None

        try:
            newsletter.status = status
            if published_at:
                newsletter.published_at = published_at

            await self.db.commit()
            await self.db.refresh(newsletter)

            logger.info(f"Updated newsletter {newsletter_id} status to {status}")
            return newsletter

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update newsletter status: {e}")
            raise

    async def delete_newsletter(self, newsletter_id: int) -> bool:
        """
        Delete newsletter by ID.

        Args:
            newsletter_id: Newsletter ID

        Returns:
            True if deleted, False if not found
        """
        newsletter = await self.get_newsletter_by_id(
            newsletter_id, include_articles=False
        )
        if not newsletter:
            return False

        try:
            await self.db.delete(newsletter)
            await self.db.commit()

            logger.info(f"Deleted newsletter {newsletter_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete newsletter: {e}")
            raise

    def _format_newsletter_content(self, content: NewsletterContent) -> str:
        """
        Format newsletter content for storage.

        Args:
            content: NewsletterContent instance

        Returns:
            Formatted content string
        """
        sections = [
            f"# {content.title}",
            "",
            "## Executive Summary",
            "",
        ]

        for i, summary in enumerate(content.executive_summary, 1):
            sections.append(f"{i}. {summary}")

        sections.extend(
            [
                "",
                "## Main Analysis",
                "",
                content.main_analysis,
                "",
                "## Pattern Spotlight",
                "",
                content.pattern_spotlight,
                "",
                "## Adjacent Watch",
                "",
                content.adjacent_watch,
                "",
                "## Signal Radar",
                "",
                content.signal_radar,
                "",
                "## Action Items",
                "",
            ]
        )

        for i, action in enumerate(content.action_items, 1):
            sections.append(f"{i}. {action}")

        sections.extend(
            [
                "",
                "## Conclusion & What This Means",
                "",
                "Based on the analysis above, readers should focus on monitoring institutional adoption patterns, regulatory developments, and cross-asset correlations as key indicators for the next phase of market evolution. The convergence of traditional finance infrastructure with crypto assets represents a fundamental shift that demands careful attention to both opportunities and risks.",
                "",
                "## Sources & Citations",
                "",
            ]
        )

        for i, source in enumerate(content.source_citations, 1):
            sections.append(f"{i}. {source}")

        sections.extend(
            [
                "",
                "---",
                "",
                f"*Estimated read time: {content.estimated_read_time} minutes*",
                f"*Quality score: {content.editorial_quality_score:.2f}*",
            ]
        )

        return "\n".join(sections)

    def _generate_html_content(self, content: NewsletterContent) -> str:
        """
        Convert newsletter content to HTML format for email/web display.

        Args:
            content: NewsletterContent object to convert

        Returns:
            HTML formatted newsletter content
        """
        # Get the markdown content
        markdown_content = self._format_newsletter_content(content)

        # Convert markdown to HTML with extensions
        html_content = markdown.markdown(
            markdown_content,
            extensions=[
                'markdown.extensions.codehilite',
                'markdown.extensions.tables',
                'markdown.extensions.toc',
                'markdown.extensions.fenced_code',
                'markdown.extensions.nl2br'
            ]
        )

        # Apply newsletter-specific HTML template
        return self._apply_newsletter_template(html_content, content)

    def _apply_newsletter_template(self, html_content: str, content: NewsletterContent) -> str:
        """
        Apply HTML template to newsletter content.

        Args:
            html_content: Raw HTML content from markdown conversion
            content: Original NewsletterContent for metadata

        Returns:
            Templated HTML newsletter
        """
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }
        .newsletter-container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #f7931a;
            border-bottom: 3px solid #f7931a;
            padding-bottom: 10px;
        }
        h2 {
            color: #2c3e50;
            margin-top: 30px;
        }
        .executive-summary {
            background: #fff3cd;
            border-left: 4px solid #f7931a;
            padding: 20px;
            margin: 20px 0;
        }
        .citation {
            font-size: 0.9em;
            color: #666;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            font-size: 0.9em;
            color: #666;
        }
        a {
            color: #f7931a;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        blockquote {
            border-left: 4px solid #f7931a;
            margin: 20px 0;
            padding-left: 20px;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="newsletter-container">
        {{ content }}
        <div class="footer">
            <p><strong>Read Time:</strong> {{ read_time }} minutes</p>
            <p><strong>Quality Score:</strong> {{ quality_score }}/1.0</p>
            <p><strong>Generated:</strong> {{ generation_date }}</p>
        </div>
    </div>
</body>
</html>
        """

        template = Template(template_str)

        return template.render(
            title=content.title,
            content=html_content,
            read_time=content.estimated_read_time,
            quality_score=f"{content.editorial_quality_score:.2f}",
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        )

    async def get_newsletter_html(self, newsletter_id: int) -> Optional[str]:
        """
        Get newsletter content as HTML.

        Args:
            newsletter_id: ID of the newsletter

        Returns:
            HTML formatted newsletter content or None if not found
        """
        newsletter = await self.get_newsletter_by_id(newsletter_id)
        if not newsletter:
            return None

        # Parse the stored content back to NewsletterContent
        try:
            import json
            content_dict = json.loads(newsletter.content)
            content = NewsletterContent(**content_dict)
            return self._generate_html_content(content)
        except Exception as e:
            logger.error(f"Failed to generate HTML for newsletter {newsletter_id}: {e}")
            return None

    def validate_citations(self, content: str) -> dict[str, int]:
        """
        Validate citations in newsletter content.

        Args:
            content: Newsletter content to validate

        Returns:
            Dictionary with citation counts and metrics
        """
        # Pattern for markdown links: [text](url)
        markdown_pattern = r'\[([^\]]+)\]\(https?://[^\)]+\)'

        # Pattern for signal references with confidence scores
        signal_pattern = r'signal.*?\((\d+\.\d+)\)'

        # Extract all URLs for validation
        url_pattern = r'https?://[^\s\)]+'
        urls = re.findall(url_pattern, content)

        # Count different citation types
        markdown_citations = re.findall(markdown_pattern, content)
        signal_references = re.findall(signal_pattern, content, re.IGNORECASE)

        return {
            'total_citations': len(markdown_citations),
            'signal_references': len(signal_references),
            'unique_urls': len(set(urls)),
            'citation_density': len(markdown_citations) / max(len(content.split()), 1) * 1000,  # per 1000 words
            'meets_minimum_citations': len(markdown_citations) >= 8
        }
