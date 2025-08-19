#!/usr/bin/env python3
"""
Test Database Storage for Phase 2.5

This script tests that the orchestrator properly stores analysis results
in the article_analyses table.

Usage:
    python scripts/test_database_storage.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load environment variables BEFORE importing analysis modules
try:
    from dotenv import load_dotenv

    env_file = Path(__file__).parent.parent / ".env.development"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"📁 Loaded environment from: {env_file}")
    else:
        print("⚠️  .env.development file not found")
except ImportError:
    print("⚠️  python-dotenv not installed, trying without explicit loading")

print("🧪 Testing Database Storage Integration")
print("=" * 50)

# Import required modules
try:
    from crypto_newsletter.analysis.agents.orchestrator import orchestrator
    from crypto_newsletter.analysis.dependencies import (
        AnalysisDependencies,
        CostTracker,
    )
    from crypto_newsletter.shared.database.connection import get_db_session
    from crypto_newsletter.shared.models.models import ArticleAnalysis
    from sqlalchemy import func, select

    print("✅ Successfully imported all required modules")
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    sys.exit(1)


async def get_test_article():
    """Get a test article for analysis."""
    async with get_db_session() as db:
        # Get article 153 (NewsBTC article we tested before)
        from crypto_newsletter.shared.models.models import Article, Publisher

        query = (
            select(Article, Publisher.name.label("publisher_name"))
            .join(Publisher, isouter=True)
            .where(Article.id == 153)
        )

        result = await db.execute(query)
        row = result.first()

        if not row:
            return None

        article, publisher_name = row

        return {
            "id": article.id,
            "title": article.title,
            "body": article.body,
            "publisher": publisher_name or "Unknown",
        }


async def check_database_before():
    """Check database state before test."""
    async with get_db_session() as db:
        # Count existing records
        result = await db.execute(select(func.count(ArticleAnalysis.id)))
        count_before = result.scalar()

        # Check if article 153 already has analysis
        result = await db.execute(
            select(func.count(ArticleAnalysis.id)).where(
                ArticleAnalysis.article_id == 153
            )
        )
        article_153_count = result.scalar()

        print("📊 Database state before test:")
        print(f"   Total analysis records: {count_before}")
        print(f"   Article 153 analysis records: {article_153_count}")

        return count_before, article_153_count


async def check_database_after():
    """Check database state after test."""
    async with get_db_session() as db:
        # Count total records
        result = await db.execute(select(func.count(ArticleAnalysis.id)))
        count_after = result.scalar()

        # Get article 153 analysis records
        result = await db.execute(
            select(ArticleAnalysis)
            .where(ArticleAnalysis.article_id == 153)
            .order_by(ArticleAnalysis.created_at.desc())
        )
        article_153_records = result.scalars().all()

        print("📊 Database state after test:")
        print(f"   Total analysis records: {count_after}")
        print(f"   Article 153 analysis records: {len(article_153_records)}")

        if article_153_records:
            latest_record = article_153_records[0]
            print(f"   Latest record ID: {latest_record.id}")
            print(f"   Sentiment: {latest_record.sentiment}")
            print(f"   Impact Score: {latest_record.impact_score}")
            print(
                f"   Weak Signals: {len(latest_record.weak_signals) if latest_record.weak_signals else 0}"
            )
            print(f"   Validation Status: {latest_record.validation_status}")
            print(f"   Cost: ${latest_record.cost_usd}")
            print(f"   Token Usage: {latest_record.token_usage}")

            return latest_record

        return None


async def test_database_storage():
    """Test the complete analysis with database storage."""
    print("\n🔬 Running Database Storage Test")
    print("-" * 40)

    # Check database state before
    count_before, article_153_before = await check_database_before()

    # Get test article
    article = await get_test_article()
    if not article:
        print("❌ Test article 153 not found")
        return False

    print(f"\n📰 Testing with Article {article['id']}: {article['title'][:50]}...")

    # Set up analysis dependencies
    async with get_db_session() as db:
        cost_tracker = CostTracker(daily_budget=5.0)
        deps = AnalysisDependencies(
            db_session=db,
            cost_tracker=cost_tracker,
            current_publisher=article["publisher"],
            current_article_id=article["id"],
            max_searches_per_validation=2,  # Limit for testing
            min_signal_confidence=0.3,
        )

        # Run analysis with database storage
        print("🔄 Running analysis with database storage...")
        result = await orchestrator.analyze_article(
            article_id=article["id"],
            title=article["title"],
            body=article["body"],
            publisher=article["publisher"],
            deps=deps,
        )

        if result["success"]:
            print("✅ Analysis completed successfully!")
            print(
                f"   Analysis Record ID: {result.get('analysis_record_id', 'Not provided')}"
            )
            print(f"   Signals Found: {result['processing_metadata']['signals_found']}")
            print(f"   Cost: ${result['costs']['total']:.4f}")

            # Check database state after
            stored_record = await check_database_after()

            if stored_record:
                print("\n✅ Database storage successful!")
                print(f"   Record stored with ID: {stored_record.id}")
                return True
            else:
                print("\n❌ Database storage failed - no record found")
                return False
        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
            return False


async def main():
    """Main test function."""
    print("Starting database storage integration test...\n")

    try:
        success = await test_database_storage()

        print("\n" + "=" * 50)
        if success:
            print("🎉 DATABASE STORAGE TEST PASSED!")
            print("✅ Analysis results are being stored correctly")
            print("✅ Ready for Phase 3 or Phase 4 implementation")
        else:
            print("❌ DATABASE STORAGE TEST FAILED!")
            print("❌ Analysis results are not being stored")
            print("❌ Need to fix storage integration before proceeding")

        return success

    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
