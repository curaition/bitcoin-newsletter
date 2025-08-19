"""Shared dependencies for analysis agents."""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class CostTracker:
    """Simple cost tracking for analysis operations."""

    total_cost: float = 0.0
    daily_budget: float = 50.0

    @property
    def remaining_budget(self) -> float:
        """Get remaining budget for today."""
        return max(0.0, self.daily_budget - self.total_cost)

    def add_cost(self, cost: float) -> None:
        """Add cost to tracker."""
        self.total_cost += cost

    def can_afford(self, estimated_cost: float) -> bool:
        """Check if we can afford an operation."""
        return self.remaining_budget >= estimated_cost


@dataclass
class AnalysisDependencies:
    """Dependencies injected into analysis agents."""

    # Database session for storing results
    db_session: AsyncSession

    # Cost tracking
    cost_tracker: CostTracker

    # Optional context
    current_publisher: Optional[str] = None
    current_article_id: Optional[int] = None

    # Analysis settings
    max_searches_per_validation: int = 5
    min_signal_confidence: float = 0.3
