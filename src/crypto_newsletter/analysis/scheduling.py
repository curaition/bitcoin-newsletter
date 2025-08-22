"""Intelligent scheduling system for article analysis."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from crypto_newsletter.shared.database.connection import get_sync_db_session
from sqlalchemy import text

logger = logging.getLogger(__name__)


@dataclass
class AnalysisSchedulingConfig:
    """Configuration for intelligent analysis scheduling."""

    # Budget management
    DAILY_BUDGET: float = 5.00  # $5/day for analysis
    MAX_COST_PER_ARTICLE: float = 0.25  # $0.25 max per article
    COST_PER_ARTICLE_ESTIMATE: float = 0.0013  # Current estimate

    # Content thresholds
    MIN_ARTICLES_FOR_ANALYSIS: int = 5  # Minimum articles to trigger analysis
    MAX_ARTICLES_PER_RUN: int = 20  # Maximum articles per scheduled run
    RECENT_HOURS_THRESHOLD: int = 24  # Hours to consider "recent"

    # Quality thresholds
    MIN_CONTENT_LENGTH: int = 1000  # Minimum article length
    PRIORITY_PUBLISHERS: list[str] = None  # Will be set in __post_init__

    # Scheduling intelligence
    PEAK_HOURS: list[int] = None  # Hours when analysis should be prioritized
    OFF_PEAK_MULTIPLIER: float = 1.5  # Process more articles during off-peak

    def __post_init__(self):
        if self.PRIORITY_PUBLISHERS is None:
            self.PRIORITY_PUBLISHERS = [
                "CoinDesk",
                "NewsBTC",
                "Crypto Potato",
                "CoinTelegraph",
            ]

        if self.PEAK_HOURS is None:
            # Peak hours: 6-10 AM UTC (newsletter generation time)
            self.PEAK_HOURS = [6, 7, 8, 9, 10]


class AnalysisScheduler:
    """Intelligent scheduler for article analysis."""

    def __init__(self, config: AnalysisSchedulingConfig = None):
        self.config = config or AnalysisSchedulingConfig()

    def should_analyze_now(self) -> dict[str, Any]:
        """
        Determine if analysis should run based on content availability and budget.

        Returns:
            Dict with decision and reasoning
        """
        try:
            with get_sync_db_session() as db:
                # Check current budget usage
                budget_status = self._check_daily_budget_usage(db)

                # Check content availability
                content_status = self._check_content_availability(db)

                # Check time-based factors
                time_status = self._check_time_factors()

                # Make decision
                should_run = self._make_scheduling_decision(
                    budget_status, content_status, time_status
                )

                return {
                    "should_analyze": should_run["decision"],
                    "reasoning": should_run["reasoning"],
                    "recommended_articles": should_run["recommended_count"],
                    "budget_status": budget_status,
                    "content_status": content_status,
                    "time_status": time_status,
                }

        except Exception as e:
            logger.error(f"Error in scheduling decision: {e}")
            return {
                "should_analyze": False,
                "reasoning": f"Scheduling error: {str(e)}",
                "recommended_articles": 0,
            }

    def _check_daily_budget_usage(self, db) -> dict[str, Any]:
        """Check how much of daily budget has been used."""
        try:
            # Get today's analysis costs
            today_query = text(
                """
                SELECT COALESCE(SUM(cost_usd), 0) as daily_cost, COUNT(*) as daily_analyses
                FROM article_analyses
                WHERE created_at >= CURRENT_DATE
            """
            )

            result = db.execute(today_query).fetchone()
            daily_cost = float(result[0]) if result else 0.0
            daily_analyses = int(result[1]) if result else 0

            remaining_budget = self.config.DAILY_BUDGET - daily_cost
            budget_utilization = (daily_cost / self.config.DAILY_BUDGET) * 100

            return {
                "daily_cost": daily_cost,
                "daily_analyses": daily_analyses,
                "remaining_budget": remaining_budget,
                "budget_utilization": budget_utilization,
                "within_budget": remaining_budget > 0,
                "can_afford_articles": int(
                    remaining_budget / self.config.COST_PER_ARTICLE_ESTIMATE
                ),
            }

        except Exception as e:
            logger.error(f"Error checking budget: {e}")
            return {"within_budget": False, "remaining_budget": 0}

    def _check_content_availability(self, db) -> dict[str, Any]:
        """Check what content is available for analysis."""
        try:
            # Recent unanalyzed articles
            recent_query = text(
                """
                SELECT COUNT(*) as count
                FROM articles a
                LEFT JOIN article_analyses aa ON a.id = aa.article_id
                WHERE a.status = 'ACTIVE'
                  AND aa.id IS NULL
                  AND LENGTH(a.body) > :min_length
                  AND a.created_at >= NOW() - INTERVAL '24 hours'
            """
            )

            recent_result = db.execute(
                recent_query, {"min_length": self.config.MIN_CONTENT_LENGTH}
            ).fetchone()
            recent_count = int(recent_result[0]) if recent_result else 0

            # Total unanalyzed articles
            total_query = text(
                """
                SELECT COUNT(*) as count
                FROM articles a
                LEFT JOIN article_analyses aa ON a.id = aa.article_id
                WHERE a.status = 'ACTIVE'
                  AND aa.id IS NULL
                  AND LENGTH(a.body) > :min_length
            """
            )

            total_result = db.execute(
                total_query, {"min_length": self.config.MIN_CONTENT_LENGTH}
            ).fetchone()
            total_count = int(total_result[0]) if total_result else 0

            # Quality articles (from priority publishers)
            quality_query = text(
                """
                SELECT COUNT(*) as count
                FROM articles a
                LEFT JOIN article_analyses aa ON a.id = aa.article_id
                LEFT JOIN publishers p ON a.publisher_id = p.id
                WHERE a.status = 'ACTIVE'
                  AND aa.id IS NULL
                  AND LENGTH(a.body) > :min_length
                  AND p.name = ANY(:publishers)
            """
            )

            quality_result = db.execute(
                quality_query,
                {
                    "min_length": self.config.MIN_CONTENT_LENGTH,
                    "publishers": self.config.PRIORITY_PUBLISHERS,
                },
            ).fetchone()
            quality_count = int(quality_result[0]) if quality_result else 0

            return {
                "recent_unanalyzed": recent_count,
                "total_unanalyzed": total_count,
                "quality_unanalyzed": quality_count,
                "has_sufficient_content": recent_count
                >= self.config.MIN_ARTICLES_FOR_ANALYSIS,
                "content_urgency": "high"
                if recent_count > 20
                else "medium"
                if recent_count > 10
                else "low",
            }

        except Exception as e:
            logger.error(f"Error checking content: {e}")
            return {"has_sufficient_content": False, "recent_unanalyzed": 0}

    def _check_time_factors(self) -> dict[str, Any]:
        """Check time-based scheduling factors."""
        now = datetime.utcnow()
        current_hour = now.hour

        is_peak_hour = current_hour in self.config.PEAK_HOURS
        is_newsletter_time = current_hour in [6, 7, 8]  # Newsletter generation hours

        # Calculate multiplier for article count
        if is_peak_hour:
            multiplier = 1.0  # Standard processing during peak
        else:
            multiplier = self.config.OFF_PEAK_MULTIPLIER  # More processing off-peak

        return {
            "current_hour": current_hour,
            "is_peak_hour": is_peak_hour,
            "is_newsletter_time": is_newsletter_time,
            "processing_multiplier": multiplier,
            "time_priority": "high"
            if is_newsletter_time
            else "medium"
            if is_peak_hour
            else "low",
        }

    def _make_scheduling_decision(
        self, budget_status: dict, content_status: dict, time_status: dict
    ) -> dict[str, Any]:
        """Make the final scheduling decision based on all factors."""

        # Decision factors
        has_budget = budget_status.get("within_budget", False)
        has_content = content_status.get("has_sufficient_content", False)
        can_afford_articles = budget_status.get("can_afford_articles", 0)

        # Base decision
        if not has_budget:
            return {
                "decision": False,
                "reasoning": "Daily budget exhausted",
                "recommended_count": 0,
            }

        if not has_content:
            return {
                "decision": False,
                "reasoning": f"Insufficient content (need {self.config.MIN_ARTICLES_FOR_ANALYSIS}, have {content_status.get('recent_unanalyzed', 0)})",
                "recommended_count": 0,
            }

        # Calculate recommended article count
        base_count = min(
            content_status.get("recent_unanalyzed", 0),
            can_afford_articles,
            self.config.MAX_ARTICLES_PER_RUN,
        )

        # Apply time-based multiplier
        multiplier = time_status.get("processing_multiplier", 1.0)
        recommended_count = min(
            int(base_count * multiplier), self.config.MAX_ARTICLES_PER_RUN
        )

        # Priority reasoning
        priority_factors = []
        if time_status.get("is_newsletter_time"):
            priority_factors.append("newsletter generation time")
        if content_status.get("content_urgency") == "high":
            priority_factors.append("high content backlog")
        if content_status.get("quality_unanalyzed", 0) > 5:
            priority_factors.append("quality articles available")

        reasoning = f"Process {recommended_count} articles"
        if priority_factors:
            reasoning += f" (priority: {', '.join(priority_factors)})"

        return {
            "decision": True,
            "reasoning": reasoning,
            "recommended_count": recommended_count,
        }


# Global scheduler instance
analysis_scheduler = AnalysisScheduler()
