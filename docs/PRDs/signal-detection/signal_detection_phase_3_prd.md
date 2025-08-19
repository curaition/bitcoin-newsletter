# Signal Detection Phase 3: Production Integration & Celery Tasks
## Product Requirements Document (PRD)

### Executive Summary
Integrate AI signal detection agents into the production pipeline by extending the existing Celery task system. This phase implements automated analysis scheduling, manages processing queues, and ensures reliable analysis execution with comprehensive error handling and cost controls.

---

## 1. Product Overview

### Vision
Transform the tested AI agents from Phase 2 into a production-ready analysis pipeline that automatically processes analysis-ready articles with robust scheduling, error handling, and cost management.

### Core Value Proposition
- **Automated Analysis**: Seamless integration with existing 4-hour ingestion cycle
- **Production Reliability**: Robust error handling and recovery mechanisms
- **Cost Management**: Strict budget controls and usage optimization
- **Operational Visibility**: Complete monitoring of analysis pipeline performance
- **Quality Assurance**: Only analyze high-value content for maximum ROI

---

## 2. Prerequisites & Foundation

### Phase 1 & 2 Deliverables Required
- ✅ Database schema with analysis tables ready for data storage
- ✅ Admin interface showing analysis-ready articles and pipeline status
- ✅ ContentAnalysisAgent and SignalValidationAgent tested and operational
- ✅ Agent orchestration system with error handling

### Current Production Environment
- **Celery Workers**: 1 active worker processing tasks
- **Celery Beat**: 4-hour scheduled ingestion cycle operational
- **Redis**: Task queue and caching infrastructure ready
- **Daily Volume**: ~35 analysis-ready articles requiring processing

---

## 3. Functional Requirements

### 3.1 Celery Task Integration
**Primary Responsibility**: Extend existing Celery infrastructure to include analysis tasks

**Core Task Implementation**:

#### Analysis Queue Management
```python
# src/crypto_newsletter/analysis/tasks.py
from celery import Celery
from crypto_newsletter.shared.celery import celery_app
from crypto_newsletter.analysis.agents import AnalysisWorkflow

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def analyze_article(self, article_id: int):
    """Analyze a single article for signals and patterns"""
    try:
        workflow = AnalysisWorkflow()

        # Check if article is analysis-worthy
        article = await workflow.get_article(article_id)
        if not workflow.is_analysis_worthy(article):
            return {
                "status": "SKIPPED",
                "reason": "Article not eligible for analysis",
                "article_id": article_id
            }

        # Check daily budget before processing
        if not await workflow.check_daily_budget():
            return {
                "status": "BUDGET_EXCEEDED",
                "reason": "Daily analysis budget exceeded",
                "article_id": article_id
            }

        # Perform analysis
        result = await workflow.analyze_article(article_id)

        # Log success and update metrics
        await workflow.log_analysis_success(article_id, result)

        return {
            "status": "COMPLETED",
            "article_id": article_id,
            "signals_detected": len(result.analysis.weak_signals),
            "processing_time": result.processing_time,
            "cost": result.cost
        }

    except Exception as exc:
        # Log error details
        await workflow.log_analysis_error(article_id, str(exc))

        # Determine retry strategy
        if self.request.retries < self.max_retries:
            # Exponential backoff with jitter
            countdown = 300 * (2 ** self.request.retries) + random.randint(0, 60)
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # Mark as permanently failed
            await workflow.mark_analysis_failed(article_id, str(exc))
            return {
                "status": "FAILED",
                "article_id": article_id,
                "error": str(exc)
            }

@celery_app.task
def process_analysis_queue():
    """Process all pending analysis-ready articles"""
    try:
        # Get articles needing analysis (full articles only)
        pending_articles = await get_pending_analysis_articles()

        analysis_count = 0
        for article in pending_articles:
            # Check if already analyzed or in progress
            if await is_analysis_complete(article.id):
                continue

            # Queue analysis task
            analyze_article.delay(article.id)
            analysis_count += 1

            # Rate limiting: don't overwhelm the queue
            if analysis_count >= 50:  # Process max 50 at once
                break

        return {
            "status": "QUEUED",
            "articles_queued": analysis_count,
            "total_pending": len(pending_articles)
        }

    except Exception as exc:
        logger.error(f"Failed to process analysis queue: {exc}")
        raise

async def get_pending_analysis_articles() -> List[Article]:
    """Get articles that need analysis (≥2000 chars, quality publishers)"""
    quality_publishers = ["NewsBTC", "CoinDesk", "Crypto Potato"]

    query = select(Article).join(Publisher).where(
        Article.status == "ACTIVE",
        func.length(Article.body) >= 2000,
        Publisher.name.in_(quality_publishers),
        ~exists(select(ArticleAnalysis).where(ArticleAnalysis.article_id == Article.id))
    ).order_by(Article.published_on.desc())

    result = await db.execute(query)
    return result.scalars().all()
```

#### Scheduling Integration
```python
# src/crypto_newsletter/shared/celery.py - Update beat schedule
CELERYBEAT_SCHEDULE = {
    # Existing ingestion schedule
    'ingest-rss-feeds': {
        'task': 'crypto_newsletter.core.tasks.ingest_all_feeds',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
    },

    # New analysis scheduling
    'process-analysis-queue': {
        'task': 'crypto_newsletter.analysis.tasks.process_analysis_queue',
        'schedule': crontab(minute=30, hour='*/4'),  # 30 minutes after ingestion
    },

    'daily-analysis-metrics': {
        'task': 'crypto_newsletter.analysis.tasks.generate_daily_metrics',
        'schedule': crontab(minute=0, hour=2),  # Daily at 2 AM
    },

    'budget-reset': {
        'task': 'crypto_newsletter.analysis.tasks.reset_daily_budget',
        'schedule': crontab(minute=0, hour=0),  # Daily at midnight
    }
}
```

**Technical Requirements**:
- Integrate with existing Celery worker infrastructure
- Use Redis for task queuing and result caching
- Implement task prioritization (newest articles first)
- Add comprehensive task monitoring and logging

**Success Criteria**:
- All analysis-ready articles processed within 4 hours of ingestion
- Task failure rate <5%
- Queue processing time <30 minutes for daily volume
- Zero data loss during task execution

### 3.2 Cost Management & Budget Controls
**Primary Responsibility**: Implement strict budget controls to prevent cost overruns

**Core Budget Management**:

#### Daily Budget Tracking
```python
# src/crypto_newsletter/analysis/budget.py
class BudgetManager:
    def __init__(self):
        self.daily_budget_usd = 15.00  # Conservative daily budget
        self.cost_per_analysis_target = 0.25  # Target cost per article
        self.emergency_stop_threshold = 0.90  # Stop at 90% of budget

    async def check_daily_budget(self) -> bool:
        """Check if daily budget allows for more analysis"""
        today_cost = await self.get_daily_cost()
        remaining_budget = self.daily_budget_usd - today_cost

        # Check if we have budget for at least one analysis
        if remaining_budget < self.cost_per_analysis_target:
            await self.log_budget_exhausted()
            return False

        # Emergency stop if approaching budget limit
        if today_cost >= (self.daily_budget_usd * self.emergency_stop_threshold):
            await self.trigger_emergency_stop()
            return False

        return True

    async def get_daily_cost(self) -> float:
        """Calculate total cost for today's analyses"""
        today = datetime.now().date()
        query = select(func.sum(ArticleAnalysis.cost_usd)).where(
            ArticleAnalysis.created_at >= today,
            ArticleAnalysis.created_at < today + timedelta(days=1)
        )
        result = await db.execute(query)
        return result.scalar() or 0.0

    async def track_analysis_cost(self, article_id: int, cost: float):
        """Track cost for individual analysis"""
        await self.store_cost_record(article_id, cost)

        # Alert if single analysis exceeds target
        if cost > self.cost_per_analysis_target * 2:
            await self.alert_high_cost_analysis(article_id, cost)

    async def get_budget_status(self) -> BudgetStatus:
        """Get current budget status for monitoring"""
        today_cost = await self.get_daily_cost()
        today_analyses = await self.get_daily_analysis_count()

        return BudgetStatus(
            daily_budget=self.daily_budget_usd,
            spent_today=today_cost,
            remaining_budget=self.daily_budget_usd - today_cost,
            analyses_today=today_analyses,
            avg_cost_per_analysis=today_cost / max(today_analyses, 1),
            budget_utilization=today_cost / self.daily_budget_usd
        )
```

#### Cost Optimization Strategies
```python
class CostOptimizer:
    def __init__(self):
        self.token_limits = {
            'content_analysis': 3500,  # Max tokens for content analysis
            'validation': 2000,        # Max tokens for validation
        }
        self.retry_cost_threshold = 0.10  # Don't retry if single attempt costs this much

    def optimize_analysis_parameters(self, article: Article) -> AnalysisConfig:
        """Optimize analysis parameters based on article characteristics"""
        config = AnalysisConfig()

        # Adjust validation depth based on signal strength expectations
        if article.publisher.name in ["NewsBTC", "CoinDesk"]:
            config.validation_depth = "FULL"  # High-quality sources get full validation
        else:
            config.validation_depth = "BASIC"  # Others get basic validation

        # Adjust analysis scope based on content length
        if len(article.body) > 5000:
            config.signal_detection_depth = "DEEP"
        else:
            config.signal_detection_depth = "STANDARD"

        return config

    async def should_retry_analysis(self, article_id: int, error: Exception, attempt_cost: float) -> bool:
        """Determine if analysis should be retried based on cost and error type"""
        if attempt_cost > self.retry_cost_threshold:
            return False  # Don't retry expensive failures

        if isinstance(error, (RateLimitError, TemporaryAPIError)):
            return True  # Retry temporary issues

        if isinstance(error, (ValidationError, ParseError)):
            return False  # Don't retry fundamental errors

        return True  # Default to retry
```

**Technical Requirements**:
- Real-time cost tracking per analysis
- Automatic budget enforcement with hard stops
- Cost optimization based on article characteristics
- Daily budget reporting and alerting

**Success Criteria**:
- Daily costs stay within $15.00 budget
- Average cost per analysis <$0.25
- Zero budget overruns due to runaway processes
- Cost tracking accuracy >99%

### 3.3 Error Handling & Recovery
**Primary Responsibility**: Ensure robust analysis pipeline with comprehensive error recovery

**Core Error Handling**:

#### Analysis Error Classification
```python
class AnalysisErrorHandler:
    def __init__(self):
        self.error_categories = {
            'TEMPORARY': [RateLimitError, TimeoutError, ConnectionError],
            'PERMANENT': [ValidationError, AuthenticationError, ParseError],
            'BUDGET': [CostLimitError, BudgetExceededError],
            'CONTENT': [ContentTooShortError, LanguageNotSupportedError]
        }

        self.retry_strategies = {
            'TEMPORARY': {'max_retries': 3, 'backoff': 'exponential'},
            'PERMANENT': {'max_retries': 0, 'backoff': None},
            'BUDGET': {'max_retries': 0, 'backoff': None, 'delay_until': 'budget_reset'},
            'CONTENT': {'max_retries': 0, 'backoff': None}
        }

    async def handle_analysis_error(self, article_id: int, error: Exception, attempt: int) -> ErrorHandlingDecision:
        """Determine how to handle analysis error"""
        error_category = self.classify_error(error)
        strategy = self.retry_strategies[error_category]

        if attempt >= strategy['max_retries']:
            return ErrorHandlingDecision(
                action='FAIL_PERMANENTLY',
                reason=f'Max retries exceeded for {error_category} error'
            )

        if error_category == 'TEMPORARY':
            delay = self.calculate_backoff_delay(attempt, strategy['backoff'])
            return ErrorHandlingDecision(
                action='RETRY',
                delay=delay,
                reason=f'Temporary error, retry #{attempt + 1}'
            )

        if error_category == 'BUDGET':
            return ErrorHandlingDecision(
                action='DEFER_TO_NEXT_BUDGET_CYCLE',
                delay=self.time_until_budget_reset(),
                reason='Budget exceeded, defer until reset'
            )

        return ErrorHandlingDecision(
            action='FAIL_PERMANENTLY',
            reason=f'Permanent error: {str(error)}'
        )

    async def log_error_patterns(self):
        """Monitor error patterns for system health insights"""
        recent_errors = await self.get_recent_errors(hours=24)
        error_patterns = self.analyze_error_patterns(recent_errors)

        if error_patterns.failure_rate > 0.10:  # >10% failure rate
            await self.alert_high_failure_rate(error_patterns)

        if error_patterns.budget_hits > 3:  # Budget exceeded multiple times
            await self.alert_budget_pressure(error_patterns)
```

#### Queue Management & Prioritization
```python
class AnalysisQueueManager:
    def __init__(self):
        self.priority_publishers = ["NewsBTC", "CoinDesk", "Crypto Potato"]
        self.max_concurrent_analyses = 5  # Limit concurrent processing
        self.queue_processing_timeout = 1800  # 30 minutes max

    async def prioritize_analysis_queue(self) -> List[Article]:
        """Prioritize articles for analysis based on quality and freshness"""
        pending_articles = await get_pending_analysis_articles()

        # Sort by priority: quality publishers first, then by recency
        prioritized = sorted(pending_articles, key=lambda article: (
            0 if article.publisher.name in self.priority_publishers else 1,
            -article.published_on.timestamp()  # Negative for reverse chronological
        ))

        return prioritized

    async def manage_processing_rate(self):
        """Control processing rate to avoid overwhelming systems"""
        active_analyses = await self.count_active_analysis_tasks()

        if active_analyses >= self.max_concurrent_analyses:
            # Wait for some analyses to complete
            await asyncio.sleep(60)
            return False

        return True  # OK to process more

    async def handle_queue_backlog(self):
        """Handle situations where analysis queue grows too large"""
        queue_size = await self.get_queue_size()

        if queue_size > 100:  # Large backlog
            # Implement triage: only process highest priority articles
            await self.enable_triage_mode()

            # Alert administrators
            await self.alert_queue_backlog(queue_size)
```

**Technical Requirements**:
- Comprehensive error classification and handling
- Intelligent retry logic with exponential backoff
- Queue management with priority processing
- Error pattern analysis and alerting

**Success Criteria**:
- Analysis success rate >95%
- Queue processing completes within 4 hours of ingestion
- Error recovery success rate >90%
- Zero permanent data loss due to processing errors

---

## 4. Technical Specifications

### 4.1 Celery Configuration Updates
```python
# src/crypto_newsletter/shared/celery.py - Enhanced configuration
CELERY_CONFIG = {
    # Task routing
    'task_routes': {
        'crypto_newsletter.analysis.tasks.analyze_article': {'queue': 'analysis'},
        'crypto_newsletter.analysis.tasks.process_analysis_queue': {'queue': 'management'},
        'crypto_newsletter.core.tasks.*': {'queue': 'ingestion'},
    },

    # Worker configuration
    'worker_prefetch_multiplier': 2,  # Limit prefetching for analysis tasks
    'task_acks_late': True,           # Acknowledge tasks only after completion
    'worker_disable_rate_limits': False,

    # Task time limits
    'task_time_limit': 900,           # 15 minutes hard limit
    'task_soft_time_limit': 600,      # 10 minutes soft limit

    # Result backend configuration
    'result_expires': 86400,          # Keep results for 24 hours
    'result_persistent': True,

    # Analysis-specific settings
    'analysis_queue_max_length': 200,
    'analysis_retry_policy': {
        'max_retries': 3,
        'interval_start': 300,        # 5 minutes
        'interval_step': 300,         # Increase by 5 minutes each retry
        'interval_max': 1800,         # Max 30 minutes between retries
    }
}
```

### 4.2 Database Updates for Task Tracking
```sql
-- Task execution tracking
CREATE TABLE analysis_task_executions (
    id BIGSERIAL PRIMARY KEY,
    article_id BIGINT REFERENCES articles(id) NOT NULL,
    task_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILURE', 'RETRY')),

    -- Execution details
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    processing_time_seconds INTEGER,

    -- Error tracking
    error_message TEXT,
    error_category VARCHAR(50),
    retry_count INTEGER DEFAULT 0,

    -- Cost tracking
    cost_usd DECIMAL(6,4),
    token_usage INTEGER,

    -- Metadata
    worker_name VARCHAR(255),
    queue_name VARCHAR(100),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analysis_task_executions_article_id ON analysis_task_executions(article_id);
CREATE INDEX idx_analysis_task_executions_status ON analysis_task_executions(status);
CREATE INDEX idx_analysis_task_executions_started_at ON analysis_task_executions(started_at);

-- Daily budget tracking
CREATE TABLE daily_budget_tracking (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    -- Budget allocation
    daily_budget_usd DECIMAL(8,2) NOT NULL,

    -- Usage tracking
    total_spent_usd DECIMAL(8,2) DEFAULT 0,
    analyses_completed INTEGER DEFAULT 0,
    analyses_failed INTEGER DEFAULT 0,

    -- Performance metrics
    avg_cost_per_analysis DECIMAL(6,4),
    avg_processing_time_seconds INTEGER,

    -- Status
    budget_exhausted_at TIMESTAMPTZ,
    emergency_stop_triggered BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_daily_budget_tracking_date ON daily_budget_tracking(date);
```

### 4.3 Monitoring and Alerting
```python
# src/crypto_newsletter/analysis/monitoring.py
class AnalysisMonitoring:
    def __init__(self):
        self.alert_thresholds = {
            'failure_rate': 0.10,          # Alert if >10% failure rate
            'budget_utilization': 0.90,    # Alert if >90% budget used
            'processing_delay': 3600,      # Alert if queue processing takes >1 hour
            'cost_spike': 2.0,             # Alert if cost per analysis >2x normal
        }

    async def check_system_health(self) -> SystemHealthReport:
        """Generate comprehensive system health report"""
        return SystemHealthReport(
            queue_status=await self.get_queue_status(),
            budget_status=await self.get_budget_status(),
            processing_performance=await self.get_processing_performance(),
            error_rate=await self.get_error_rate(),
            recent_failures=await self.get_recent_failures()
        )

    async def generate_daily_metrics(self):
        """Generate daily metrics for performance tracking"""
        today = datetime.now().date()

        metrics = DailyAnalysisMetrics(
            date=today,
            articles_analyzed=await self.count_daily_analyses(),
            total_cost=await self.get_daily_cost(),
            avg_processing_time=await self.get_avg_processing_time(),
            success_rate=await self.get_daily_success_rate(),
            top_signal_types=await self.get_top_signal_types(),
            publisher_performance=await self.get_publisher_performance()
        )

        await self.store_daily_metrics(metrics)
        await self.check_performance_alerts(metrics)

    async def alert_system_issues(self, issue: SystemIssue):
        """Send alerts for system issues"""
        alert_message = f"""
        Analysis System Alert: {issue.severity}

        Issue: {issue.description}
        Timestamp: {issue.timestamp}
        Affected Components: {', '.join(issue.affected_components)}

        Recommended Action: {issue.recommended_action}
        """

        # Send to monitoring dashboard
        await self.update_monitoring_dashboard(issue)

        # Log for historical tracking
        await self.log_system_issue(issue)
```

---

## 5. Quality Standards

### 5.1 Production Reliability
- **Task Success Rate**: >95% successful task completion
- **Queue Processing Time**: Complete daily analysis queue within 4 hours
- **Error Recovery Rate**: >90% successful recovery from temporary failures
- **Data Consistency**: 100% data integrity between tasks and database

### 5.2 Performance Standards
- **Analysis Throughput**: Process 35 articles within 2 hours
- **Cost Efficiency**: Maintain <$15 daily budget with <$0.25 per analysis
- **Resource Utilization**: <80% CPU and memory usage during peak processing
- **Queue Management**: Zero queue overflow or task loss

### 5.3 Operational Standards
- **Monitoring Coverage**: 100% task execution monitoring and alerting
- **Budget Compliance**: Zero budget overruns or uncontrolled spending
- **Error Visibility**: All errors logged and categorized for analysis
- **Recovery Time**: <30 minutes to recover from most system issues

---

## 6. Success Metrics

### 6.1 Pipeline Performance
- **Daily Analysis Coverage**: 100% of analysis-ready articles processed within 24 hours
- **Processing Efficiency**: Average 8-10 minutes per article including validation
- **Queue Utilization**: Optimal queue size with no bottlenecks or overflow
- **Cost Predictability**: Daily costs within ±10% of budget allocation

### 6.2 Quality Delivery
- **Analysis Quality**: Maintain >4.0/5.0 average signal detection quality
- **Data Completeness**: 100% of successful analyses stored in database
- **Error Categorization**: All errors properly classified and handled
- **Recovery Success**: >90% of failed analyses eventually complete successfully

---

## 7. Implementation Roadmap

### Week 1: Core Integration
- Extend Celery configuration with analysis tasks
- Implement core analysis task with error handling
- Create budget management and cost tracking systems
- Add queue prioritization and management logic

### Week 2: Production Hardening
- Implement comprehensive error classification and recovery
- Add monitoring and alerting for all system components
- Create task execution tracking and performance metrics
- Test under production load with controlled rollout

### Week 3: Optimization & Monitoring
- Optimize task scheduling and resource utilization
- Implement advanced cost optimization strategies
- Create comprehensive monitoring dashboard integration
- Fine-tune performance based on production metrics

---

## 8. Risk Assessment

### Technical Risks
- **Task Queue Overflow**: Mitigation through intelligent prioritization and rate limiting
- **Budget Overruns**: Mitigation through strict budget controls and emergency stops
- **Analysis Quality Degradation**: Mitigation through continuous quality monitoring

### Operational Risks
- **Production Stability**: Mitigation through phased rollout and comprehensive testing
- **Cost Unpredictability**: Mitigation through conservative budgets and cost tracking
- **Error Accumulation**: Mitigation through robust error handling and monitoring

---

## 9. Dependencies

### Phase 1 & 2 Dependencies
- **Database Schema**: Analysis tables operational and tested
- **AI Agents**: ContentAnalysisAgent and SignalValidationAgent tested and optimized
- **Admin Interface**: Analysis monitoring capabilities implemented

### Production Infrastructure
- **Celery Workers**: Existing worker infrastructure with capacity for analysis tasks
- **Redis**: Task queue with sufficient memory and performance
- **Database**: Production Neon PostgreSQL with analysis table capacity

---

## 10. Acceptance Criteria

### Core Functionality
- [ ] Analysis tasks integrate seamlessly with existing Celery infrastructure
- [ ] All analysis-ready articles processed automatically within 4 hours of ingestion
- [ ] Budget controls prevent cost overruns with hard stops at 90% of daily budget
- [ ] Error handling and recovery working for all identified error scenarios

### Production Readiness
- [ ] Task monitoring and alerting operational for all analysis pipeline components
- [ ] Queue management handles daily volume without bottlenecks or overflow
- [ ] Cost tracking accurate to within 1% of actual expenses
- [ ] Performance metrics collected and reported for optimization

### Integration Verification
- [ ] Analysis results properly stored in database with full referential integrity
- [ ] Admin interface displays real-time analysis pipeline status and metrics
- [ ] No impact on existing ingestion pipeline performance or reliability
- [ ] All analysis tasks complete within allocated time and resource limits

---

*Document Version: 1.0*
*Last Updated: August 14, 2025*
*Status: Ready for Implementation*
*Prerequisites: Phase 1 & 2 Complete*
*Next Phase: Admin Interface & Analysis Display*
