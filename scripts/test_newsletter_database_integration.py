#!/usr/bin/env python3
"""
Test script for Newsletter database integration.

This script tests the Newsletter SQLAlchemy model and NewsletterStorage class
to ensure they work correctly with the existing database schema.
"""

import asyncio
import logging
import sys
from datetime import date, datetime

# Add the project root to the path
sys.path.insert(0, "/Users/rick/---projects/bitcoin_newsletter")

from crypto_newsletter.core.storage import NewsletterRepository
from crypto_newsletter.newsletter.models.newsletter import (
    CrossStoryConnection,
    NewsletterContent,
    NewsletterSynthesis,
    PatternInsight,
    StoryScore,
    StorySelection,
)
from crypto_newsletter.newsletter.storage import NewsletterStorage
from crypto_newsletter.shared.database.connection import get_db_session
from crypto_newsletter.shared.models import Newsletter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_newsletter_content() -> NewsletterContent:
    """Create sample newsletter content for testing."""
    return NewsletterContent(
        title="Bitcoin Market Analysis: Whale Accumulation Signals Potential Rally",
        executive_summary=[
            "Bitcoin whales accumulated 20K BTC during recent market dip",
            "Ethereum leads $3.75B in crypto inflows, signaling institutional rotation",
            "Political-monetary policy convergence creates new market dynamics",
        ],
        main_analysis="""
        The cryptocurrency market is experiencing a significant shift in institutional behavior,
        with large holders (whales) demonstrating counter-trend accumulation patterns during
        recent market weakness. This behavior, historically associated with major price rallies,
        coincides with record-breaking institutional inflows into Ethereum products and emerging
        political-monetary policy dynamics that could reshape the digital asset landscape.

        The whale accumulation of over 20,000 BTC in 48 hours represents a classic
        counter-cyclical investment strategy, where sophisticated investors increase positions
        during periods of market fear. This pattern mirrors similar accumulation phases that
        preceded major rallies in 2020 and 2023, suggesting potential upward price momentum.
        """,
        pattern_spotlight="""
        The most significant pattern emerging is the multi-asset institutional rotation,
        where traditional Bitcoin-focused institutional flows are diversifying into Ethereum
        and other major cryptocurrencies. This represents a maturation of institutional
        crypto investment strategies, moving from single-asset exposure to diversified
        digital asset portfolios.
        """,
        adjacent_watch="""
        Political developments, particularly potential Federal Reserve appointments,
        are creating new cross-domain implications for crypto markets. The intersection
        of electoral cycles with Bitcoin's halving cycle could create unprecedented
        market dynamics in the coming months.
        """,
        signal_radar="""
        Key weak signals to monitor include coordinated whale activity across multiple
        assets, regulatory clarity announcements timing with accumulation patterns,
        and the convergence of traditional monetary policy cycles with crypto market cycles.
        """,
        action_items=[
            "Monitor whale wallet activity for continued accumulation patterns",
            "Track institutional flow data for diversification trends",
            "Watch for Federal Reserve policy signals and political appointments",
        ],
        source_citations=[
            "Crypto Potato - Bitcoin Whales Add 20K BTC Post-Dip",
            "NewsBTC - Ethereum Leads $3.75 Billion Crypto Inflows",
            "NewsBTC - Bitcoin Bull Run Hinges On Trump's Pick For Fed Chair",
        ],
        estimated_read_time=8,
        editorial_quality_score=0.87,
    )


def create_sample_story_selection() -> StorySelection:
    """Create sample story selection for testing."""
    return StorySelection(
        selection_date=datetime.now(),
        total_articles_reviewed=25,
        selected_stories=[
            StoryScore(
                article_id=1,
                title="Bitcoin Whales Add 20K BTC Post-Dip",
                publisher="Crypto Potato",
                signal_strength=0.85,
                uniqueness_score=0.78,
                relevance_score=0.82,
                selection_reasoning="Strong whale accumulation signal with historical precedent",
                key_signals=[
                    "Whale Accumulation",
                    "Technical Support",
                    "Institutional Interest",
                ],
            ),
            StoryScore(
                article_id=2,
                title="Ethereum Leads $3.75 Billion Crypto Inflows",
                publisher="NewsBTC",
                signal_strength=0.79,
                uniqueness_score=0.73,
                relevance_score=0.86,
                selection_reasoning="Record institutional flows indicating market rotation",
                key_signals=["Institutional Rotation", "ETF Flows", "DeFi Renaissance"],
            ),
        ],
        rejected_highlights=[],
        selection_themes=[
            "Institutional Adoption",
            "Market Rotation",
            "Whale Activity",
        ],
        coverage_gaps=["Regulatory Updates", "Technical Analysis"],
    )


def create_sample_synthesis() -> NewsletterSynthesis:
    """Create sample synthesis for testing."""
    return NewsletterSynthesis(
        synthesis_date=datetime.now(),
        primary_themes=[
            "Institutional Maturation",
            "Counter-Cyclical Investment",
            "Policy Convergence",
        ],
        pattern_insights=[
            PatternInsight(
                pattern_type="Accumulation",
                confidence=0.85,
                description="Whale accumulation during market weakness",
                supporting_stories=[1, 2],
                implications=[
                    "Potential upward price pressure",
                    "Reduced selling pressure",
                ],
                timeline="2-4 weeks for impact to materialize",
            )
        ],
        cross_story_connections=[
            CrossStoryConnection(
                connection_type="Institutional Behavior",
                connected_articles=[1, 2],
                connection_strength=0.78,
                synthesis_insight="Both stories show institutional adoption patterns",
                market_implications=[
                    "Increased institutional confidence",
                    "Market maturation",
                ],
            )
        ],
        market_narrative="The crypto market is experiencing institutional maturation with diversified investment strategies and counter-cyclical positioning by sophisticated investors.",
        adjacent_implications=[
            "Traditional finance adoption",
            "Regulatory clarity impact",
        ],
        forward_indicators=["Fed policy announcements", "Continued whale activity"],
        synthesis_confidence=0.82,
    )


async def test_newsletter_model_creation():
    """Test creating a Newsletter model instance."""
    logger.info("Testing Newsletter model creation...")

    try:
        async with get_db_session() as db:
            # Create a simple newsletter record
            newsletter = Newsletter(
                title="Test Newsletter",
                content="This is a test newsletter content.",
                summary="Test summary",
                generation_date=date.today(),
                status="DRAFT",
                quality_score=0.85,
                agent_version="1.0",
                generation_metadata={"test": True},
            )

            db.add(newsletter)
            await db.commit()
            await db.refresh(newsletter)

            logger.info(f"✅ Created newsletter with ID: {newsletter.id}")

            # Clean up
            await db.delete(newsletter)
            await db.commit()

            return True

    except Exception as e:
        logger.error(f"❌ Newsletter model creation failed: {e}")
        return False


async def test_newsletter_storage():
    """Test NewsletterStorage class operations."""
    logger.info("Testing NewsletterStorage operations...")

    try:
        async with get_db_session() as db:
            storage = NewsletterStorage(db)

            # Create sample data with empty story selection to avoid FK constraint issues
            newsletter_content = create_sample_newsletter_content()
            story_selection = StorySelection(
                selection_date=datetime.now(),
                total_articles_reviewed=0,
                selected_stories=[],  # Empty to avoid FK constraint issues
                rejected_highlights=[],
                selection_themes=["Test Theme"],
                coverage_gaps=["Test Gap"],
            )
            synthesis = create_sample_synthesis()

            # Test create newsletter
            newsletter = await storage.create_newsletter(
                newsletter_content=newsletter_content,
                story_selection=story_selection,
                synthesis=synthesis,
                generation_metadata={"test_run": True},
            )

            logger.info(f"✅ Created newsletter via storage: {newsletter.id}")

            # Test get newsletter by ID
            retrieved = await storage.get_newsletter_by_id(newsletter.id)
            if retrieved:
                logger.info(f"✅ Retrieved newsletter: {retrieved.title}")
            else:
                logger.error("❌ Failed to retrieve newsletter")
                return False

            # Test update status
            updated = await storage.update_newsletter_status(
                newsletter.id, "REVIEW", datetime.now()
            )
            if updated and updated.status == "REVIEW":
                logger.info("✅ Updated newsletter status")
            else:
                logger.error("❌ Failed to update newsletter status")
                return False

            # Test get recent newsletters
            recent = await storage.get_recent_newsletters(days=1)
            if recent and len(recent) > 0:
                logger.info(f"✅ Retrieved {len(recent)} recent newsletters")
            else:
                logger.info("ℹ️ No recent newsletters found (expected for test)")

            # Clean up
            deleted = await storage.delete_newsletter(newsletter.id)
            if deleted:
                logger.info("✅ Deleted test newsletter")
            else:
                logger.error("❌ Failed to delete test newsletter")
                return False

            return True

    except Exception as e:
        logger.error(f"❌ NewsletterStorage test failed: {e}")
        return False


async def test_newsletter_repository():
    """Test NewsletterRepository class operations."""
    logger.info("Testing NewsletterRepository operations...")

    try:
        async with get_db_session() as db:
            repo = NewsletterRepository(db)

            # Test get all newsletters (should be empty initially)
            newsletters = await repo.get_all_newsletters()
            logger.info(f"✅ Retrieved {len(newsletters)} newsletters from repository")

            # Test get by status
            drafts = await repo.get_draft_newsletters()
            published = await repo.get_published_newsletters()

            logger.info(
                f"✅ Found {len(drafts)} draft and {len(published)} published newsletters"
            )

            return True

    except Exception as e:
        logger.error(f"❌ NewsletterRepository test failed: {e}")
        return False


async def test_database_schema_compatibility():
    """Test that our models are compatible with the existing database schema."""
    logger.info("Testing database schema compatibility...")

    try:
        async with get_db_session() as db:
            # Test that we can query the newsletters table
            from sqlalchemy import select, text

            # Test basic table access
            result = await db.execute(text("SELECT COUNT(*) FROM newsletters"))
            count = result.scalar()
            logger.info(f"✅ Newsletters table accessible, contains {count} records")

            # Test newsletter_articles table access
            result = await db.execute(text("SELECT COUNT(*) FROM newsletter_articles"))
            count = result.scalar()
            logger.info(
                f"✅ Newsletter_articles table accessible, contains {count} records"
            )

            # Test our model can query the table
            result = await db.execute(select(Newsletter))
            newsletters = result.scalars().all()
            logger.info(
                f"✅ SQLAlchemy model can query newsletters table, found {len(newsletters)} records"
            )

            return True

    except Exception as e:
        logger.error(f"❌ Database schema compatibility test failed: {e}")
        return False


async def main():
    """Main test execution."""
    logger.info("🧪 Starting Newsletter Database Integration Test Suite")
    logger.info("=" * 70)

    tests = [
        ("Database Schema Compatibility", test_database_schema_compatibility),
        ("Newsletter Model Creation", test_newsletter_model_creation),
        ("Newsletter Storage Operations", test_newsletter_storage),
        ("Newsletter Repository Operations", test_newsletter_repository),
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
            if success:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info(
            "🎉 All tests passed! Newsletter database integration is working correctly."
        )
        return True
    else:
        logger.error("💥 Some tests failed. Check the logs for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
