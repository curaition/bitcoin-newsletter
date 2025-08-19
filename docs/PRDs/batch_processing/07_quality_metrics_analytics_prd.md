# Quality Metrics & Analytics System
## Sub-PRD 7: Comprehensive Newsletter Performance Tracking

### Executive Summary
Implement a comprehensive quality metrics and analytics system that tracks newsletter performance across editorial quality, reader engagement, signal accuracy, and business metrics. This system provides actionable insights for continuous improvement and validates the newsletter's unique value proposition.

---

## 1. Product Overview

### Objective
Create a robust analytics system that measures newsletter success across multiple dimensions, provides actionable insights for improvement, and validates the unique value of signal-based newsletter content.

### Analytics Architecture
```
Newsletter Data → Quality Assessment → Engagement Tracking → Signal Validation → Business Metrics → Insights Dashboard
       ↓               ↓                    ↓                  ↓                ↓                ↓
   Content Analysis  Editorial Scoring   Reader Behavior   Signal Accuracy   Revenue/Growth   Optimization
```

---

## 2. Editorial Quality Metrics System

### 2.1 Content Quality Assessment
```python
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_newsletter.shared.database.connection import get_async_session
from crypto_newsletter.shared.models import Newsletter, NewsletterMetrics
from crypto_newsletter.newsletter.analysis import ContentAnalyzer

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for a newsletter."""

    # Editorial Quality
    editorial_quality_score: float
    content_uniqueness_score: float
    signal_coherence_score: float
    synthesis_quality_score: float

    # Content Metrics
    word_count: int
    reading_time_minutes: int
    action_items_count: int
    source_citations_count: int

    # Signal Quality
    signals_featured: int
    signal_accuracy_score: float
    pattern_insights_count: int
    adjacent_connections_count: int

    # Engagement Predictors
    headline_strength_score: float
    executive_summary_clarity: float
    actionability_score: float

class NewsletterQualityAnalyzer:
    """Analyzes and scores newsletter quality across multiple dimensions."""

    def __init__(self):
        self.content_analyzer = ContentAnalyzer()
        self.quality_thresholds = {
            "editorial_quality_min": 0.7,
            "uniqueness_min": 0.8,
            "signal_coherence_min": 0.6,
            "synthesis_quality_min": 0.7
        }

    async def analyze_newsletter_quality(
        self,
        newsletter_id: int
    ) -> QualityMetrics:
        """Perform comprehensive quality analysis of a newsletter."""

        async with get_async_session() as db:
            newsletter = await self._get_newsletter_with_content(db, newsletter_id)

            if not newsletter:
                raise NewsletterNotFoundException(f"Newsletter {newsletter_id} not found")

            # Editorial Quality Analysis
            editorial_scores = await self._analyze_editorial_quality(newsletter)

            # Content Metrics Analysis
            content_metrics = await self._analyze_content_metrics(newsletter)

            # Signal Quality Analysis
            signal_metrics = await self._analyze_signal_quality(newsletter)

            # Engagement Prediction Analysis
            engagement_predictors = await self._analyze_engagement_predictors(newsletter)

            return QualityMetrics(
                # Editorial Quality
                editorial_quality_score=editorial_scores["overall_score"],
                content_uniqueness_score=editorial_scores["uniqueness_score"],
                signal_coherence_score=editorial_scores["coherence_score"],
                synthesis_quality_score=editorial_scores["synthesis_score"],

                # Content Metrics
                word_count=content_metrics["word_count"],
                reading_time_minutes=content_metrics["reading_time"],
                action_items_count=content_metrics["action_items"],
                source_citations_count=content_metrics["citations"],

                # Signal Quality
                signals_featured=signal_metrics["signals_count"],
                signal_accuracy_score=signal_metrics["accuracy_score"],
                pattern_insights_count=signal_metrics["patterns_count"],
                adjacent_connections_count=signal_metrics["connections_count"],

                # Engagement Predictors
                headline_strength_score=engagement_predictors["headline_score"],
                executive_summary_clarity=engagement_predictors["summary_clarity"],
                actionability_score=engagement_predictors["actionability"]
            )

    async def _analyze_editorial_quality(self, newsletter: Newsletter) -> Dict[str, float]:
        """Analyze editorial quality dimensions."""

        # Content uniqueness analysis
        uniqueness_score = await self._calculate_content_uniqueness(newsletter)

        # Signal coherence analysis
        coherence_score = await self._calculate_signal_coherence(newsletter)

        # Synthesis quality analysis
        synthesis_score = await self._calculate_synthesis_quality(newsletter)

        # Overall editorial score (weighted average)
        overall_score = (
            uniqueness_score * 0.3 +
            coherence_score * 0.3 +
            synthesis_score * 0.4
        )

        return {
            "overall_score": overall_score,
            "uniqueness_score": uniqueness_score,
            "coherence_score": coherence_score,
            "synthesis_score": synthesis_score
        }

    async def _calculate_content_uniqueness(self, newsletter: Newsletter) -> float:
        """Calculate how unique the newsletter content is vs mainstream crypto media."""

        # This would integrate with external APIs to compare content
        # For now, use synthesis data as proxy
        if newsletter.synthesis_themes:
            unique_insights = newsletter.synthesis_themes.get('unique_insights', [])
            mainstream_coverage = newsletter.synthesis_themes.get('mainstream_coverage', [])

            if len(unique_insights) + len(mainstream_coverage) > 0:
                uniqueness_ratio = len(unique_insights) / (len(unique_insights) + len(mainstream_coverage))
                return min(uniqueness_ratio * 1.2, 1.0)  # Boost unique content

        return 0.7  # Default score

    async def _calculate_signal_coherence(self, newsletter: Newsletter) -> float:
        """Calculate how well signals are integrated into the narrative."""

        if newsletter.signal_highlights and newsletter.pattern_insights:
            signals = newsletter.signal_highlights.get('featured_signals', [])
            patterns = newsletter.pattern_insights.get('patterns', [])

            # Check for cross-references between signals and patterns
            coherence_indicators = 0
            total_possible = len(signals) + len(patterns)

            if total_possible > 0:
                # Simple coherence calculation based on structured data
                coherence_indicators = len([s for s in signals if s.get('pattern_connection')])
                coherence_indicators += len([p for p in patterns if p.get('signal_support')])

                return min(coherence_indicators / total_possible, 1.0)

        return 0.6  # Default score

# Global quality analyzer
quality_analyzer = NewsletterQualityAnalyzer()
```

### 2.2 Signal Accuracy Tracking
```python
class SignalAccuracyTracker:
    """Tracks the accuracy of newsletter signals over time."""

    def __init__(self):
        self.validation_periods = [7, 14, 30]  # Days to track signal accuracy

    async def track_signal_accuracy(
        self,
        newsletter_id: int,
        validation_period_days: int = 30
    ) -> Dict[str, Any]:
        """Track accuracy of signals featured in newsletter."""

        async with get_async_session() as db:
            newsletter = await self._get_newsletter_with_signals(db, newsletter_id)

            if not newsletter or not newsletter.signal_highlights:
                return {"error": "No signals found for tracking"}

            signals = newsletter.signal_highlights.get('featured_signals', [])
            validation_results = []

            for signal in signals:
                validation = await self._validate_signal_accuracy(
                    signal, newsletter.publication_date, validation_period_days
                )
                validation_results.append(validation)

            # Calculate overall accuracy metrics
            accuracy_metrics = self._calculate_accuracy_metrics(validation_results)

            # Store validation results
            await self._store_signal_validation_results(
                db, newsletter_id, validation_results, accuracy_metrics
            )

            return {
                "newsletter_id": newsletter_id,
                "validation_period_days": validation_period_days,
                "signals_tracked": len(signals),
                "accuracy_metrics": accuracy_metrics,
                "individual_validations": validation_results
            }

    async def _validate_signal_accuracy(
        self,
        signal: Dict[str, Any],
        publication_date: datetime,
        validation_days: int
    ) -> Dict[str, Any]:
        """Validate accuracy of a specific signal."""

        # This would integrate with market data APIs, news APIs, etc.
        # to validate if the signal proved accurate

        signal_type = signal.get('type', 'unknown')
        prediction = signal.get('prediction', '')
        confidence = signal.get('confidence', 0.5)

        # Placeholder validation logic
        # In production, this would check actual market data
        validation_score = await self._check_signal_against_reality(
            signal_type, prediction, publication_date, validation_days
        )

        return {
            "signal_id": signal.get('id', ''),
            "signal_type": signal_type,
            "prediction": prediction,
            "original_confidence": confidence,
            "validation_score": validation_score,
            "validation_date": datetime.utcnow().isoformat(),
            "days_tracked": validation_days
        }

    def _calculate_accuracy_metrics(
        self,
        validation_results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate overall accuracy metrics from individual validations."""

        if not validation_results:
            return {"overall_accuracy": 0.0}

        total_score = sum(v["validation_score"] for v in validation_results)
        overall_accuracy = total_score / len(validation_results)

        # Calculate accuracy by signal type
        type_accuracies = {}
        for result in validation_results:
            signal_type = result["signal_type"]
            if signal_type not in type_accuracies:
                type_accuracies[signal_type] = []
            type_accuracies[signal_type].append(result["validation_score"])

        for signal_type, scores in type_accuracies.items():
            type_accuracies[signal_type] = sum(scores) / len(scores)

        return {
            "overall_accuracy": overall_accuracy,
            "accuracy_by_type": type_accuracies,
            "signals_validated": len(validation_results),
            "high_accuracy_signals": len([v for v in validation_results if v["validation_score"] > 0.7])
        }

# Global signal accuracy tracker
signal_tracker = SignalAccuracyTracker()
```

---

## 3. Reader Engagement Analytics

### 3.1 Engagement Metrics Collection
```python
class EngagementAnalytics:
    """Collects and analyzes reader engagement metrics."""

    def __init__(self):
        self.engagement_sources = ["email", "web", "social", "direct"]

    async def collect_engagement_metrics(
        self,
        newsletter_id: int
    ) -> Dict[str, Any]:
        """Collect comprehensive engagement metrics for a newsletter."""

        async with get_async_session() as db:
            # Email engagement metrics
            email_metrics = await self._collect_email_metrics(db, newsletter_id)

            # Web engagement metrics
            web_metrics = await self._collect_web_metrics(db, newsletter_id)

            # Social engagement metrics
            social_metrics = await self._collect_social_metrics(db, newsletter_id)

            # Reader feedback metrics
            feedback_metrics = await self._collect_feedback_metrics(db, newsletter_id)

            # Calculate composite engagement score
            engagement_score = self._calculate_engagement_score(
                email_metrics, web_metrics, social_metrics, feedback_metrics
            )

            return {
                "newsletter_id": newsletter_id,
                "collection_timestamp": datetime.utcnow().isoformat(),
                "email_metrics": email_metrics,
                "web_metrics": web_metrics,
                "social_metrics": social_metrics,
                "feedback_metrics": feedback_metrics,
                "composite_engagement_score": engagement_score
            }

    async def _collect_email_metrics(
        self,
        db: AsyncSession,
        newsletter_id: int
    ) -> Dict[str, Any]:
        """Collect email-specific engagement metrics."""

        # Get existing metrics from database
        metrics = await self._get_newsletter_metrics(db, newsletter_id)

        if not metrics:
            return {"error": "No email metrics found"}

        # Calculate derived metrics
        open_rate = (metrics.emails_opened / metrics.emails_sent * 100) if metrics.emails_sent > 0 else 0
        click_rate = (metrics.links_clicked / metrics.emails_opened * 100) if metrics.emails_opened > 0 else 0
        unsubscribe_rate = (metrics.emails_unsubscribed / metrics.emails_sent * 100) if metrics.emails_sent > 0 else 0

        return {
            "emails_sent": metrics.emails_sent,
            "emails_delivered": metrics.emails_delivered,
            "emails_opened": metrics.emails_opened,
            "links_clicked": metrics.links_clicked,
            "emails_unsubscribed": metrics.emails_unsubscribed,
            "open_rate_percent": round(open_rate, 2),
            "click_through_rate_percent": round(click_rate, 2),
            "unsubscribe_rate_percent": round(unsubscribe_rate, 2),
            "delivery_rate_percent": round((metrics.emails_delivered / metrics.emails_sent * 100), 2) if metrics.emails_sent > 0 else 0
        }

    def _calculate_engagement_score(
        self,
        email_metrics: Dict[str, Any],
        web_metrics: Dict[str, Any],
        social_metrics: Dict[str, Any],
        feedback_metrics: Dict[str, Any]
    ) -> float:
        """Calculate composite engagement score (0-100)."""

        score_components = []

        # Email engagement (40% weight)
        if "open_rate_percent" in email_metrics:
            email_score = (
                email_metrics["open_rate_percent"] * 0.4 +
                email_metrics["click_through_rate_percent"] * 0.6
            )
            score_components.append(("email", email_score * 0.4))

        # Web engagement (30% weight)
        if "bounce_rate_percent" in web_metrics:
            web_score = (
                (100 - web_metrics["bounce_rate_percent"]) * 0.3 +
                min(web_metrics["avg_time_on_page_seconds"] / 300 * 100, 100) * 0.7
            )
            score_components.append(("web", web_score * 0.3))

        # Social engagement (20% weight)
        if "total_shares" in social_metrics:
            social_score = min(social_metrics["total_shares"] * 10, 100)  # 10 shares = 100%
            score_components.append(("social", social_score * 0.2))

        # Reader feedback (10% weight)
        if "avg_rating" in feedback_metrics:
            feedback_score = feedback_metrics["avg_rating"] * 20  # 5-star to 100-point scale
            score_components.append(("feedback", feedback_score * 0.1))

        # Calculate weighted average
        if score_components:
            total_score = sum(score for _, score in score_components)
            return min(total_score, 100.0)

        return 0.0

# Global engagement analytics
engagement_analytics = EngagementAnalytics()
```

---

## 4. Business Metrics & ROI Tracking

### 4.1 Business Performance Metrics
```python
class BusinessMetricsTracker:
    """Tracks business performance and ROI metrics for the newsletter."""

    def __init__(self):
        self.cost_categories = ["generation", "distribution", "infrastructure", "analysis"]

    async def calculate_newsletter_roi(
        self,
        newsletter_id: int,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate ROI metrics for newsletter operations."""

        async with get_async_session() as db:
            # Calculate costs
            costs = await self._calculate_newsletter_costs(db, newsletter_id, time_period_days)

            # Calculate revenue/value metrics
            value_metrics = await self._calculate_newsletter_value(db, newsletter_id, time_period_days)

            # Calculate ROI
            roi_metrics = self._calculate_roi(costs, value_metrics)

            return {
                "newsletter_id": newsletter_id,
                "analysis_period_days": time_period_days,
                "costs": costs,
                "value_metrics": value_metrics,
                "roi_metrics": roi_metrics,
                "calculation_timestamp": datetime.utcnow().isoformat()
            }

    async def _calculate_newsletter_costs(
        self,
        db: AsyncSession,
        newsletter_id: int,
        days: int
    ) -> Dict[str, float]:
        """Calculate all costs associated with newsletter operations."""

        newsletter = await self._get_newsletter_with_costs(db, newsletter_id)

        # Direct generation costs
        generation_cost = newsletter.generation_cost_usd or 0.0

        # Estimated infrastructure costs (daily allocation)
        daily_infrastructure_cost = 2.50  # $2.50/day for Render services
        infrastructure_cost = daily_infrastructure_cost * (days / 30)  # Monthly allocation

        # Distribution costs (email service)
        distribution_cost = await self._calculate_distribution_costs(db, newsletter_id)

        # Analysis costs (signal validation, metrics collection)
        analysis_cost = 0.10  # Estimated $0.10 per newsletter for analysis

        total_cost = generation_cost + infrastructure_cost + distribution_cost + analysis_cost

        return {
            "generation_cost": generation_cost,
            "infrastructure_cost": infrastructure_cost,
            "distribution_cost": distribution_cost,
            "analysis_cost": analysis_cost,
            "total_cost": total_cost
        }

    async def _calculate_newsletter_value(
        self,
        db: AsyncSession,
        newsletter_id: int,
        days: int
    ) -> Dict[str, Any]:
        """Calculate value metrics for the newsletter."""

        # Subscriber value metrics
        subscriber_metrics = await self._calculate_subscriber_value(db, newsletter_id)

        # Content value metrics
        content_value = await self._calculate_content_value(db, newsletter_id)

        # Signal accuracy value
        signal_value = await self._calculate_signal_value(db, newsletter_id)

        return {
            "subscriber_value": subscriber_metrics,
            "content_value": content_value,
            "signal_value": signal_value,
            "total_estimated_value": (
                subscriber_metrics.get("total_value", 0) +
                content_value.get("total_value", 0) +
                signal_value.get("total_value", 0)
            )
        }

    def _calculate_roi(
        self,
        costs: Dict[str, float],
        value_metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate ROI metrics."""

        total_cost = costs["total_cost"]
        total_value = value_metrics["total_estimated_value"]

        if total_cost > 0:
            roi_ratio = (total_value - total_cost) / total_cost
            roi_percentage = roi_ratio * 100
        else:
            roi_ratio = 0
            roi_percentage = 0

        return {
            "roi_ratio": roi_ratio,
            "roi_percentage": roi_percentage,
            "cost_per_subscriber": total_cost / max(value_metrics["subscriber_value"].get("active_subscribers", 1), 1),
            "value_per_dollar": total_value / max(total_cost, 0.01),
            "break_even_subscribers": total_cost / 0.50 if total_cost > 0 else 0  # Assuming $0.50 value per subscriber
        }

# Global business metrics tracker
business_tracker = BusinessMetricsTracker()
```

---

## 5. Analytics Dashboard Integration

### 5.1 Metrics Aggregation Task
```python
@celery_app.task(
    name="crypto_newsletter.analytics.tasks.aggregate_newsletter_metrics",
    bind=True
)
def aggregate_newsletter_metrics_task(self, days_back: int = 7) -> Dict[str, Any]:
    """Aggregate comprehensive metrics for newsletter analytics dashboard."""

    async def _aggregate_metrics() -> Dict[str, Any]:
        """Internal async metrics aggregation function."""

        try:
            async with get_async_session() as db:
                # Get newsletters from specified period
                newsletters = await get_newsletters_for_period(db, days_back)

                aggregated_metrics = {
                    "period_days": days_back,
                    "newsletters_analyzed": len(newsletters),
                    "quality_metrics": {},
                    "engagement_metrics": {},
                    "business_metrics": {},
                    "signal_accuracy": {},
                    "trends": {},
                    "aggregation_timestamp": datetime.utcnow().isoformat()
                }

                # Aggregate quality metrics
                quality_scores = []
                for newsletter in newsletters:
                    quality = await quality_analyzer.analyze_newsletter_quality(newsletter.id)
                    quality_scores.append(quality)

                aggregated_metrics["quality_metrics"] = self._aggregate_quality_scores(quality_scores)

                # Aggregate engagement metrics
                engagement_scores = []
                for newsletter in newsletters:
                    engagement = await engagement_analytics.collect_engagement_metrics(newsletter.id)
                    engagement_scores.append(engagement)

                aggregated_metrics["engagement_metrics"] = self._aggregate_engagement_scores(engagement_scores)

                # Aggregate business metrics
                business_metrics = []
                for newsletter in newsletters:
                    business = await business_tracker.calculate_newsletter_roi(newsletter.id, days_back)
                    business_metrics.append(business)

                aggregated_metrics["business_metrics"] = self._aggregate_business_metrics(business_metrics)

                # Calculate trends
                aggregated_metrics["trends"] = await self._calculate_trends(db, days_back)

                # Store aggregated metrics
                await store_aggregated_metrics(db, aggregated_metrics)

                return aggregated_metrics

        except Exception as exc:
            logger.error(f"Metrics aggregation failed: {exc}")
            return {
                "status": "failed",
                "error": str(exc),
                "aggregation_timestamp": datetime.utcnow().isoformat()
            }

    return asyncio.run(_aggregate_metrics())
```

---

## 6. Implementation Timeline

### Week 1: Quality Metrics
- **Days 1-3**: Implement editorial quality assessment system
- **Days 4-5**: Build signal accuracy tracking
- **Days 6-7**: Create content uniqueness analysis

### Week 2: Engagement Analytics
- **Days 1-3**: Implement engagement metrics collection
- **Days 4-5**: Build reader behavior analytics
- **Days 6-7**: Create feedback and rating systems

### Week 3: Business Metrics & Integration
- **Days 1-3**: Implement business metrics and ROI tracking
- **Days 4-5**: Build metrics aggregation and dashboard integration
- **Days 6-7**: Testing and optimization

---

## 7. Success Metrics

### Quality Tracking
- **Editorial Quality**: >4.0/5.0 average across all newsletters
- **Content Uniqueness**: >85% unique insights vs mainstream media
- **Signal Accuracy**: >70% of signals prove relevant within 30 days
- **Synthesis Quality**: >0.75 average coherence score

### Engagement Performance
- **Email Open Rate**: >25% for daily, >30% for weekly
- **Click-Through Rate**: >8% for actionable content
- **Time on Page**: >5 minutes average reading time
- **Reader Satisfaction**: >4.2/5.0 average rating

### Business Value
- **Cost Efficiency**: <$0.50 per newsletter generation
- **Subscriber Growth**: >10% monthly growth rate
- **ROI**: >200% return on newsletter operations
- **Signal Value**: >60% of readers report actionable insights

---

*Sub-PRD Version: 1.0*
*Implementation Priority: Phase 7 - Analytics*
*Dependencies: All previous phases*
*Estimated Effort: 3 weeks*
