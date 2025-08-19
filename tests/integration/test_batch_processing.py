"""Integration tests for batch processing system."""

import os

import pytest

# Set testing environment before importing modules
os.environ["TESTING"] = "true"
os.environ["GEMINI_API_KEY"] = "test-key-for-testing"
os.environ["TAVILY_API_KEY"] = "test-key-for-testing"

from crypto_newsletter.newsletter.batch.config import BatchProcessingConfig
from crypto_newsletter.newsletter.batch.identifier import BatchArticleIdentifier
from crypto_newsletter.newsletter.batch.storage import BatchStorageManager
from crypto_newsletter.shared.database.connection import get_db_session


@pytest.mark.integration
class TestBatchProcessingIntegration:
    """Integration tests for the complete batch processing system."""

    @pytest.fixture
    def test_environment(self):
        """Set up test environment variables."""
        original_testing = os.environ.get("TESTING")
        original_gemini = os.environ.get("GEMINI_API_KEY")
        original_tavily = os.environ.get("TAVILY_API_KEY")

        os.environ["TESTING"] = "true"
        os.environ["GEMINI_API_KEY"] = "test-key-for-testing"
        os.environ["TAVILY_API_KEY"] = "test-key-for-testing"

        yield

        # Restore original values
        if original_testing:
            os.environ["TESTING"] = original_testing
        if original_gemini:
            os.environ["GEMINI_API_KEY"] = original_gemini
        if original_tavily:
            os.environ["TAVILY_API_KEY"] = original_tavily

    @pytest.mark.asyncio
    async def test_article_identification_with_real_database(self, test_environment):
        """Test article identification against real database."""
        async with get_db_session() as db:
            identifier = BatchArticleIdentifier()

            # Test getting analyzable articles
            article_ids = await identifier.get_analyzable_articles(db, limit=50)

            assert isinstance(article_ids, list)
            assert len(article_ids) > 0, "Should find unanalyzed articles in database"

            print(f"Found {len(article_ids)} analyzable articles")

            # Test getting article details
            if article_ids:
                details = await identifier.get_article_details(db, article_ids[:5])
                assert len(details) > 0
                assert all("id" in article for article in details)
                assert all("title" in article for article in details)
                assert all("content_length" in article for article in details)

                print(f"Retrieved details for {len(details)} articles")

                # Test validation
                validation = await identifier.validate_articles_for_processing(
                    db, article_ids[:5]
                )
                assert "valid_articles" in validation
                assert "validation_summary" in validation

                print(f"Validation summary: {validation['validation_summary']}")

    @pytest.mark.asyncio
    async def test_batch_storage_operations(self, test_environment):
        """Test batch storage operations."""
        async with get_db_session() as db:
            storage = BatchStorageManager()

            # Create a test session
            import uuid

            test_session_id = str(uuid.uuid4())

            session = await storage.create_batch_session(
                db, test_session_id, 10, 2, 0.013
            )

            assert session.session_id == test_session_id
            assert session.total_articles == 10
            assert session.total_batches == 2
            assert session.status == "INITIATED"

            # Create batch records
            record1 = await storage.create_batch_record(
                db, test_session_id, 1, [1, 2, 3, 4, 5], 0.0065
            )

            assert record1.batch_number == 1
            assert record1.article_ids == [1, 2, 3, 4, 5]
            assert record1.status == "PENDING"

            # Test updating batch status
            await storage.update_batch_record_status(
                db, test_session_id, 1, "PROCESSING"
            )

            # Test getting session with records
            session_with_records = await storage.get_batch_session_with_records(
                db, test_session_id
            )
            assert len(session_with_records.batch_records) == 1
            assert session_with_records.batch_records[0].status == "PROCESSING"

            print(
                f"Successfully tested storage operations for session {test_session_id}"
            )

    @pytest.mark.asyncio
    async def test_batch_configuration_validation(self, test_environment):
        """Test batch processing configuration."""
        # Test budget validation
        budget_check = BatchProcessingConfig.validate_budget(50)

        assert "article_count" in budget_check
        assert "estimated_cost" in budget_check
        assert "within_budget" in budget_check
        assert budget_check["article_count"] == 50

        # Test timeline calculation
        timeline = BatchProcessingConfig.get_processing_timeline(50)

        assert "batch_count" in timeline
        assert "estimated_time_minutes" in timeline
        assert timeline["article_count"] == 50

        print(f"Budget check for 50 articles: ${budget_check['estimated_cost']:.4f}")
        print(f"Timeline: {timeline['estimated_time_minutes']:.1f} minutes")

    @pytest.mark.asyncio
    async def test_analysis_task_integration(self, test_environment):
        """Test integration with analysis tasks using TestModel."""
        async with get_db_session() as db:
            identifier = BatchArticleIdentifier()

            # Get a real article for testing
            article_ids = await identifier.get_analyzable_articles(db, limit=1)

            if not article_ids:
                pytest.skip("No unanalyzed articles available for testing")

            article_id = article_ids[0]

            # Test that we can import and call the analysis task
            # This should use TestModel due to TESTING=true
            try:
                # Import should work now with TESTING=true
                from crypto_newsletter.analysis.tasks import analyze_article_task

                # We can't easily test the actual Celery task execution in integration tests
                # but we can verify the task is properly defined and importable
                assert analyze_article_task is not None
                assert hasattr(analyze_article_task, "delay")

                print(f"Successfully imported analysis task for article {article_id}")

            except Exception as e:
                pytest.fail(f"Failed to import analysis task: {e}")

    @pytest.mark.asyncio
    async def test_small_batch_simulation(self, test_environment):
        """Test a small batch processing simulation."""
        async with get_db_session() as db:
            identifier = BatchArticleIdentifier()
            storage = BatchStorageManager()

            # Get articles for testing
            article_ids = await identifier.get_analyzable_articles(db, limit=3)

            if len(article_ids) < 3:
                pytest.skip("Need at least 3 unanalyzed articles for batch testing")

            # Validate articles
            validation = await identifier.validate_articles_for_processing(
                db, article_ids
            )

            assert validation["validation_summary"]["validation_passed"]

            # Create a test batch session
            import uuid

            session_id = str(uuid.uuid4())

            session = await storage.create_batch_session(
                db,
                session_id,
                len(article_ids),
                1,
                len(article_ids) * BatchProcessingConfig.ESTIMATED_COST_PER_ARTICLE,
            )

            # Create batch record
            record = await storage.create_batch_record(
                db,
                session_id,
                1,
                article_ids,
                len(article_ids) * BatchProcessingConfig.ESTIMATED_COST_PER_ARTICLE,
            )

            assert record.status == "PENDING"
            assert len(record.article_ids) == len(article_ids)

            print(f"Successfully simulated batch setup for {len(article_ids)} articles")
            print(f"Session ID: {session_id}")
            print(f"Estimated cost: ${session.estimated_cost:.4f}")


@pytest.mark.unit
class TestBatchProcessingComponents:
    """Unit tests for individual batch processing components."""

    def test_batch_config_calculations(self):
        """Test batch configuration calculations."""
        # Test batch count calculation
        assert (
            BatchProcessingConfig.get_batch_count(25) == 3
        )  # 25 articles / 10 per batch = 3 batches
        assert BatchProcessingConfig.get_batch_count(10) == 1  # Exactly one batch
        assert BatchProcessingConfig.get_batch_count(1) == 1  # Less than batch size

        # Test cost estimation
        cost = BatchProcessingConfig.get_estimated_total_cost(100)
        expected_cost = 100 * BatchProcessingConfig.ESTIMATED_COST_PER_ARTICLE
        assert cost == expected_cost

        # Test budget validation
        budget_check = BatchProcessingConfig.validate_budget(
            200
        )  # Should be within budget
        assert budget_check["within_budget"] is True

        budget_check = BatchProcessingConfig.validate_budget(
            300
        )  # Should exceed budget
        assert budget_check["within_budget"] is False

    def test_article_identifier_initialization(self):
        """Test article identifier initialization."""
        identifier = BatchArticleIdentifier()
        assert identifier.min_content_length == 1000

        identifier_custom = BatchArticleIdentifier(min_content_length=2000)
        assert identifier_custom.min_content_length == 2000


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])
