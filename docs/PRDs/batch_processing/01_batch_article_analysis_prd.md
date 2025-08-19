# Batch Article Analysis System
## Sub-PRD 1: Historical Article Processing

### Executive Summary
Implement a robust batch processing system to analyze 171 historical articles through the existing PydanticAI signal detection pipeline. This system will process articles in manageable chunks with cost monitoring, error handling, and progress tracking to populate the signal database for newsletter generation.

---

## 1. Product Overview

### Objective
Process 171 analyzable articles (>1000 characters) through batch analysis to build a comprehensive signal database that enables automated newsletter generation.

### Success Criteria
- 100% of 171 articles processed within 48 hours
- Processing cost under $0.30 total budget
- Average signal strength >0.6 across all analyses
- <5% failure rate with automatic retry
- Zero data corruption or analysis failures

---

## 2. Technical Requirements

### 2.1 Article Identification System
```python
class BatchArticleIdentifier:
    """Identifies articles suitable for batch processing."""

    @staticmethod
    async def get_analyzable_articles(min_content_length: int = 1000) -> List[int]:
        """Get article IDs for batch processing."""
        query = """
        SELECT a.id
        FROM articles a
        LEFT JOIN article_analyses aa ON a.id = aa.article_id
        WHERE aa.id IS NULL  -- Not yet analyzed
          AND LENGTH(a.body) > %s  -- Substantial content
          AND a.body IS NOT NULL
          AND a.body != ''
        ORDER BY a.published_at DESC
        LIMIT 200  -- Safety buffer
        """
        # Returns list of article IDs for processing
```

### 2.2 Batch Processing Configuration
```python
class BatchProcessingConfig:
    BATCH_SIZE = 10  # Articles per batch
    MAX_TOTAL_BUDGET = 0.30  # USD
    ESTIMATED_COST_PER_ARTICLE = 0.0013  # USD
    MAX_RETRY_ATTEMPTS = 3
    PROCESSING_TIMEOUT = 300  # 5 minutes per article
    BATCH_DELAY = 30  # Seconds between batches

    # Cost monitoring thresholds
    COST_WARNING_THRESHOLD = 0.20  # 67% of budget
    COST_CRITICAL_THRESHOLD = 0.25  # 83% of budget
```

### 2.3 Core Batch Processing Tasks
```python
@celery_app.task(
    bind=True,
    max_retries=3,
    queue="batch_processing"
)
def batch_analyze_articles(self, article_ids: List[int], batch_number: int):
    """Process a batch of articles for analysis."""
    try:
        results = []
        batch_cost = 0.0

        for article_id in article_ids:
            # Check budget constraint before processing
            current_total_cost = get_current_batch_cost()
            if current_total_cost > BatchProcessingConfig.MAX_TOTAL_BUDGET:
                raise BudgetExceededException(f"Budget exceeded: ${current_total_cost}")

            # Process individual article using existing analysis task
            result = analyze_article_task.delay(article_id)
            results.append({
                "article_id": article_id,
                "task_id": result.id,
                "estimated_cost": BatchProcessingConfig.ESTIMATED_COST_PER_ARTICLE
            })

            batch_cost += BatchProcessingConfig.ESTIMATED_COST_PER_ARTICLE

            # Brief pause between articles to manage load
            time.sleep(2)

        # Store batch processing record
        store_batch_record(batch_number, article_ids, batch_cost, results)

        return {
            "batch_number": batch_number,
            "articles_processed": len(article_ids),
            "estimated_batch_cost": batch_cost,
            "task_results": results,
            "status": "completed"
        }

    except Exception as exc:
        logger.error(f"Batch {batch_number} failed: {exc}")
        raise self.retry(exc=exc, countdown=300)  # 5 minute retry delay

@celery_app.task(
    bind=True,
    queue="batch_processing"
)
def initiate_batch_processing(self):
    """Start the complete batch processing workflow."""
    try:
        # Get articles to process
        article_ids = BatchArticleIdentifier.get_analyzable_articles()

        if len(article_ids) == 0:
            return {"status": "no_articles", "message": "No articles found for processing"}

        # Create batches
        article_chunks = [
            article_ids[i:i + BatchProcessingConfig.BATCH_SIZE]
            for i in range(0, len(article_ids), BatchProcessingConfig.BATCH_SIZE)
        ]

        # Initialize batch processing session
        session_id = initialize_batch_session(len(article_ids), len(article_chunks))

        # Launch batches with staggered execution
        batch_results = []
        for i, chunk in enumerate(article_chunks, 1):
            result = batch_analyze_articles.delay(chunk, i)
            batch_results.append({
                "batch_number": i,
                "task_id": result.id,
                "article_count": len(chunk)
            })

            # Stagger batch execution to manage system load
            if i < len(article_chunks):  # Don't sleep after last batch
                time.sleep(BatchProcessingConfig.BATCH_DELAY)

        return {
            "session_id": session_id,
            "total_batches": len(article_chunks),
            "total_articles": len(article_ids),
            "batch_tasks": batch_results,
            "estimated_total_cost": len(article_ids) * BatchProcessingConfig.ESTIMATED_COST_PER_ARTICLE,
            "status": "initiated"
        }

    except Exception as exc:
        logger.error(f"Batch processing initiation failed: {exc}")
        raise
```

---

## 3. Database Schema Extensions

### 3.1 Batch Processing Tracking
```sql
-- Batch Processing Sessions
CREATE TABLE batch_processing_sessions (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    total_articles INTEGER NOT NULL,
    total_batches INTEGER NOT NULL,
    estimated_cost DECIMAL(6,4) NOT NULL,
    actual_cost DECIMAL(6,4) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'INITIATED' CHECK (status IN ('INITIATED', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED')),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Individual Batch Records
CREATE TABLE batch_processing_records (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES batch_processing_sessions(session_id),
    batch_number INTEGER NOT NULL,
    article_ids INTEGER[] NOT NULL,
    estimated_cost DECIMAL(6,4) NOT NULL,
    actual_cost DECIMAL(6,4) DEFAULT 0,
    articles_processed INTEGER DEFAULT 0,
    articles_failed INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(session_id, batch_number)
);
```

---

## 4. Monitoring & Progress Tracking

### 4.1 Batch Monitoring Task
```python
@celery_app.task(queue="monitoring")
def monitor_batch_processing():
    """Monitor active batch processing sessions."""
    active_sessions = get_active_batch_sessions()

    for session in active_sessions:
        session_status = calculate_session_progress(session.session_id)

        # Update session status
        update_batch_session_status(session.session_id, session_status)

        # Check for cost overruns
        if session_status['actual_cost'] > BatchProcessingConfig.COST_WARNING_THRESHOLD:
            send_cost_warning_alert(session.session_id, session_status)

        # Check for completion
        if session_status['completed_batches'] == session.total_batches:
            finalize_batch_session(session.session_id)

    return {"monitored_sessions": len(active_sessions)}
```

### 4.2 Progress Reporting
```python
def get_batch_processing_status(session_id: str) -> Dict[str, Any]:
    """Get detailed status of batch processing session."""
    return {
        "session_id": session_id,
        "progress": {
            "total_articles": 171,
            "articles_processed": 85,
            "articles_remaining": 86,
            "completion_percentage": 49.7
        },
        "batches": {
            "total_batches": 18,
            "completed_batches": 8,
            "failed_batches": 1,
            "pending_batches": 9
        },
        "costs": {
            "estimated_total": 0.22,
            "actual_spent": 0.11,
            "remaining_budget": 0.19
        },
        "timing": {
            "started_at": "2025-01-15T10:00:00Z",
            "estimated_completion": "2025-01-15T14:30:00Z",
            "elapsed_hours": 2.5
        },
        "quality_metrics": {
            "average_signal_strength": 0.73,
            "analysis_success_rate": 94.1,
            "retry_rate": 5.9
        }
    }
```

---

## 5. Error Handling & Recovery

### 5.1 Failure Recovery System
```python
@celery_app.task(queue="batch_processing")
def recover_failed_batch_articles():
    """Recover and retry failed article analyses."""
    failed_articles = get_failed_batch_articles()

    recovery_results = []
    for article_id in failed_articles:
        # Retry with exponential backoff
        result = analyze_article_task.apply_async(
            args=[article_id],
            countdown=calculate_retry_delay(article_id)
        )
        recovery_results.append({
            "article_id": article_id,
            "retry_task_id": result.id
        })

    return {
        "articles_retried": len(failed_articles),
        "recovery_tasks": recovery_results
    }
```

---

## 6. Implementation Timeline

### Week 1: Core Batch System
- **Days 1-2**: Implement `BatchArticleIdentifier` and configuration
- **Days 3-4**: Build `batch_analyze_articles` and `initiate_batch_processing` tasks
- **Days 5-7**: Create database schema and monitoring system

### Week 2: Testing & Optimization
- **Days 1-3**: Test batch processing with small article sets
- **Days 4-5**: Implement error handling and recovery systems
- **Days 6-7**: Performance optimization and cost validation

### Week 3: Production Deployment
- **Days 1-2**: Deploy to production environment
- **Days 3-4**: Execute full 171-article batch processing
- **Days 5-7**: Monitor results and optimize for newsletter generation

---

## 7. Success Metrics

### Processing Metrics
- **Completion Rate**: >95% of articles successfully analyzed
- **Cost Efficiency**: Actual cost within 120% of estimated budget
- **Processing Speed**: <5 minutes average per article
- **Error Recovery**: <5% retry rate with 100% eventual success

### Quality Metrics
- **Signal Detection**: Average signal strength >0.6
- **Analysis Confidence**: Average confidence >0.75
- **Data Integrity**: Zero corrupted or incomplete analyses

---

*Sub-PRD Version: 1.0*
*Implementation Priority: Phase 1 - Foundation*
*Dependencies: Existing signal analysis system*
*Estimated Effort: 3 weeks*
