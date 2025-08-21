# Monitoring and Logging Guide

This document covers the comprehensive monitoring and logging system implemented in the Bitcoin Newsletter application.

## Overview

The application includes a multi-layered monitoring and logging system designed for production observability:

- **Structured Logging**: Loguru-based centralized logging with JSON output for production
- **Metrics Collection**: System, application, database, and task metrics
- **Health Checks**: Multi-level health monitoring for all components
- **Performance Monitoring**: Request timing, resource usage, and bottleneck detection
- **Alerting**: Configurable thresholds and alert conditions

## Logging System

### Configuration

The logging system is automatically configured based on environment:

**Development Environment:**
- Colorized console output
- Detailed error traces with source code
- Debug-level logging enabled
- Human-readable format

**Production Environment:**
- Structured JSON logging
- Centralized log aggregation
- Info-level logging (configurable)
- Security-focused (no sensitive data)

### Usage Examples

**Basic Logging:**
```python
from crypto_newsletter.shared.logging.config import get_logger

logger = get_logger("my_module")
logger.info("Operation completed successfully")
logger.error("Operation failed", extra={"error_code": "DB_001"})
```

**Structured Logging with Context:**
```python
from crypto_newsletter.shared.logging.config import LogContext

with LogContext(user_id=123, operation="article_fetch"):
    logger.info("Starting article fetch")
    # All logs within this context include user_id and operation
```

**Request Logging:**
```python
from crypto_newsletter.shared.logging.config import RequestLogContext

with RequestLogContext("GET", "/api/articles", client_ip="192.168.1.1"):
    logger.info("Processing API request")
```

**Performance Logging:**
```python
from crypto_newsletter.shared.logging.config import log_performance_metric

log_performance_metric("api_response_time", 150.5, "ms", endpoint="/api/articles")
```

### Log Levels and Categories

**Log Levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational messages
- `WARNING`: Warning conditions that should be noted
- `ERROR`: Error conditions that need attention
- `CRITICAL`: Critical conditions requiring immediate action

**Log Categories:**
- `web.*`: Web service logs (requests, responses, middleware)
- `worker.*`: Celery worker logs (task processing, queue management)
- `beat.*`: Celery beat scheduler logs (periodic tasks)
- `db.*`: Database operation logs (queries, connections, migrations)
- `api.*`: External API interaction logs (CoinDesk, third-party services)
- `health.*`: Health check and monitoring logs
- `security.*`: Security-related events and alerts

### Log Storage and Rotation

**File Locations:**
```
logs/
├── app.log          # General application logs (INFO+)
├── error.log        # Error logs only (ERROR+)
├── web.log          # Web service specific logs
├── worker.log       # Worker service specific logs
└── beat.log         # Beat service specific logs
```

**Rotation Policy:**
- **Application logs**: 10MB rotation, 30 days retention
- **Error logs**: 5MB rotation, 90 days retention
- **Service logs**: 5MB rotation, 7 days retention
- **Compression**: Gzip compression for rotated logs

## Metrics Collection

### System Metrics

**CPU and Memory:**
```python
from crypto_newsletter.shared.monitoring.metrics import get_metrics_collector

collector = get_metrics_collector()
system_metrics = collector.collect_system_metrics()

print(f"CPU Usage: {system_metrics.cpu_percent}%")
print(f"Memory Usage: {system_metrics.memory_percent}%")
print(f"Disk Usage: {system_metrics.disk_percent}%")
```

**Available Metrics:**
- CPU utilization percentage
- Memory usage (percent, used MB, available MB)
- Disk usage (percent, used GB, free GB)
- Load average (1min, 5min, 15min)
- Process count
- Network connections (by service)

### Application Metrics

**Request Metrics:**
```python
# Automatically recorded by middleware
collector.record_request(response_time_ms=150.5, status_code=200)

# Get aggregated metrics
app_metrics = collector.collect_application_metrics()
print(f"Total Requests: {app_metrics.total_requests}")
print(f"Average Response Time: {app_metrics.avg_response_time_ms}ms")
print(f"Error Rate: {app_metrics.error_count / app_metrics.total_requests}")
```

**Cache Metrics:**
```python
# Record cache operations
collector.record_cache_hit()
collector.record_cache_miss()

# Cache hit rate is automatically calculated
print(f"Cache Hit Rate: {app_metrics.cache_hit_rate}")
```

### Database Metrics

**Connection and Query Metrics:**
```python
db_metrics = await collector.collect_database_metrics()

print(f"Active Connections: {db_metrics.connection_count}")
print(f"Total Articles: {db_metrics.total_articles}")
print(f"Articles Today: {db_metrics.articles_today}")
print(f"Average Query Time: {db_metrics.avg_query_time_ms}ms")
```

### Task Queue Metrics

**Celery Task Metrics:**
```python
task_metrics = collector.collect_task_metrics()

print(f"Active Tasks: {task_metrics.active_tasks}")
print(f"Pending Tasks: {task_metrics.pending_tasks}")
print(f"Queue Lengths: {task_metrics.queue_lengths}")
```

## Health Checks

### Health Check Endpoints

**Basic Health Check:**
```bash
curl https://your-app.railway.app/health
```

**Detailed Health Check:**
```bash
curl https://your-app.railway.app/health/detailed
```

**Metrics Endpoint:**
```bash
curl https://your-app.railway.app/health/metrics
```

### Health Check Components

**Database Health:**
- Connection availability
- Query response time
- Connection pool status

**Redis Health:**
- Connection availability
- Response time
- Memory usage

**External API Health:**
- CoinDesk API accessibility
- Response time
- Rate limit status

**Task Queue Health:**
- Worker availability
- Queue lengths
- Task processing rates

### Custom Health Checks

**Adding Custom Checks:**
```python
from crypto_newsletter.shared.monitoring.metrics import HealthChecker

class CustomHealthChecker(HealthChecker):
    @staticmethod
    async def check_custom_service() -> Dict[str, Any]:
        try:
            # Your custom health check logic
            return {
                "status": "healthy",
                "response_time_ms": 50.0,
                "message": "Custom service is operational"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "response_time_ms": 0,
                "message": f"Custom service failed: {str(e)}"
            }
```

## Performance Monitoring

### Function Performance Monitoring

**Decorator-based Monitoring:**
```python
from crypto_newsletter.shared.monitoring.metrics import PerformanceMonitor

@PerformanceMonitor.monitor_function("article_processing")
async def process_article(article_data):
    # Function implementation
    pass
```

**Context Manager Monitoring:**
```python
from crypto_newsletter.shared.monitoring.metrics import measure_time

with measure_time("database_query"):
    result = await db.execute(query)
```

### Resource Usage Monitoring

**Memory Monitoring:**
```python
from crypto_newsletter.shared.monitoring.metrics import PerformanceMonitor

# Check if memory usage exceeds threshold
if PerformanceMonitor.check_memory_usage(threshold_mb=500.0):
    logger.warning("High memory usage detected")
```

**Disk Monitoring:**
```python
# Check if disk usage exceeds threshold
if PerformanceMonitor.check_disk_usage(threshold_percent=80.0):
    logger.warning("High disk usage detected")
```

## Alerting and Notifications

### Alert Thresholds

**System Resource Alerts:**
- CPU usage > 80%
- Memory usage > 80%
- Disk usage > 90%
- Load average > 2.0

**Application Alerts:**
- Error rate > 5%
- Average response time > 1000ms
- Database connection failures
- External API failures

**Task Queue Alerts:**
- Queue length > 100 tasks
- Task failure rate > 10%
- Worker unavailability > 5 minutes

### Alert Configuration

**Environment Variables:**
```bash
# Alert thresholds
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=80
ALERT_THRESHOLD_DISK=90
ALERT_THRESHOLD_ERROR_RATE=5
ALERT_THRESHOLD_RESPONSE_TIME=1000

# Notification settings
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_RECIPIENTS=admin@example.com,ops@example.com
ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### Custom Alerts

**Creating Custom Alerts:**
```python
from crypto_newsletter.shared.logging.config import log_security_event

# Security alert
log_security_event(
    "SUSPICIOUS_ACTIVITY",
    severity="WARNING",
    client_ip="192.168.1.100",
    endpoint="/api/articles",
    details="Multiple failed requests"
)

# Business metric alert
from crypto_newsletter.shared.logging.config import log_business_event

log_business_event(
    "ARTICLE_INGESTION_FAILURE",
    source="coindesk",
    error_count=5,
    threshold=3
)
```

## Monitoring Dashboard

### Real-time Monitoring

**Using Monitoring Script:**
```bash
# Real-time system monitoring
./scripts/monitor.sh watch

# System health check
./scripts/monitor.sh health

# Generate monitoring report
./scripts/monitor.sh report
```

### Metrics Visualization

**Grafana Integration (Future):**
- System resource dashboards
- Application performance metrics
- Database performance monitoring
- Task queue monitoring
- Custom business metrics

**Prometheus Integration (Future):**
- Metrics export endpoint
- Custom metric definitions
- Alert manager integration

## Log Analysis

### Log Aggregation

**Production Log Analysis:**
```bash
# Search for errors in the last hour
grep -E "ERROR|CRITICAL" logs/app.log | grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')"

# Analyze API response times
grep "api_response_time" logs/app.log | jq '.metric_value' | sort -n

# Find slow database queries
grep "db_operation" logs/app.log | jq 'select(.duration_ms > 1000)'
```

### Log Monitoring Tools

**ELK Stack Integration (Future):**
- Elasticsearch for log storage
- Logstash for log processing
- Kibana for log visualization

**Structured Log Queries:**
```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"level": "ERROR"}},
        {"range": {"timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}
```

## Troubleshooting

### Common Monitoring Issues

**High Memory Usage:**
1. Check application metrics for memory leaks
2. Review database connection pooling
3. Analyze task queue memory usage
4. Check for large object retention

**Slow Response Times:**
1. Review database query performance
2. Check external API response times
3. Analyze middleware processing time
4. Review caching effectiveness

**Task Queue Backlog:**
1. Check worker availability
2. Review task processing times
3. Analyze queue distribution
4. Check Redis memory usage

### Monitoring Script Usage

**Health Monitoring:**
```bash
# Comprehensive health check
./scripts/monitor.sh health

# Check for system alerts
./scripts/monitor.sh alerts

# View system metrics
./scripts/monitor.sh metrics
```

**Maintenance:**
```bash
# Clean up old logs and data
./scripts/monitor.sh cleanup

# Create system backup
./scripts/monitor.sh backup

# Optimize system performance
./scripts/monitor.sh optimize
```

## Best Practices

### Logging Best Practices

1. **Use Structured Logging**: Always include relevant context
2. **Avoid Sensitive Data**: Never log passwords, tokens, or PII
3. **Use Appropriate Levels**: Don't overuse DEBUG or ERROR levels
4. **Include Correlation IDs**: Track requests across services
5. **Log Business Events**: Track important business metrics

### Monitoring Best Practices

1. **Monitor Key Metrics**: Focus on metrics that matter to users
2. **Set Realistic Thresholds**: Avoid alert fatigue
3. **Monitor Dependencies**: Include external services and databases
4. **Regular Review**: Periodically review and update monitoring
5. **Document Runbooks**: Create clear response procedures

### Performance Best Practices

1. **Measure Everything**: Instrument critical code paths
2. **Set Performance Budgets**: Define acceptable performance limits
3. **Monitor Trends**: Look for performance degradation over time
4. **Optimize Bottlenecks**: Focus on the slowest components
5. **Test Under Load**: Validate performance under realistic conditions

## Integration with External Services

### Railway Integration

**Built-in Monitoring:**
- Service health checks
- Resource usage metrics
- Deployment monitoring
- Log aggregation

### Neon Database Monitoring

**Database Metrics:**
- Connection pool monitoring
- Query performance tracking
- Storage usage monitoring
- Backup status monitoring

### Redis Monitoring

**Cache Metrics:**
- Memory usage tracking
- Hit/miss ratios
- Connection monitoring
- Eviction tracking

This comprehensive monitoring and logging system provides full observability into the Bitcoin Newsletter application, enabling proactive issue detection and resolution.

## Newsletter Generation Progress Tracking

### Real-time Progress Monitoring

The system now includes comprehensive progress tracking for newsletter generation with real-time updates and quality validation.

**Progress Tracking Features:**
- Step-by-step progress visualization (Selection → Synthesis → Writing → Storage)
- Real-time quality metrics and validation gates
- Intermediate results preview for transparency
- Estimated completion times and progress percentages
- Automatic error detection and recovery

**Database Schema:**
```sql
CREATE TABLE newsletter_generation_progress (
    task_id VARCHAR PRIMARY KEY,
    current_step VARCHAR NOT NULL,
    step_progress FLOAT DEFAULT 0.0,
    overall_progress FLOAT DEFAULT 0.0,
    step_details JSONB DEFAULT '{}',
    intermediate_results JSONB DEFAULT '{}',
    quality_metrics JSONB DEFAULT '{}',
    articles_being_processed JSONB DEFAULT '[]',
    estimated_completion TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR DEFAULT 'in_progress'
);
```

**API Endpoints:**
```bash
# Get real-time progress for a generation task
curl https://your-app.railway.app/admin/tasks/{task_id}/progress

# Generate newsletter with progress tracking
curl -X POST https://your-app.railway.app/admin/newsletters/generate \
  -H "Content-Type: application/json" \
  -d '{"newsletter_type": "DAILY", "force_generation": false}'
```

### Newsletter Quality Monitoring

**Quality Metrics Tracked:**
- Average quality score (target: >0.7)
- Citation count per newsletter (target: >5)
- Generation success/failure rates
- Signal utilization effectiveness
- Content uniqueness scores

**Quality Alerts:**
```python
# Quality score alerts
if avg_quality_score < 0.5:
    severity = "CRITICAL"
elif avg_quality_score < 0.7:
    severity = "WARNING"

# Citation count alerts
if avg_citation_count < 3:
    severity = "CRITICAL"
elif avg_citation_count < 5:
    severity = "WARNING"

# Failure rate alerts
if failure_rate > 0.5:
    severity = "CRITICAL"
elif failure_rate > 0.2:
    severity = "WARNING"
```

### Enhanced Alert System

**Newsletter Generation Alerts:**
- `GENERATION_FAILURE`: Individual generation task failures
- `LOW_QUALITY_SCORE`: Quality scores below acceptable thresholds
- `LOW_CITATION_COUNT`: Insufficient article citations
- `HIGH_FAILURE_RATE`: Elevated failure rates over time
- `STUCK_GENERATION`: Tasks stuck in progress for >2 hours
- `COST_THRESHOLD`: API costs exceeding budget limits

**Alert Configuration:**
```bash
# Environment variables for alert thresholds
ALERT_QUALITY_SCORE_WARNING=0.7
ALERT_QUALITY_SCORE_CRITICAL=0.5
ALERT_CITATION_COUNT_WARNING=5
ALERT_CITATION_COUNT_CRITICAL=3
ALERT_FAILURE_RATE_WARNING=0.2
ALERT_FAILURE_RATE_CRITICAL=0.5
ALERT_STUCK_GENERATION_HOURS=2
```

**Scheduled Alert Checking:**
```python
# Celery beat schedule - runs every 15 minutes
"check-newsletter-alerts": {
    "task": "crypto_newsletter.newsletter.tasks.check_newsletter_alerts_task",
    "schedule": crontab(minute="*/15"),
    "options": {"priority": 8, "queue": "monitoring"}
}
```

### Frontend Progress Visualization

**Real-time Progress Components:**
- `NewsletterGenerationProgress`: Live progress tracking with step indicators
- `NewsletterGenerationComplete`: Success state with newsletter details
- `NewsletterGenerationError`: Error handling with retry options

**Progress Polling:**
```typescript
// Frontend polls for progress every 2 seconds
const { data: progressData } = useQuery({
  queryKey: ['newsletter-progress', taskId],
  queryFn: () => apiClient.getGenerationProgress(taskId),
  enabled: taskId !== null && generationState === 'generating',
  refetchInterval: 2000,
  retry: 3,
});
```

**Quality Metrics Display:**
- Stories selected count
- Quality scores and confidence levels
- Citation count and URL availability
- Word count and readability metrics
- Theme identification and coherence

This enhanced monitoring system provides complete transparency into newsletter generation with proactive quality assurance and real-time user feedback.
