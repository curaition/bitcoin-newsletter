# Newsletter Generation Celery Tasks
## Sub-PRD 4: Automated Daily & Weekly Newsletter Generation

### Executive Summary
Implement comprehensive Celery tasks for automated daily and weekly newsletter generation, integrating the PydanticAI agent system with robust error handling, quality validation, and publishing workflows. This system enables fully automated newsletter production with manual override capabilities.

---

## 1. Product Overview

### Objective
Create production-ready Celery tasks that automatically generate, validate, and publish daily and weekly newsletters using the multi-agent system, with comprehensive error handling and quality assurance.

### Task Architecture
```
Scheduled Trigger → Article Selection → Agent Workflow → Quality Validation → Storage → Publishing
       ↓                  ↓               ↓               ↓            ↓         ↓
   Celery Beat      Filter Articles   Multi-Agent     Quality Gates   Database   Email/Web
```

---

## 2. Core Newsletter Generation Tasks

### 2.1 Daily Newsletter Generation Task
```python
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_newsletter.shared.celery.app import celery_app
from crypto_newsletter.shared.database.connection import get_async_session
from crypto_newsletter.shared.models import Article, ArticleAnalysis, Newsletter
from crypto_newsletter.newsletter.agents.orchestrator import newsletter_orchestrator
from crypto_newsletter.newsletter.storage import NewsletterStorage
from crypto_newsletter.newsletter.publishing import NewsletterPublisher

logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    name="crypto_newsletter.newsletter.tasks.generate_daily_newsletter",
    max_retries=2,
    default_retry_delay=1800,  # 30 minutes
    queue="newsletter"
)
def generate_daily_newsletter_task(self, force_generation: bool = False) -> Dict[str, Any]:
    """
    Generate daily newsletter from past 24 hours of analyzed articles.

    Args:
        force_generation: Generate even if insufficient articles

    Returns:
        Dict with generation results and metadata
    """

    async def _generate_daily_newsletter() -> Dict[str, Any]:
        """Internal async function for daily newsletter generation."""

        task_start = datetime.utcnow()
        generation_metadata = {
            "task_started_at": task_start.isoformat(),
            "newsletter_type": "DAILY",
            "force_generation": force_generation
        }

        try:
            async with get_async_session() as db:
                # Step 1: Get analyzed articles from past 24 hours
                daily_articles = await get_daily_analyzed_articles(db)

                logger.info(f"Found {len(daily_articles)} analyzed articles from past 24 hours")
                generation_metadata["articles_found"] = len(daily_articles)

                # Step 2: Quality check - ensure sufficient content
                if len(daily_articles) < 3 and not force_generation:
                    logger.warning(f"Insufficient articles for daily newsletter: {len(daily_articles)}")
                    return {
                        "status": "skipped",
                        "reason": "insufficient_content",
                        "articles_found": len(daily_articles),
                        "minimum_required": 3,
                        "generation_metadata": generation_metadata
                    }

                # Step 3: Check if newsletter already exists for today
                today = datetime.utcnow().date()
                existing_newsletter = await check_existing_newsletter(db, today, "DAILY")

                if existing_newsletter and not force_generation:
                    logger.info(f"Daily newsletter already exists for {today}")
                    return {
                        "status": "already_exists",
                        "newsletter_id": existing_newsletter.id,
                        "publication_date": today.isoformat(),
                        "generation_metadata": generation_metadata
                    }

                # Step 4: Generate newsletter using agent orchestrator
                logger.info("Starting newsletter generation with agent system")

                generation_result = await newsletter_orchestrator.generate_daily_newsletter(
                    articles=daily_articles,
                    newsletter_type="DAILY"
                )

                if not generation_result["success"]:
                    raise NewsletterGenerationException(
                        f"Agent generation failed: {generation_result.get('error', 'Unknown error')}"
                    )

                # Step 5: Quality validation
                quality_validation = validate_newsletter_quality(
                    generation_result["newsletter_content"],
                    generation_result["generation_metadata"]
                )

                if not quality_validation["passes_quality_gates"]:
                    logger.warning(f"Newsletter failed quality validation: {quality_validation['issues']}")

                    if not force_generation:
                        return {
                            "status": "quality_failed",
                            "quality_issues": quality_validation["issues"],
                            "generation_metadata": generation_metadata
                        }

                # Step 6: Store newsletter in database
                storage = NewsletterStorage()
                newsletter_id = await storage.store_newsletter(
                    db=db,
                    newsletter_content=generation_result["newsletter_content"],
                    story_selection=generation_result["story_selection"],
                    synthesis=generation_result["synthesis"],
                    generation_metadata=generation_result["generation_metadata"],
                    newsletter_type="DAILY",
                    publication_date=today
                )

                # Step 7: Calculate processing time and costs
                processing_time = (datetime.utcnow() - task_start).total_seconds()
                generation_metadata.update({
                    "processing_time_seconds": processing_time,
                    "newsletter_id": newsletter_id,
                    "quality_validation": quality_validation,
                    "task_completed_at": datetime.utcnow().isoformat()
                })

                logger.info(
                    f"Daily newsletter generated successfully - "
                    f"ID: {newsletter_id}, Time: {processing_time:.2f}s, "
                    f"Cost: ${generation_result['generation_metadata']['generation_cost']:.4f}"
                )

                # Step 8: Trigger publishing (async)
                publish_task = publish_newsletter_task.delay(newsletter_id, "email_and_web")

                return {
                    "status": "success",
                    "newsletter_id": newsletter_id,
                    "publication_date": today.isoformat(),
                    "articles_processed": len(daily_articles),
                    "stories_selected": len(generation_result["story_selection"].selected_stories),
                    "generation_cost": generation_result["generation_metadata"]["generation_cost"],
                    "processing_time_seconds": processing_time,
                    "quality_score": generation_result["newsletter_content"].editorial_quality_score,
                    "publish_task_id": publish_task.id,
                    "generation_metadata": generation_metadata
                }

        except Exception as exc:
            logger.error(f"Daily newsletter generation failed: {exc}")

            # Store failure record for monitoring
            await store_generation_failure(
                newsletter_type="DAILY",
                error=str(exc),
                metadata=generation_metadata
            )

            # Retry logic
            if self.request.retries < self.max_retries:
                retry_delay = 1800 * (self.request.retries + 1)  # Exponential backoff
                logger.warning(f"Retrying daily newsletter generation in {retry_delay} seconds")
                raise self.retry(countdown=retry_delay, exc=exc)

            return {
                "status": "failed",
                "error": str(exc),
                "retries_exhausted": True,
                "generation_metadata": generation_metadata
            }

    return asyncio.run(_generate_daily_newsletter())

async def get_daily_analyzed_articles(db: AsyncSession) -> List[Dict[str, Any]]:
    """Get analyzed articles from past 24 hours with quality filtering."""
    from sqlalchemy import select, and_, text

    query = text("""
        SELECT
            a.id, a.title, a.body, a.published_at, p.name as publisher,
            aa.weak_signals, aa.pattern_anomalies, aa.adjacent_connections,
            aa.signal_strength, aa.uniqueness_score, aa.analysis_confidence,
            aa.narrative_gaps, aa.edge_indicators
        FROM articles a
        JOIN article_analyses aa ON a.id = aa.article_id
        JOIN publishers p ON a.publisher_id = p.id
        WHERE a.published_at >= NOW() - INTERVAL '24 hours'
          AND aa.signal_strength > 0.6
          AND aa.uniqueness_score > 0.7
          AND aa.analysis_confidence > 0.75
          AND LENGTH(a.body) > 1000
        ORDER BY aa.signal_strength DESC, aa.uniqueness_score DESC, a.published_at DESC
        LIMIT 20
    """)

    result = await db.execute(query)
    rows = result.fetchall()

    # Convert to dictionaries for agent processing
    articles = []
    for row in rows:
        articles.append({
            "id": row.id,
            "title": row.title,
            "body": row.body,
            "published_at": row.published_at.isoformat(),
            "publisher": row.publisher,
            "weak_signals": row.weak_signals or [],
            "pattern_anomalies": row.pattern_anomalies or [],
            "adjacent_connections": row.adjacent_connections or [],
            "signal_strength": float(row.signal_strength) if row.signal_strength else 0.0,
            "uniqueness_score": float(row.uniqueness_score) if row.uniqueness_score else 0.0,
            "analysis_confidence": float(row.analysis_confidence) if row.analysis_confidence else 0.0,
            "narrative_gaps": row.narrative_gaps or [],
            "edge_indicators": row.edge_indicators or []
        })

    return articles
```

### 2.2 Weekly Newsletter Generation Task
```python
@celery_app.task(
    bind=True,
    name="crypto_newsletter.newsletter.tasks.generate_weekly_newsletter",
    max_retries=2,
    default_retry_delay=3600,  # 1 hour
    queue="newsletter"
)
def generate_weekly_newsletter_task(self, force_generation: bool = False) -> Dict[str, Any]:
    """
    Generate weekly newsletter synthesizing past 7 daily newsletters.

    Args:
        force_generation: Generate even if insufficient daily newsletters

    Returns:
        Dict with generation results and metadata
    """

    async def _generate_weekly_newsletter() -> Dict[str, Any]:
        """Internal async function for weekly newsletter generation."""

        task_start = datetime.utcnow()
        generation_metadata = {
            "task_started_at": task_start.isoformat(),
            "newsletter_type": "WEEKLY",
            "force_generation": force_generation
        }

        try:
            async with get_async_session() as db:
                # Step 1: Get past week's daily newsletters
                weekly_data = await get_weekly_newsletter_data(db)

                logger.info(f"Found {len(weekly_data['daily_newsletters'])} daily newsletters from past week")
                generation_metadata["daily_newsletters_found"] = len(weekly_data['daily_newsletters'])

                # Step 2: Quality check - ensure sufficient daily content
                if len(weekly_data['daily_newsletters']) < 5 and not force_generation:
                    logger.warning(f"Insufficient daily newsletters for weekly synthesis: {len(weekly_data['daily_newsletters'])}")
                    return {
                        "status": "skipped",
                        "reason": "insufficient_daily_content",
                        "daily_newsletters_found": len(weekly_data['daily_newsletters']),
                        "minimum_required": 5,
                        "generation_metadata": generation_metadata
                    }

                # Step 3: Check if weekly newsletter already exists
                week_end = datetime.utcnow().date()
                existing_newsletter = await check_existing_newsletter(db, week_end, "WEEKLY")

                if existing_newsletter and not force_generation:
                    logger.info(f"Weekly newsletter already exists for week ending {week_end}")
                    return {
                        "status": "already_exists",
                        "newsletter_id": existing_newsletter.id,
                        "publication_date": week_end.isoformat(),
                        "generation_metadata": generation_metadata
                    }

                # Step 4: Generate weekly newsletter using specialized agent
                logger.info("Starting weekly newsletter generation with synthesis agent")

                weekly_generation_result = await newsletter_orchestrator.generate_weekly_newsletter(
                    weekly_data=weekly_data,
                    newsletter_type="WEEKLY"
                )

                if not weekly_generation_result["success"]:
                    raise NewsletterGenerationException(
                        f"Weekly generation failed: {weekly_generation_result.get('error', 'Unknown error')}"
                    )

                # Step 5: Enhanced quality validation for weekly content
                quality_validation = validate_weekly_newsletter_quality(
                    weekly_generation_result["newsletter_content"],
                    weekly_generation_result["generation_metadata"],
                    weekly_data
                )

                if not quality_validation["passes_quality_gates"] and not force_generation:
                    return {
                        "status": "quality_failed",
                        "quality_issues": quality_validation["issues"],
                        "generation_metadata": generation_metadata
                    }

                # Step 6: Store weekly newsletter with synthesis data
                storage = NewsletterStorage()
                newsletter_id = await storage.store_weekly_newsletter(
                    db=db,
                    newsletter_content=weekly_generation_result["newsletter_content"],
                    weekly_synthesis=weekly_generation_result["weekly_synthesis"],
                    daily_newsletters=weekly_data['daily_newsletters'],
                    generation_metadata=weekly_generation_result["generation_metadata"],
                    publication_date=week_end
                )

                # Step 7: Calculate processing metrics
                processing_time = (datetime.utcnow() - task_start).total_seconds()
                generation_metadata.update({
                    "processing_time_seconds": processing_time,
                    "newsletter_id": newsletter_id,
                    "quality_validation": quality_validation,
                    "task_completed_at": datetime.utcnow().isoformat()
                })

                logger.info(
                    f"Weekly newsletter generated successfully - "
                    f"ID: {newsletter_id}, Time: {processing_time:.2f}s, "
                    f"Daily newsletters synthesized: {len(weekly_data['daily_newsletters'])}"
                )

                # Step 8: Trigger weekly publishing (different subscriber list)
                publish_task = publish_newsletter_task.delay(newsletter_id, "weekly_subscribers")

                return {
                    "status": "success",
                    "newsletter_id": newsletter_id,
                    "publication_date": week_end.isoformat(),
                    "daily_newsletters_synthesized": len(weekly_data['daily_newsletters']),
                    "generation_cost": weekly_generation_result["generation_metadata"]["generation_cost"],
                    "processing_time_seconds": processing_time,
                    "quality_score": weekly_generation_result["newsletter_content"].editorial_quality_score,
                    "publish_task_id": publish_task.id,
                    "generation_metadata": generation_metadata
                }

        except Exception as exc:
            logger.error(f"Weekly newsletter generation failed: {exc}")

            await store_generation_failure(
                newsletter_type="WEEKLY",
                error=str(exc),
                metadata=generation_metadata
            )

            if self.request.retries < self.max_retries:
                retry_delay = 3600 * (self.request.retries + 1)
                logger.warning(f"Retrying weekly newsletter generation in {retry_delay} seconds")
                raise self.retry(countdown=retry_delay, exc=exc)

            return {
                "status": "failed",
                "error": str(exc),
                "retries_exhausted": True,
                "generation_metadata": generation_metadata
            }

    return asyncio.run(_generate_weekly_newsletter())

async def get_weekly_newsletter_data(db: AsyncSession) -> Dict[str, Any]:
    """Aggregate data from past week for weekly synthesis."""
    from sqlalchemy import select, text

    # Get daily newsletters from past 7 days
    daily_query = text("""
        SELECT
            id, publication_date, title, synthesis_themes, pattern_insights,
            signal_highlights, editorial_quality_score, selected_articles
        FROM newsletters
        WHERE publication_date >= CURRENT_DATE - INTERVAL '7 days'
          AND newsletter_type = 'DAILY'
          AND publish_status = 'PUBLISHED'
        ORDER BY publication_date DESC
    """)

    daily_result = await db.execute(daily_query)
    daily_newsletters = [dict(row._mapping) for row in daily_result.fetchall()]

    # Aggregate weekly signals from articles covered in daily newsletters
    if daily_newsletters:
        all_article_ids = []
        for newsletter in daily_newsletters:
            if newsletter['selected_articles']:
                all_article_ids.extend(newsletter['selected_articles'])

        if all_article_ids:
            # Get aggregated signal data
            signals_query = text("""
                SELECT
                    aa.weak_signals,
                    aa.pattern_anomalies,
                    aa.adjacent_connections,
                    AVG(aa.signal_strength) as avg_signal_strength,
                    COUNT(*) as article_count
                FROM article_analyses aa
                WHERE aa.article_id = ANY(:article_ids)
            """)

            signals_result = await db.execute(signals_query, {"article_ids": all_article_ids})
            aggregated_signals = signals_result.fetchone()
        else:
            aggregated_signals = None
    else:
        aggregated_signals = None

    return {
        "daily_newsletters": daily_newsletters,
        "aggregated_signals": dict(aggregated_signals._mapping) if aggregated_signals else {},
        "pattern_evolution": analyze_pattern_evolution(daily_newsletters),
        "synthesis_period": {
            "start": (datetime.utcnow().date() - timedelta(days=7)).isoformat(),
            "end": datetime.utcnow().date().isoformat()
        }
    }
```

---

## 3. Quality Validation System

### 3.1 Newsletter Quality Gates
```python
class NewsletterQualityValidator:
    """Validates newsletter quality before publishing."""

    @staticmethod
    def validate_newsletter_quality(
        newsletter_content: Any,
        generation_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate daily newsletter quality."""

        issues = []
        warnings = []

        # Content length validation
        if len(newsletter_content.main_analysis) < 800:
            issues.append("Main analysis too short (<800 words)")
        elif len(newsletter_content.main_analysis) > 1500:
            warnings.append("Main analysis very long (>1500 words)")

        # Quality score validation
        if newsletter_content.editorial_quality_score < 0.7:
            issues.append(f"Editorial quality score too low: {newsletter_content.editorial_quality_score}")

        # Executive summary validation
        if len(newsletter_content.executive_summary) < 3:
            issues.append("Executive summary has fewer than 3 key points")

        # Action items validation
        if len(newsletter_content.action_items) < 2:
            warnings.append("Fewer than 2 action items provided")

        # Source citations validation
        if len(newsletter_content.source_citations) < 3:
            issues.append("Insufficient source citations (<3)")

        # Generation metadata validation
        if generation_metadata.get("stories_selected", 0) < 3:
            issues.append("Too few stories selected for newsletter")

        passes_quality_gates = len(issues) == 0

        return {
            "passes_quality_gates": passes_quality_gates,
            "issues": issues,
            "warnings": warnings,
            "quality_score": newsletter_content.editorial_quality_score,
            "validation_timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def validate_weekly_newsletter_quality(
        newsletter_content: Any,
        generation_metadata: Dict[str, Any],
        weekly_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate weekly newsletter quality with additional checks."""

        # Start with daily validation
        base_validation = NewsletterQualityValidator.validate_newsletter_quality(
            newsletter_content, generation_metadata
        )

        issues = base_validation["issues"]
        warnings = base_validation["warnings"]

        # Weekly-specific validations
        if len(weekly_data["daily_newsletters"]) < 5:
            issues.append(f"Insufficient daily newsletters for synthesis: {len(weekly_data['daily_newsletters'])}")

        # Strategic insight validation for weekly content
        if len(newsletter_content.main_analysis) < 1200:
            issues.append("Weekly analysis too short (<1200 words) - should be more comprehensive")

        # Pattern evolution validation
        if not weekly_data.get("pattern_evolution"):
            warnings.append("No pattern evolution data available for weekly synthesis")

        passes_quality_gates = len(issues) == 0

        return {
            "passes_quality_gates": passes_quality_gates,
            "issues": issues,
            "warnings": warnings,
            "quality_score": newsletter_content.editorial_quality_score,
            "weekly_specific_checks": True,
            "validation_timestamp": datetime.utcnow().isoformat()
        }

# Global validator instance
quality_validator = NewsletterQualityValidator()
```

---

## 4. Implementation Timeline

### Week 1: Core Task Development
- **Days 1-3**: Implement daily newsletter generation task
- **Days 4-5**: Build weekly newsletter generation task
- **Days 6-7**: Create quality validation system

### Week 2: Integration & Testing
- **Days 1-3**: Integrate with agent orchestrator and database
- **Days 4-5**: Test error handling and retry logic
- **Days 6-7**: Performance optimization and monitoring

### Week 3: Production Deployment
- **Days 1-2**: Deploy tasks to production environment
- **Days 3-7**: Monitor first week of automated generation

---

## 5. Success Metrics

### Task Performance
- **Generation Success Rate**: >95% successful newsletter generation
- **Processing Time**: Daily <15 minutes, Weekly <30 minutes
- **Quality Gate Pass Rate**: >90% of newsletters pass quality validation
- **Error Recovery**: <5% retry rate with 100% eventual success

### Content Quality
- **Editorial Quality Score**: >4.0/5.0 average across all newsletters
- **Reader Engagement**: >25% email open rate, >60% read completion
- **Content Uniqueness**: >85% unique insights vs mainstream media

---

*Sub-PRD Version: 1.0*
*Implementation Priority: Phase 4 - Automation*
*Dependencies: Newsletter agents, enhanced database schema*
*Estimated Effort: 3 weeks*
