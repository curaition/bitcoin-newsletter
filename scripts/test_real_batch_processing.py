#!/usr/bin/env python3
"""
Real Batch Processing Test - Complete end-to-end validation.

This script tests the COMPLETE batch processing workflow with real APIs,
real articles, and real database operations to validate Phase 1 is truly ready.
"""

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Load environment variables from .env.development
from dotenv import load_dotenv

env_file = project_root / ".env.development"
if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded environment from {env_file}")

# Ensure we're using real APIs
os.environ["TESTING"] = "false"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_single_article_analysis():
    """Test analyzing a single article with real APIs - Direct execution."""

    logger.info("🧠 Testing Single Article Analysis with Real APIs (Direct)")
    logger.info("=" * 60)

    try:
        # Import analysis components directly for testing
        from crypto_newsletter.analysis.agents.content_analysis import (
            content_analysis_agent,
        )
        from crypto_newsletter.analysis.agents.signal_validation import (
            signal_validation_agent,
        )
        from crypto_newsletter.analysis.storage import AnalysisStorageManager
        from crypto_newsletter.newsletter.batch.identifier import BatchArticleIdentifier
        from crypto_newsletter.shared.database.connection import get_db_session

        async with get_db_session() as db:
            identifier = BatchArticleIdentifier()

            # Get one article for testing
            article_ids = await identifier.get_analyzable_articles(db, limit=1)

            if not article_ids:
                logger.error("❌ No analyzable articles found")
                return False

            article_id = article_ids[0]

            # Get article details
            details = await identifier.get_article_details(db, [article_id])
            article = details[0]

            logger.info(f"📄 Testing with article: {article['title'][:50]}...")
            logger.info(f"📊 Content length: {article['content_length']} chars")
            logger.info(f"🏢 Publisher: {article['publisher_name']}")

            # Test real analysis - Direct execution without Celery
            logger.info("🔄 Starting direct article analysis...")
            start_time = time.time()

            try:
                # Step 1: Content Analysis
                logger.info("🔍 Running content analysis...")
                content_result = await content_analysis_agent.run(
                    f"Analyze this Bitcoin/crypto article for market signals:\n\n"
                    f"Title: {article['title']}\n\n"
                    f"Content: {article['body'][:2000]}..."  # Limit content for testing
                )

                logger.info("✅ Content analysis completed")
                logger.info(f"📊 Content result type: {type(content_result.data)}")

                # Step 2: Signal Validation
                logger.info("🎯 Running signal validation...")
                validation_result = await signal_validation_agent.run(
                    f"Validate signals from this analysis: {content_result.data}"
                )

                logger.info("✅ Signal validation completed")
                logger.info(f"📊 Validation result type: {type(validation_result.data)}")

                processing_time = time.time() - start_time
                logger.info(f"⏱️  Total processing time: {processing_time:.2f} seconds")

                # Step 3: Store results in database
                logger.info("💾 Storing analysis results...")
                storage = AnalysisStorageManager()

                # Create analysis record
                analysis_data = {
                    "article_id": article_id,
                    "content_analysis": content_result.data,
                    "signal_validation": validation_result.data,
                    "analysis_confidence": 0.85,  # Mock confidence for testing
                    "signal_count": 3,  # Mock signal count
                    "estimated_cost": 0.0025,  # Mock cost
                    "processing_time": processing_time,
                }

                analysis_id = await storage.store_analysis_result(db, analysis_data)

                if analysis_id:
                    logger.info(f"✅ Analysis stored with ID: {analysis_id}")

                    # Verify storage
                    from sqlalchemy import text

                    analysis_query = text(
                        """
                        SELECT id, analysis_confidence, signal_count, estimated_cost
                        FROM article_analyses
                        WHERE article_id = :article_id
                        ORDER BY created_at DESC
                        LIMIT 1
                    """
                    )

                    result_check = await db.execute(
                        analysis_query, {"article_id": article_id}
                    )
                    analysis_row = result_check.fetchone()

                    if analysis_row:
                        logger.info("✅ Analysis verified in database")
                        logger.info(f"📊 Confidence: {analysis_row.analysis_confidence}")
                        logger.info(f"🎯 Signals: {analysis_row.signal_count}")
                        logger.info(f"💰 Cost: ${analysis_row.estimated_cost}")
                        return True
                    else:
                        logger.error("❌ Analysis not found in database after storage")
                        return False
                else:
                    logger.error("❌ Failed to store analysis")
                    return False

            except Exception as e:
                logger.error(f"❌ Analysis execution failed: {e}")
                import traceback

                traceback.print_exc()
                return False

    except Exception as e:
        logger.error(f"❌ Single article analysis test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_small_batch_processing():
    """Test processing a small batch of 3-5 articles."""

    logger.info("\n🔄 Testing Small Batch Processing (3-5 Articles)")
    logger.info("=" * 60)

    try:
        from crypto_newsletter.newsletter.batch.identifier import BatchArticleIdentifier
        from crypto_newsletter.newsletter.batch.tasks import initiate_batch_processing
        from crypto_newsletter.shared.database.connection import get_db_session

        async with get_db_session() as db:
            identifier = BatchArticleIdentifier()

            # Get 3-5 articles for batch testing
            article_ids = await identifier.get_analyzable_articles(db, limit=5)

            if len(article_ids) < 3:
                logger.error("❌ Need at least 3 articles for batch testing")
                return False

            # Limit to 3 articles for testing
            test_articles = article_ids[:3]

            logger.info(
                f"📰 Testing batch processing with {len(test_articles)} articles"
            )

            # Get article details
            details = await identifier.get_article_details(db, test_articles)

            for i, article in enumerate(details, 1):
                logger.info(
                    f"📄 Article {i}: {article['title'][:40]}... ({article['content_length']} chars)"
                )

            # Validate articles
            validation = await identifier.validate_articles_for_processing(
                db, test_articles
            )

            if not validation["validation_summary"]["validation_passed"]:
                logger.error("❌ Article validation failed")
                return False

            logger.info("✅ Articles validated for batch processing")

            # Start batch processing
            logger.info("🚀 Initiating batch processing...")
            start_time = time.time()

            # This will create a real batch processing session
            batch_result = initiate_batch_processing.delay()

            # Wait for batch initiation result
            try:
                initiation_result = batch_result.get(timeout=60)

                if initiation_result.get("status") == "initiated":
                    session_id = initiation_result["session_id"]
                    logger.info(f"✅ Batch processing initiated: {session_id[:8]}...")
                    logger.info(
                        f"📊 Total batches: {initiation_result['total_batches']}"
                    )
                    logger.info(
                        f"📊 Total articles: {initiation_result['total_articles']}"
                    )
                    logger.info(
                        f"💰 Estimated cost: ${initiation_result['estimated_total_cost']:.4f}"
                    )

                    # Monitor batch progress
                    logger.info("👀 Monitoring batch progress...")

                    # Wait for batch completion (with timeout)
                    max_wait_time = 600  # 10 minutes
                    check_interval = 30  # 30 seconds
                    elapsed_time = 0

                    while elapsed_time < max_wait_time:
                        await asyncio.sleep(check_interval)
                        elapsed_time += check_interval

                        # Check batch status
                        from crypto_newsletter.newsletter.batch.monitoring import (
                            get_batch_processing_status,
                        )

                        status = get_batch_processing_status(session_id)

                        if "progress" in status:
                            progress = status["progress"]
                            logger.info(
                                f"📊 Progress: {progress['completion_percentage']:.1f}% "
                                f"({progress['articles_processed']}/{progress['articles_remaining'] + progress['articles_processed']} articles)"
                            )

                            if progress["completion_percentage"] >= 100:
                                logger.info("✅ Batch processing completed!")

                                # Verify results in database
                                total_time = time.time() - start_time
                                logger.info(
                                    f"⏱️  Total processing time: {total_time:.2f} seconds"
                                )

                                return await verify_batch_results(db, session_id)

                    logger.warning(
                        "⚠️  Batch processing timeout - may still be running"
                    )
                    return False

                else:
                    logger.error(f"❌ Batch initiation failed: {initiation_result}")
                    return False

            except Exception as e:
                logger.error(f"❌ Batch processing failed: {e}")
                return False

    except Exception as e:
        logger.error(f"❌ Small batch processing test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def verify_batch_results(db, session_id: str):
    """Verify batch processing results in database."""

    logger.info("🔍 Verifying batch processing results...")

    try:
        from crypto_newsletter.newsletter.batch.storage import BatchStorageManager
        from sqlalchemy import text

        storage = BatchStorageManager()

        # Get batch session with records
        session = await storage.get_batch_session_with_records(db, session_id)

        if not session:
            logger.error("❌ Batch session not found")
            return False

        logger.info(f"📊 Session status: {session.status}")
        logger.info(f"💰 Actual cost: ${session.actual_cost or 0:.4f}")

        # Check batch records
        completed_batches = sum(
            1 for r in session.batch_records if r.status == "COMPLETED"
        )
        failed_batches = sum(1 for r in session.batch_records if r.status == "FAILED")

        logger.info(f"✅ Completed batches: {completed_batches}")
        logger.info(f"❌ Failed batches: {failed_batches}")

        # Check if analyses were created
        total_processed = sum(r.articles_processed or 0 for r in session.batch_records)

        analysis_count_query = text(
            """
            SELECT COUNT(*) as count
            FROM article_analyses aa
            JOIN batch_processing_records bpr ON aa.article_id = ANY(bpr.article_ids)
            WHERE bpr.session_id = :session_id
        """
        )

        result = await db.execute(analysis_count_query, {"session_id": session_id})
        analyses_created = result.scalar()

        logger.info(f"📊 Articles processed: {total_processed}")
        logger.info(f"📊 Analyses created: {analyses_created}")

        if analyses_created > 0:
            logger.info("✅ Batch processing results verified successfully")
            return True
        else:
            logger.error("❌ No analyses were created")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to verify batch results: {e}")
        return False


async def main():
    """Main test function."""

    logger.info("🚀 REAL BATCH PROCESSING TEST - COMPLETE END-TO-END VALIDATION")
    logger.info("=" * 80)

    try:
        # Test 1: Single article analysis
        single_success = await test_single_article_analysis()

        if not single_success:
            logger.error("❌ Single article analysis failed - stopping tests")
            return False

        # Test 2: Small batch processing
        batch_success = await test_small_batch_processing()

        # Final verdict
        logger.info("\n" + "=" * 80)
        logger.info("🏁 REAL BATCH PROCESSING TEST RESULTS")
        logger.info("=" * 80)

        if single_success and batch_success:
            logger.info("🎉 ALL TESTS PASSED - Phase 1 is TRULY COMPLETE!")
            logger.info("✅ Single article analysis working with real APIs")
            logger.info("✅ Batch processing workflow fully functional")
            logger.info("✅ Database integration confirmed")
            logger.info("✅ Ready to proceed to Phase 2")
            return True
        else:
            logger.error("❌ TESTS FAILED - Phase 1 needs more work")
            if not single_success:
                logger.error("❌ Single article analysis issues")
            if not batch_success:
                logger.error("❌ Batch processing issues")
            return False

    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
