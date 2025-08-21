"""Newsletter formatting utilities for consistent API responses."""

from datetime import datetime
from typing import Any, Optional

from crypto_newsletter.shared.models import Newsletter
from crypto_newsletter.web.models import (
    AdminNewsletterResponse,
    NewsletterContentSummary,
    NewsletterResponse,
)


class NewsletterFormatter:
    """Utility class for formatting newsletter data for API responses."""

    @staticmethod
    def format_newsletter_response(newsletter: Newsletter) -> NewsletterResponse:
        """Format a Newsletter model into a NewsletterResponse."""
        return NewsletterResponse(
            id=newsletter.id,
            title=newsletter.title,
            content=newsletter.content,
            summary=newsletter.summary,
            generation_date=newsletter.generation_date.isoformat(),
            status=newsletter.status,
            quality_score=newsletter.quality_score,
            agent_version=newsletter.agent_version,
            generation_metadata=newsletter.generation_metadata,
            published_at=newsletter.published_at.isoformat()
            if newsletter.published_at
            else None,
            created_at=newsletter.created_at.isoformat(),
            updated_at=newsletter.updated_at.isoformat(),
        )

    @staticmethod
    def format_admin_newsletter_response(
        newsletter: Newsletter,
    ) -> AdminNewsletterResponse:
        """Format a Newsletter model into an AdminNewsletterResponse with enhanced metadata."""
        # Extract admin-specific metadata
        newsletter_type = None
        generation_cost = None
        processing_time = None
        articles_processed = None

        if newsletter.generation_metadata:
            newsletter_type = newsletter.generation_metadata.get("newsletter_type")
            generation_cost = newsletter.generation_metadata.get("generation_cost")
            processing_time = newsletter.generation_metadata.get(
                "processing_time_seconds"
            )
            articles_processed = newsletter.generation_metadata.get(
                "articles_processed"
            )

        return AdminNewsletterResponse(
            id=newsletter.id,
            title=newsletter.title,
            status=newsletter.status,
            generation_date=newsletter.generation_date.isoformat(),
            quality_score=newsletter.quality_score,
            agent_version=newsletter.agent_version,
            created_at=newsletter.created_at.isoformat(),
            updated_at=newsletter.updated_at.isoformat(),
            newsletter_type=newsletter_type,
            generation_cost=generation_cost,
            processing_time=processing_time,
            articles_processed=articles_processed,
        )

    @staticmethod
    def format_newsletter_summary(newsletter: Newsletter) -> NewsletterContentSummary:
        """Format a Newsletter model into a NewsletterContentSummary."""
        # Calculate content metrics
        word_count = len(newsletter.content.split()) if newsletter.content else 0
        estimated_read_time = max(1, word_count // 200)  # 200 words per minute

        newsletter_type = "UNKNOWN"
        if newsletter.generation_metadata:
            newsletter_type = newsletter.generation_metadata.get(
                "newsletter_type", "UNKNOWN"
            )

        return NewsletterContentSummary(
            id=newsletter.id,
            title=newsletter.title,
            summary=newsletter.summary,
            newsletter_type=newsletter_type,
            status=newsletter.status,
            quality_score=newsletter.quality_score,
            generation_date=newsletter.generation_date.isoformat(),
            word_count=word_count,
            estimated_read_time=estimated_read_time,
        )

    @staticmethod
    def format_newsletter_list(
        newsletters: list[Newsletter],
        total_count: int,
        page: int,
        limit: int,
        formatter_type: str = "standard",
    ) -> dict[str, Any]:
        """
        Format a list of newsletters for API responses.

        Args:
            newsletters: List of Newsletter models
            total_count: Total count of newsletters matching criteria
            page: Current page number
            limit: Items per page
            formatter_type: Type of formatting ("standard", "admin", "summary")

        Returns:
            Formatted response dictionary
        """
        if formatter_type == "admin":
            formatted_newsletters = [
                NewsletterFormatter.format_admin_newsletter_response(n)
                for n in newsletters
            ]
        elif formatter_type == "summary":
            formatted_newsletters = [
                NewsletterFormatter.format_newsletter_summary(n) for n in newsletters
            ]
        else:
            formatted_newsletters = [
                NewsletterFormatter.format_newsletter_response(n) for n in newsletters
            ]

        return {
            "newsletters": formatted_newsletters,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "has_more": (page * limit) < total_count,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def format_generation_metadata(
        metadata: Optional[dict[str, Any]]
    ) -> dict[str, Any]:
        """Format generation metadata for API responses."""
        if not metadata:
            return {}

        formatted = {}

        # Core metadata
        if "newsletter_type" in metadata:
            formatted["newsletter_type"] = metadata["newsletter_type"]

        if "generation_cost" in metadata:
            formatted["generation_cost"] = round(metadata["generation_cost"], 4)

        if "processing_time_seconds" in metadata:
            formatted["processing_time_seconds"] = round(
                metadata["processing_time_seconds"], 2
            )

        if "articles_processed" in metadata:
            formatted["articles_processed"] = metadata["articles_processed"]

        # Quality metrics
        if "synthesis_confidence" in metadata:
            formatted["synthesis_confidence"] = round(
                metadata["synthesis_confidence"], 3
            )

        # Agent information
        if "agent_versions" in metadata:
            formatted["agent_versions"] = metadata["agent_versions"]

        # Task information
        if "task_started_at" in metadata:
            formatted["task_started_at"] = metadata["task_started_at"]

        return formatted

    @staticmethod
    def format_newsletter_stats(
        newsletters: list[Newsletter], period: str = "past_30_days"
    ) -> dict[str, Any]:
        """Format newsletter statistics for admin dashboard."""
        if not newsletters:
            return {
                "period": period,
                "total_newsletters": 0,
                "newsletter_types": {"daily": 0, "weekly": 0},
                "status_breakdown": {},
                "quality_metrics": {
                    "average_quality_score": 0.0,
                    "newsletters_with_scores": 0,
                },
                "cost_metrics": {
                    "total_generation_cost": 0.0,
                    "average_cost_per_newsletter": 0.0,
                    "newsletters_with_cost_data": 0,
                },
                "recent_newsletters": [],
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Separate by type
        daily_newsletters = [
            n
            for n in newsletters
            if n.generation_metadata
            and n.generation_metadata.get("newsletter_type") == "DAILY"
        ]
        weekly_newsletters = [
            n
            for n in newsletters
            if n.generation_metadata
            and n.generation_metadata.get("newsletter_type") == "WEEKLY"
        ]

        # Status breakdown
        status_counts = {}
        for newsletter in newsletters:
            status = newsletter.status
            status_counts[status] = status_counts.get(status, 0) + 1

        # Quality metrics
        quality_scores = [
            n.quality_score for n in newsletters if n.quality_score is not None
        ]
        avg_quality = (
            sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        )

        # Cost metrics
        generation_costs = []
        for newsletter in newsletters:
            if newsletter.generation_metadata:
                cost = newsletter.generation_metadata.get("generation_cost", 0.0)
                if cost and isinstance(cost, (int, float)):
                    generation_costs.append(cost)

        total_cost = sum(generation_costs)
        avg_cost = total_cost / len(generation_costs) if generation_costs else 0.0

        # Recent newsletters (last 10)
        recent_newsletters = sorted(
            newsletters, key=lambda n: n.generation_date, reverse=True
        )[:10]
        recent_formatted = []
        for newsletter in recent_newsletters:
            newsletter_type = "UNKNOWN"
            if newsletter.generation_metadata:
                newsletter_type = newsletter.generation_metadata.get(
                    "newsletter_type", "UNKNOWN"
                )

            recent_formatted.append(
                {
                    "id": newsletter.id,
                    "title": newsletter.title,
                    "type": newsletter_type,
                    "status": newsletter.status,
                    "generation_date": newsletter.generation_date.isoformat(),
                    "quality_score": newsletter.quality_score,
                }
            )

        return {
            "period": period,
            "total_newsletters": len(newsletters),
            "newsletter_types": {
                "daily": len(daily_newsletters),
                "weekly": len(weekly_newsletters),
            },
            "status_breakdown": status_counts,
            "quality_metrics": {
                "average_quality_score": round(avg_quality, 3),
                "newsletters_with_scores": len(quality_scores),
            },
            "cost_metrics": {
                "total_generation_cost": round(total_cost, 4),
                "average_cost_per_newsletter": round(avg_cost, 4),
                "newsletters_with_cost_data": len(generation_costs),
            },
            "recent_newsletters": recent_formatted,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def format_content_preview(content: str, max_length: int = 500) -> str:
        """Format content preview for API responses."""
        if not content:
            return ""

        if len(content) <= max_length:
            return content

        # Find a good breaking point (end of sentence or paragraph)
        truncated = content[:max_length]

        # Try to break at sentence end
        last_sentence = max(
            truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?")
        )

        if (
            last_sentence > max_length * 0.7
        ):  # If we found a sentence end in the last 30%
            return truncated[: last_sentence + 1] + "..."

        # Otherwise break at word boundary
        last_space = truncated.rfind(" ")
        if last_space > 0:
            return truncated[:last_space] + "..."

        return truncated + "..."
