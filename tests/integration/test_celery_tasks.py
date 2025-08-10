"""Integration tests for Celery tasks."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from crypto_newsletter.core.scheduling.tasks import (
    cleanup_old_articles,
    health_check,
    ingest_articles,
    manual_ingest,
)


class TestCeleryTasks:
    """Test Celery task functionality."""

    @pytest.mark.asyncio
    async def test_health_check_task(self):
        """Test health check task execution."""
        # Mock the health check function
        with patch("crypto_newsletter.core.scheduling.tasks.pipeline_health_check") as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": {
                    "coindesk_api": {"status": "healthy", "message": "API connection successful"},
                    "database": {"status": "healthy", "message": "Database connection successful"},
                }
            }
            
            # Create task instance and run
            task = health_check
            result = await task.run_async(task)
            
            assert result["status"] == "healthy"
            assert "timestamp" in result
            mock_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_ingest_articles_task(self):
        """Test article ingestion task execution."""
        # Mock the pipeline
        with patch("crypto_newsletter.core.scheduling.tasks.ArticleIngestionPipeline") as mock_pipeline_class:
            mock_pipeline = AsyncMock()
            mock_pipeline_class.return_value = mock_pipeline
            
            mock_pipeline.run_full_ingestion.return_value = {
                "articles_fetched": 5,
                "articles_processed": 3,
                "duplicates_skipped": 2,
                "success_rate": 0.6,
                "errors": 0,
            }
            
            # Create task instance and run
            task = ingest_articles
            result = await task.run_async(task, limit=5, hours_back=4)
            
            assert result["articles_fetched"] == 5
            assert result["articles_processed"] == 3
            assert result["duplicates_skipped"] == 2
            assert "processing_time_seconds" in result
            assert "task_completed_at" in result
            
            mock_pipeline.run_full_ingestion.assert_called_once_with(
                limit=5,
                hours_back=4,
                categories=None,
            )

    @pytest.mark.asyncio
    async def test_cleanup_old_articles_task_dry_run(self):
        """Test article cleanup task in dry run mode."""
        # Mock database session and repository
        with patch("crypto_newsletter.core.scheduling.tasks.get_db_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock the count query result
            mock_result = AsyncMock()
            mock_result.scalar.return_value = 15
            mock_session.execute.return_value = mock_result
            
            # Create task instance and run
            task = cleanup_old_articles
            result = await task.run_async(task, days_to_keep=30, dry_run=True)
            
            assert result["success"] is True
            assert result["dry_run"] is True
            assert result["articles_to_delete"] == 15
            assert "cutoff_date" in result

    def test_manual_ingest_task(self):
        """Test manual ingestion task (synchronous wrapper)."""
        # Mock the async pipeline
        with patch("crypto_newsletter.core.scheduling.tasks.ArticleIngestionPipeline") as mock_pipeline_class:
            mock_pipeline = AsyncMock()
            mock_pipeline_class.return_value = mock_pipeline
            
            mock_pipeline.run_full_ingestion.return_value = {
                "articles_fetched": 2,
                "articles_processed": 1,
                "duplicates_skipped": 1,
                "success_rate": 0.5,
                "errors": 0,
            }
            
            # Run the manual task
            result = manual_ingest(limit=2, hours_back=24)
            
            assert result["articles_fetched"] == 2
            assert result["articles_processed"] == 1

    @pytest.mark.asyncio
    async def test_ingest_articles_task_with_retry(self):
        """Test article ingestion task retry logic."""
        # Mock the pipeline to fail first, then succeed
        with patch("crypto_newsletter.core.scheduling.tasks.ArticleIngestionPipeline") as mock_pipeline_class:
            mock_pipeline = AsyncMock()
            mock_pipeline_class.return_value = mock_pipeline
            
            # First call fails, second succeeds
            mock_pipeline.run_full_ingestion.side_effect = [
                Exception("API timeout"),
                {
                    "articles_fetched": 3,
                    "articles_processed": 3,
                    "duplicates_skipped": 0,
                    "success_rate": 1.0,
                    "errors": 0,
                }
            ]
            
            # Create a mock task with retry capability
            task = ingest_articles
            task.request = type('obj', (object,), {'retries': 0})()
            task.max_retries = 3
            
            # Mock the retry method
            with patch.object(task, 'retry', side_effect=Exception("Retry called")):
                try:
                    await task.run_async(task, limit=3)
                except Exception as e:
                    assert "Retry called" in str(e)

    @pytest.mark.asyncio
    async def test_health_check_task_failure(self):
        """Test health check task when health check fails."""
        # Mock the health check to fail
        with patch("crypto_newsletter.core.scheduling.tasks.pipeline_health_check") as mock_health:
            mock_health.side_effect = Exception("Database connection failed")
            
            # Create task instance and run
            task = health_check
            result = await task.run_async(task)
            
            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Database connection failed" in result["error"]

    @pytest.mark.asyncio
    async def test_cleanup_old_articles_task_actual_cleanup(self):
        """Test article cleanup task with actual deletion."""
        # Mock database session and repository
        with patch("crypto_newsletter.core.scheduling.tasks.get_db_session") as mock_get_session:
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock the update query result
            mock_result = AsyncMock()
            mock_result.rowcount = 8
            mock_session.execute.return_value = mock_result
            
            # Create task instance and run
            task = cleanup_old_articles
            result = await task.run_async(task, days_to_keep=30, dry_run=False)
            
            assert result["success"] is True
            assert result["dry_run"] is False
            assert result["articles_deleted"] == 8
            assert "cutoff_date" in result
            
            # Verify commit was called
            mock_session.commit.assert_called_once()
