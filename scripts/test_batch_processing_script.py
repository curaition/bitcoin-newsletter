#!/usr/bin/env python3
"""Test script for batch processing system validation."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from crypto_newsletter.newsletter.batch.config import BatchProcessingConfig
from crypto_newsletter.newsletter.batch.identifier import BatchArticleIdentifier
from crypto_newsletter.newsletter.batch.storage import BatchStorageManager
from crypto_newsletter.shared.database.connection import get_db_session

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_article_identification():
    """Test the article identification system."""
    logger.info("Testing article identification...")

    try:
        async with get_db_session() as db:
            identifier = BatchArticleIdentifier()

            # Test getting analyzable articles
            article_ids = await identifier.get_analyzable_articles(db, limit=10)
            logger.info(f"Found {len(article_ids)} analyzable articles")

            if article_ids:
                # Test getting article details
                details = await identifier.get_article_details(db, article_ids[:5])
                logger.info(f"Retrieved details for {len(details)} articles")

                # Test validation
                validation = await identifier.validate_articles_for_processing(
                    db, article_ids[:5]
                )
                logger.info(f"Validation: {validation['validation_summary']}")

                return True
            else:
                logger.warning("No articles found for testing")
                return False

    except Exception as e:
        logger.error(f"Article identification test failed: {e}")
        return False


async def test_batch_configuration():
    """Test batch processing configuration."""
    logger.info("Testing batch configuration...")

    try:
        # Test budget validation
        budget_check = BatchProcessingConfig.validate_budget(50)
        logger.info(f"Budget check for 50 articles: {budget_check}")

        # Test timeline calculation
        timeline = BatchProcessingConfig.get_processing_timeline(50)
        logger.info(f"Timeline for 50 articles: {timeline}")

        # Test batch count calculation
        batch_count = BatchProcessingConfig.get_batch_count(50)
        logger.info(f"Batch count for 50 articles: {batch_count}")

        return True

    except Exception as e:
        logger.error(f"Batch configuration test failed: {e}")
        return False


async def test_storage_system():
    """Test the batch storage system."""
    logger.info("Testing storage system...")

    try:
        async with get_db_session() as db:
            storage = BatchStorageManager()

            # Test creating a test session
            import uuid

            test_session_id = str(uuid.uuid4())
            session = await storage.create_batch_session(
                db, test_session_id, 10, 2, 0.013
            )
            logger.info(f"Created test session: {session.session_id}")

            # Test creating batch records
            record1 = await storage.create_batch_record(
                db, test_session_id, 1, [1, 2, 3, 4, 5], 0.0065
            )
            logger.info(f"Created batch record 1: {record1.batch_number}")

            record2 = await storage.create_batch_record(
                db, test_session_id, 2, [6, 7, 8, 9, 10], 0.0065
            )
            logger.info(f"Created batch record 2: {record2.batch_number}")

            # Test getting session with records
            session_with_records = await storage.get_batch_session_with_records(
                db, test_session_id
            )
            logger.info(
                f"Retrieved session with {len(session_with_records.batch_records)} records"
            )

            # Test updating batch status
            await storage.update_batch_record_status(
                db, test_session_id, 1, "COMPLETED"
            )
            logger.info("Updated batch 1 status to COMPLETED")

            # Test finalizing session
            await storage.finalize_batch_session(db, test_session_id)
            logger.info("Finalized test session")

            return True

    except Exception as e:
        logger.error(f"Storage system test failed: {e}")
        return False


async def test_small_batch_processing():
    """Test batch processing with a small number of articles."""
    logger.info("Testing small batch processing...")

    try:
        async with get_db_session() as db:
            identifier = BatchArticleIdentifier()

            # Get a small number of articles for testing
            article_ids = await identifier.get_analyzable_articles(db, limit=3)

            if len(article_ids) < 3:
                logger.warning("Not enough articles for small batch test")
                return False

            logger.info(f"Starting small batch test with {len(article_ids)} articles")

            # Note: We're not actually running the full batch processing here
            # as it would require Celery workers to be running
            # Instead, we'll validate the setup

            validation = await identifier.validate_articles_for_processing(
                db, article_ids
            )

            if validation["validation_summary"]["validation_passed"]:
                logger.info("Small batch validation passed - ready for processing")

                # Show what would happen
                budget_check = BatchProcessingConfig.validate_budget(len(article_ids))
                timeline = BatchProcessingConfig.get_processing_timeline(
                    len(article_ids)
                )

                logger.info(f"Would process {len(article_ids)} articles")
                logger.info(f"Estimated cost: ${budget_check['estimated_cost']:.4f}")
                logger.info(
                    f"Estimated time: {timeline['estimated_time_minutes']:.1f} minutes"
                )

                return True
            else:
                logger.warning("Small batch validation failed")
                return False

    except Exception as e:
        logger.error(f"Small batch processing test failed: {e}")
        return False


async def run_all_tests():
    """Run all batch processing tests."""
    logger.info("Starting batch processing system tests...")

    tests = [
        ("Article Identification", test_article_identification),
        ("Batch Configuration", test_batch_configuration),
        ("Storage System", test_storage_system),
        ("Small Batch Processing", test_small_batch_processing),
    ]

    results = {}

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")

        try:
            result = await test_func()
            results[test_name] = result

            if result:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")

        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
            results[test_name] = False

    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! Batch processing system is ready.")
        return True
    else:
        logger.error("⚠️  Some tests failed. Please review and fix issues.")
        return False


def main():
    """Main test function."""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
