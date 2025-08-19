# Automated Newsletter Scheduling System
## Sub-PRD 6: Celery Beat Schedule & Monitoring Integration

### Executive Summary
Implement comprehensive Celery Beat scheduling for automated daily and weekly newsletter generation, with intelligent monitoring, failure recovery, and adaptive scheduling based on content availability and system performance.

---

## 1. Product Overview

### Objective
Create a robust automated scheduling system that reliably generates and publishes newsletters at optimal times, with intelligent monitoring, failure recovery, and adaptive scheduling capabilities.

### Scheduling Architecture
```
Celery Beat → Task Triggers → Content Validation → Generation Pipeline → Publishing → Monitoring
     ↓             ↓              ↓                    ↓               ↓           ↓
Time-based    Task Queue    Quality Gates      Agent Workflow    Distribution   Analytics
```

---

## 2. Enhanced Celery Beat Configuration

### 2.1 Newsletter Scheduling Configuration
```python
from celery.schedules import crontab
from crypto_newsletter.shared.celery.app import celery_app

# Enhanced Celery Beat Schedule with Newsletter Tasks
ENHANCED_CELERY_BEAT_SCHEDULE = {
    # Existing tasks (keep current schedule)
    "ingest-articles-every-4-hours": {
        "task": "crypto_newsletter.core.scheduling.tasks.ingest_articles",
        "schedule": crontab(minute=0, hour="*/4"),  # Every 4 hours
        "options": {
            "priority": 9,
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 60,
                "interval_step": 60,
                "interval_max": 300,
            }
        },
    },

    "analyze-recent-articles-every-6-hours": {
        "task": "crypto_newsletter.analysis.tasks.analyze_recent_articles",
        "schedule": crontab(minute=30, hour="*/6"),  # Every 6 hours at :30
        "options": {
            "priority": 7,
            "retry_policy": {
                "max_retries": 2,
                "interval_start": 300,
                "interval_step": 300,
                "interval_max": 900,
            }
        },
    },

    # NEW: Daily Newsletter Generation
    "generate-daily-newsletter": {
        "task": "crypto_newsletter.newsletter.tasks.generate_daily_newsletter",
        "schedule": crontab(hour=6, minute=0),  # 6:00 AM UTC daily
        "options": {
            "priority": 8,
            "queue": "newsletter",
            "retry_policy": {
                "max_retries": 2,
                "interval_start": 1800,  # 30 minutes
                "interval_step": 1800,
                "interval_max": 3600,    # 1 hour max
            }
        },
    },

    # NEW: Weekly Newsletter Generation
    "generate-weekly-newsletter": {
        "task": "crypto_newsletter.newsletter.tasks.generate_weekly_newsletter",
        "schedule": crontab(hour=8, minute=0, day_of_week=0),  # 8:00 AM UTC Sundays
        "options": {
            "priority": 8,
            "queue": "newsletter",
            "retry_policy": {
                "max_retries": 2,
                "interval_start": 3600,  # 1 hour
                "interval_step": 3600,
                "interval_max": 7200,    # 2 hours max
            }
        },
    },

    # NEW: Newsletter Generation Monitoring
    "monitor-newsletter-generation": {
        "task": "crypto_newsletter.newsletter.tasks.monitor_newsletter_generation",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
        "options": {"priority": 6},
    },

    # NEW: Newsletter Performance Tracking
    "update-newsletter-metrics": {
        "task": "crypto_newsletter.newsletter.tasks.update_newsletter_metrics",
        "schedule": crontab(minute=0, hour="*/2"),  # Every 2 hours
        "options": {"priority": 5},
    },

    # NEW: Batch Processing Monitoring (when active)
    "monitor-batch-processing": {
        "task": "crypto_newsletter.newsletter.tasks.monitor_batch_processing",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
        "options": {"priority": 7},
        "enabled": False,  # Enable only during batch processing
    },

    # Enhanced existing tasks
    "health-check-every-5-minutes": {
        "task": "crypto_newsletter.core.scheduling.tasks.health_check",
        "schedule": crontab(minute="*/5"),
        "options": {"priority": 8},
    },

    "cleanup-old-articles-daily": {
        "task": "crypto_newsletter.core.scheduling.tasks.cleanup_old_articles",
        "schedule": crontab(minute=0, hour=2),  # Daily at 2 AM UTC
        "options": {"priority": 5},
    },
}

# Update Celery configuration
def update_celery_beat_schedule():
    """Update Celery Beat schedule with newsletter tasks."""
    celery_app.conf.beat_schedule.update(ENHANCED_CELERY_BEAT_SCHEDULE)
    return celery_app.conf.beat_schedule
```

### 2.2 Intelligent Scheduling System
```python
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_newsletter.shared.celery.app import celery_app
from crypto_newsletter.shared.database.connection import get_async_session
from crypto_newsletter.shared.models import Newsletter, ArticleAnalysis

logger = logging.getLogger(__name__)

class IntelligentScheduler:
    """Manages intelligent scheduling decisions for newsletter generation."""

    def __init__(self):
        self.min_articles_daily = 3
        self.min_articles_weekly = 5
        self.quality_threshold = 0.6

    async def should_generate_daily_newsletter(self) -> Dict[str, Any]:
        """Determine if daily newsletter should be generated."""

        async with get_async_session() as db:
            # Check if newsletter already exists for today
            today = datetime.utcnow().date()
            existing = await self._check_existing_newsletter(db, today, "DAILY")

            if existing:
                return {
                    "should_generate": False,
                    "reason": "already_exists",
                    "existing_newsletter_id": existing.id
                }

            # Check available analyzed articles
            articles = await self._get_daily_analyzed_articles(db)

            if len(articles) < self.min_articles_daily:
                return {
                    "should_generate": False,
                    "reason": "insufficient_articles",
                    "articles_found": len(articles),
                    "minimum_required": self.min_articles_daily
                }

            # Check article quality
            quality_articles = [
                a for a in articles
                if a.get('signal_strength', 0) >= self.quality_threshold
            ]

            if len(quality_articles) < self.min_articles_daily:
                return {
                    "should_generate": False,
                    "reason": "insufficient_quality",
                    "quality_articles": len(quality_articles),
                    "total_articles": len(articles)
                }

            return {
                "should_generate": True,
                "articles_available": len(articles),
                "quality_articles": len(quality_articles),
                "confidence": min(len(quality_articles) / 8.0, 1.0)  # Optimal is 8 articles
            }

    async def should_generate_weekly_newsletter(self) -> Dict[str, Any]:
        """Determine if weekly newsletter should be generated."""

        async with get_async_session() as db:
            # Check if weekly newsletter already exists for this week
            week_end = datetime.utcnow().date()
            existing = await self._check_existing_newsletter(db, week_end, "WEEKLY")

            if existing:
                return {
                    "should_generate": False,
                    "reason": "already_exists",
                    "existing_newsletter_id": existing.id
                }

            # Check available daily newsletters from past week
            daily_newsletters = await self._get_weekly_daily_newsletters(db)

            if len(daily_newsletters) < self.min_articles_weekly:
                return {
                    "should_generate": False,
                    "reason": "insufficient_daily_newsletters",
                    "daily_newsletters_found": len(daily_newsletters),
                    "minimum_required": self.min_articles_weekly
                }

            # Check quality of daily newsletters
            quality_newsletters = [
                n for n in daily_newsletters
                if n.editorial_quality_score and n.editorial_quality_score >= 0.7
            ]

            return {
                "should_generate": True,
                "daily_newsletters_available": len(daily_newsletters),
                "quality_newsletters": len(quality_newsletters),
                "synthesis_confidence": min(len(daily_newsletters) / 7.0, 1.0)
            }

    async def get_optimal_generation_time(self, newsletter_type: str) -> Optional[datetime]:
        """Calculate optimal time for newsletter generation based on content availability."""

        if newsletter_type == "DAILY":
            # Check if we have enough content now, or should wait
            decision = await self.should_generate_daily_newsletter()

            if decision["should_generate"]:
                return datetime.utcnow()
            elif decision["reason"] == "insufficient_articles":
                # Suggest waiting 2 hours for more articles to be analyzed
                return datetime.utcnow() + timedelta(hours=2)

        elif newsletter_type == "WEEKLY":
            decision = await self.should_generate_weekly_newsletter()

            if decision["should_generate"]:
                return datetime.utcnow()
            elif decision["reason"] == "insufficient_daily_newsletters":
                # Suggest waiting until next Sunday
                return datetime.utcnow() + timedelta(days=7)

        return None

# Global scheduler instance
intelligent_scheduler = IntelligentScheduler()
```

---

## 3. Newsletter Generation Monitoring Tasks

### 3.1 Generation Monitoring Task
```python
@celery_app.task(
    name="crypto_newsletter.newsletter.tasks.monitor_newsletter_generation",
    bind=True,
    queue="monitoring"
)
def monitor_newsletter_generation_task(self) -> Dict[str, Any]:
    """Monitor newsletter generation status and handle failures."""

    async def _monitor_generation() -> Dict[str, Any]:
        """Internal async monitoring function."""

        monitoring_results = {
            "monitoring_timestamp": datetime.utcnow().isoformat(),
            "daily_status": {},
            "weekly_status": {},
            "alerts": [],
            "actions_taken": []
        }

        try:
            async with get_async_session() as db:
                # Check daily newsletter status
                daily_status = await check_daily_newsletter_status(db)
                monitoring_results["daily_status"] = daily_status

                # Check weekly newsletter status
                weekly_status = await check_weekly_newsletter_status(db)
                monitoring_results["weekly_status"] = weekly_status

                # Check for missed newsletters
                missed_daily = await check_missed_daily_newsletters(db)
                if missed_daily:
                    monitoring_results["alerts"].append({
                        "type": "missed_daily_newsletter",
                        "details": missed_daily
                    })

                    # Trigger recovery generation
                    recovery_task = generate_daily_newsletter_task.delay(force_generation=True)
                    monitoring_results["actions_taken"].append({
                        "action": "trigger_daily_recovery",
                        "task_id": recovery_task.id
                    })

                # Check for failed generations
                failed_generations = await check_failed_generations(db)
                if failed_generations:
                    monitoring_results["alerts"].append({
                        "type": "failed_generations",
                        "count": len(failed_generations),
                        "details": failed_generations
                    })

                # Check system health for newsletter generation
                system_health = await check_newsletter_system_health(db)
                if system_health["status"] != "healthy":
                    monitoring_results["alerts"].append({
                        "type": "system_health_issue",
                        "details": system_health
                    })

                # Update monitoring metrics
                await update_monitoring_metrics(db, monitoring_results)

                return monitoring_results

        except Exception as exc:
            logger.error(f"Newsletter generation monitoring failed: {exc}")
            return {
                "status": "monitoring_failed",
                "error": str(exc),
                "monitoring_timestamp": datetime.utcnow().isoformat()
            }

    return asyncio.run(_monitor_generation())

async def check_daily_newsletter_status(db: AsyncSession) -> Dict[str, Any]:
    """Check status of daily newsletter generation."""

    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    # Check today's newsletter
    today_newsletter = await get_newsletter_by_date(db, today, "DAILY")
    yesterday_newsletter = await get_newsletter_by_date(db, yesterday, "DAILY")

    return {
        "today": {
            "date": today.isoformat(),
            "exists": today_newsletter is not None,
            "status": today_newsletter.publish_status if today_newsletter else None,
            "quality_score": today_newsletter.editorial_quality_score if today_newsletter else None
        },
        "yesterday": {
            "date": yesterday.isoformat(),
            "exists": yesterday_newsletter is not None,
            "status": yesterday_newsletter.publish_status if yesterday_newsletter else None,
            "quality_score": yesterday_newsletter.editorial_quality_score if yesterday_newsletter else None
        }
    }

async def check_missed_daily_newsletters(db: AsyncSession) -> List[Dict[str, Any]]:
    """Check for missed daily newsletters in the past week."""

    missed_newsletters = []

    for i in range(1, 8):  # Check past 7 days
        check_date = datetime.utcnow().date() - timedelta(days=i)
        newsletter = await get_newsletter_by_date(db, check_date, "DAILY")

        if not newsletter:
            # Check if there were analyzable articles on that date
            articles_available = await count_analyzable_articles_for_date(db, check_date)

            if articles_available >= 3:  # Sufficient articles were available
                missed_newsletters.append({
                    "date": check_date.isoformat(),
                    "articles_available": articles_available,
                    "days_ago": i
                })

    return missed_newsletters
```

### 3.2 Performance Metrics Update Task
```python
@celery_app.task(
    name="crypto_newsletter.newsletter.tasks.update_newsletter_metrics",
    bind=True,
    queue="monitoring"
)
def update_newsletter_metrics_task(self) -> Dict[str, Any]:
    """Update newsletter performance metrics from various sources."""

    async def _update_metrics() -> Dict[str, Any]:
        """Internal async metrics update function."""

        try:
            async with get_async_session() as db:
                # Get newsletters that need metrics updates
                newsletters_to_update = await get_newsletters_needing_metrics_update(db)

                updated_count = 0
                failed_count = 0

                for newsletter in newsletters_to_update:
                    try:
                        # Update email metrics
                        email_metrics = await fetch_email_metrics(newsletter.id)

                        # Update web metrics
                        web_metrics = await fetch_web_metrics(newsletter.id)

                        # Update engagement metrics
                        engagement_metrics = await calculate_engagement_metrics(newsletter.id)

                        # Store updated metrics
                        await store_newsletter_metrics(
                            db, newsletter.id, email_metrics, web_metrics, engagement_metrics
                        )

                        updated_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to update metrics for newsletter {newsletter.id}: {e}")
                        failed_count += 1

                return {
                    "status": "completed",
                    "newsletters_processed": len(newsletters_to_update),
                    "updated_successfully": updated_count,
                    "failed_updates": failed_count,
                    "update_timestamp": datetime.utcnow().isoformat()
                }

        except Exception as exc:
            logger.error(f"Newsletter metrics update failed: {exc}")
            return {
                "status": "failed",
                "error": str(exc),
                "update_timestamp": datetime.utcnow().isoformat()
            }

    return asyncio.run(_update_metrics())
```

---

## 4. Adaptive Scheduling Logic

### 4.1 Dynamic Schedule Adjustment
```python
class AdaptiveScheduler:
    """Manages adaptive scheduling based on system performance and content availability."""

    def __init__(self):
        self.performance_history = {}
        self.content_patterns = {}

    async def adjust_daily_schedule(self) -> Dict[str, Any]:
        """Adjust daily newsletter schedule based on content patterns."""

        # Analyze content availability patterns
        content_analysis = await self.analyze_content_patterns()

        # Analyze generation performance
        performance_analysis = await self.analyze_generation_performance()

        # Calculate optimal schedule
        optimal_time = self.calculate_optimal_daily_time(
            content_analysis, performance_analysis
        )

        return {
            "current_schedule": "06:00 UTC",
            "recommended_schedule": optimal_time,
            "adjustment_needed": optimal_time != "06:00",
            "reasoning": self.get_schedule_reasoning(content_analysis, performance_analysis)
        }

    async def analyze_content_patterns(self) -> Dict[str, Any]:
        """Analyze when quality content becomes available."""

        # This would analyze historical data to find patterns
        # For now, return default analysis
        return {
            "peak_content_hours": [4, 5, 6, 7],  # UTC hours when most quality content is available
            "content_quality_trend": "stable",
            "average_articles_by_hour": {
                "04:00": 2.3,
                "05:00": 4.1,
                "06:00": 5.8,
                "07:00": 6.2,
                "08:00": 5.1
            }
        }

    def calculate_optimal_daily_time(
        self,
        content_analysis: Dict[str, Any],
        performance_analysis: Dict[str, Any]
    ) -> str:
        """Calculate optimal time for daily newsletter generation."""

        # Simple logic - can be enhanced with ML
        peak_hours = content_analysis["peak_content_hours"]

        if performance_analysis["average_generation_time"] > 900:  # 15 minutes
            # If generation takes long, start earlier
            return f"{min(peak_hours):02d}:00"
        else:
            # Standard time when content is most available
            return "06:00"

# Global adaptive scheduler
adaptive_scheduler = AdaptiveScheduler()
```

---

## 5. Implementation Timeline

### Week 1: Core Scheduling
- **Days 1-2**: Implement enhanced Celery Beat configuration
- **Days 3-4**: Build intelligent scheduling system
- **Days 5-7**: Create monitoring tasks

### Week 2: Adaptive Features
- **Days 1-3**: Implement adaptive scheduling logic
- **Days 4-5**: Build performance tracking and metrics
- **Days 6-7**: Create failure recovery systems

### Week 3: Integration & Testing
- **Days 1-3**: Test complete scheduling system
- **Days 4-5**: Performance optimization and monitoring
- **Days 6-7**: Production deployment and validation

---

## 6. Success Metrics

### Scheduling Reliability
- **Newsletter Generation Success Rate**: >98% on-time generation
- **Schedule Adherence**: <5 minute variance from scheduled time
- **Failure Recovery**: <30 minutes to detect and recover from failures
- **System Uptime**: >99.5% scheduler availability

### Performance Optimization
- **Content Availability Prediction**: >85% accuracy in content readiness
- **Adaptive Scheduling**: 20% improvement in content quality through timing
- **Resource Utilization**: <70% peak system load during generation
- **Cost Efficiency**: <$0.50 total daily operational cost

---

*Sub-PRD Version: 1.0*
*Implementation Priority: Phase 6 - Automation*
*Dependencies: Newsletter generation tasks, publishing system*
*Estimated Effort: 3 weeks*
