"""Newsletter generation alerting system."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Optional

from crypto_newsletter.shared.config.settings import get_settings
from crypto_newsletter.shared.monitoring.metrics import MetricsCollector
from loguru import logger


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertType(Enum):
    """Newsletter generation alert types."""

    GENERATION_FAILURE = "generation_failure"
    LOW_QUALITY_SCORE = "low_quality_score"
    LOW_CITATION_COUNT = "low_citation_count"
    HIGH_FAILURE_RATE = "high_failure_rate"
    STUCK_GENERATION = "stuck_generation"
    COST_THRESHOLD = "cost_threshold"


@dataclass
class NewsletterAlert:
    """Newsletter generation alert."""

    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime
    task_id: Optional[str] = None
    newsletter_id: Optional[int] = None
    metrics: Optional[dict[str, Any]] = None
    threshold: Optional[float] = None
    current_value: Optional[float] = None


class NewsletterAlertManager:
    """Manages newsletter generation alerts and notifications."""

    def __init__(self):
        self.settings = get_settings()
        self.metrics_collector = MetricsCollector()

        # Alert thresholds (configurable via environment)
        self.thresholds = {
            "quality_score_warning": float(
                getattr(self.settings, "alert_quality_score_warning", 0.7)
            ),
            "quality_score_critical": float(
                getattr(self.settings, "alert_quality_score_critical", 0.5)
            ),
            "citation_count_warning": int(
                getattr(self.settings, "alert_citation_count_warning", 5)
            ),
            "citation_count_critical": int(
                getattr(self.settings, "alert_citation_count_critical", 3)
            ),
            "failure_rate_warning": float(
                getattr(self.settings, "alert_failure_rate_warning", 0.2)
            ),
            "failure_rate_critical": float(
                getattr(self.settings, "alert_failure_rate_critical", 0.5)
            ),
            "stuck_generation_hours": int(
                getattr(self.settings, "alert_stuck_generation_hours", 2)
            ),
        }

    async def check_newsletter_alerts(self) -> list[NewsletterAlert]:
        """Check for newsletter generation alerts."""
        alerts = []

        try:
            # Get generation metrics
            generation_metrics = (
                await self.metrics_collector.collect_newsletter_generation_metrics()
            )

            # Check quality score alerts
            quality_alerts = self._check_quality_alerts(generation_metrics)
            alerts.extend(quality_alerts)

            # Check failure rate alerts
            failure_alerts = self._check_failure_rate_alerts(generation_metrics)
            alerts.extend(failure_alerts)

            # Check stuck generation alerts
            stuck_alerts = await self._check_stuck_generation_alerts()
            alerts.extend(stuck_alerts)

            # Log alerts
            for alert in alerts:
                self._log_alert(alert)

            return alerts

        except Exception as e:
            logger.error(f"Failed to check newsletter alerts: {e}")
            return []

    def _check_quality_alerts(self, metrics: dict[str, Any]) -> list[NewsletterAlert]:
        """Check for quality-related alerts."""
        alerts = []

        avg_quality_score = metrics.get("avg_quality_score", 1.0)
        avg_citation_count = metrics.get("avg_citation_count", 10)

        # Quality score alerts
        if avg_quality_score < self.thresholds["quality_score_critical"]:
            alerts.append(
                NewsletterAlert(
                    alert_type=AlertType.LOW_QUALITY_SCORE,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Critical: Average quality score is {avg_quality_score:.2f} (threshold: {self.thresholds['quality_score_critical']})",
                    timestamp=datetime.now(UTC),
                    metrics=metrics,
                    threshold=self.thresholds["quality_score_critical"],
                    current_value=avg_quality_score,
                )
            )
        elif avg_quality_score < self.thresholds["quality_score_warning"]:
            alerts.append(
                NewsletterAlert(
                    alert_type=AlertType.LOW_QUALITY_SCORE,
                    severity=AlertSeverity.WARNING,
                    message=f"Warning: Average quality score is {avg_quality_score:.2f} (threshold: {self.thresholds['quality_score_warning']})",
                    timestamp=datetime.now(UTC),
                    metrics=metrics,
                    threshold=self.thresholds["quality_score_warning"],
                    current_value=avg_quality_score,
                )
            )

        # Citation count alerts
        if avg_citation_count < self.thresholds["citation_count_critical"]:
            alerts.append(
                NewsletterAlert(
                    alert_type=AlertType.LOW_CITATION_COUNT,
                    severity=AlertSeverity.CRITICAL,
                    message=f"Critical: Average citation count is {avg_citation_count} (threshold: {self.thresholds['citation_count_critical']})",
                    timestamp=datetime.now(UTC),
                    metrics=metrics,
                    threshold=self.thresholds["citation_count_critical"],
                    current_value=avg_citation_count,
                )
            )
        elif avg_citation_count < self.thresholds["citation_count_warning"]:
            alerts.append(
                NewsletterAlert(
                    alert_type=AlertType.LOW_CITATION_COUNT,
                    severity=AlertSeverity.WARNING,
                    message=f"Warning: Average citation count is {avg_citation_count} (threshold: {self.thresholds['citation_count_warning']})",
                    timestamp=datetime.now(UTC),
                    metrics=metrics,
                    threshold=self.thresholds["citation_count_warning"],
                    current_value=avg_citation_count,
                )
            )

        return alerts

    def _check_failure_rate_alerts(
        self, metrics: dict[str, Any]
    ) -> list[NewsletterAlert]:
        """Check for failure rate alerts."""
        alerts = []

        failure_rate = metrics.get("failure_rate", 0.0)
        total_generations = metrics.get("total_generations_24h", 0)

        if total_generations > 0:
            if failure_rate >= self.thresholds["failure_rate_critical"]:
                alerts.append(
                    NewsletterAlert(
                        alert_type=AlertType.HIGH_FAILURE_RATE,
                        severity=AlertSeverity.CRITICAL,
                        message=f"Critical: Generation failure rate is {failure_rate:.1%} (threshold: {self.thresholds['failure_rate_critical']:.1%})",
                        timestamp=datetime.now(UTC),
                        metrics=metrics,
                        threshold=self.thresholds["failure_rate_critical"],
                        current_value=failure_rate,
                    )
                )
            elif failure_rate >= self.thresholds["failure_rate_warning"]:
                alerts.append(
                    NewsletterAlert(
                        alert_type=AlertType.HIGH_FAILURE_RATE,
                        severity=AlertSeverity.WARNING,
                        message=f"Warning: Generation failure rate is {failure_rate:.1%} (threshold: {self.thresholds['failure_rate_warning']:.1%})",
                        timestamp=datetime.now(UTC),
                        metrics=metrics,
                        threshold=self.thresholds["failure_rate_warning"],
                        current_value=failure_rate,
                    )
                )

        return alerts

    async def _check_stuck_generation_alerts(self) -> list[NewsletterAlert]:
        """Check for stuck generation alerts."""
        alerts = []

        try:
            from crypto_newsletter.newsletter.models.progress import (
                NewsletterGenerationProgress,
            )
            from crypto_newsletter.shared.database.connection import get_db_session
            from sqlalchemy import select

            async with get_db_session() as db:
                # Find generations stuck for more than threshold hours (use naive datetime)
                stuck_threshold = datetime.now() - timedelta(
                    hours=self.thresholds["stuck_generation_hours"]
                )

                stuck_query = select(NewsletterGenerationProgress).where(
                    NewsletterGenerationProgress.status == "in_progress",
                    NewsletterGenerationProgress.created_at < stuck_threshold,
                )

                result = await db.execute(stuck_query)
                stuck_generations = result.scalars().all()

                for stuck_gen in stuck_generations:
                    alerts.append(
                        NewsletterAlert(
                            alert_type=AlertType.STUCK_GENERATION,
                            severity=AlertSeverity.WARNING,
                            message=f"Generation stuck for {self.thresholds['stuck_generation_hours']}+ hours",
                            timestamp=datetime.now(UTC),
                            task_id=stuck_gen.task_id,
                            metrics={"stuck_since": stuck_gen.created_at.isoformat()},
                        )
                    )

        except Exception as e:
            logger.error(f"Failed to check stuck generations: {e}")

        return alerts

    def _log_alert(self, alert: NewsletterAlert) -> None:
        """Log alert using structured logging."""
        log_data = {
            "alert_type": alert.alert_type.value,
            "severity": alert.severity.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "service_type": "newsletter_generation",
        }

        if alert.task_id:
            log_data["task_id"] = alert.task_id
        if alert.newsletter_id:
            log_data["newsletter_id"] = alert.newsletter_id
        if alert.threshold:
            log_data["threshold"] = alert.threshold
        if alert.current_value:
            log_data["current_value"] = alert.current_value

        # Log with appropriate level
        if alert.severity == AlertSeverity.CRITICAL:
            logger.critical("Newsletter generation alert", extra=log_data)
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning("Newsletter generation alert", extra=log_data)
        else:
            logger.info("Newsletter generation alert", extra=log_data)


# Global alert manager instance
_alert_manager = NewsletterAlertManager()


def get_alert_manager() -> NewsletterAlertManager:
    """Get the global alert manager instance."""
    return _alert_manager


async def check_newsletter_alerts() -> list[NewsletterAlert]:
    """Convenience function to check newsletter alerts."""
    return await _alert_manager.check_newsletter_alerts()
