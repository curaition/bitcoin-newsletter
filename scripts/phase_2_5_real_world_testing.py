#!/usr/bin/env python3
"""
Phase 2.5 Real-World Testing Script for Bitcoin Newsletter Signal Analysis

This script validates the PydanticAI analysis agents against real articles from the
production Neon database using real APIs (Gemini + Tavily).

Usage:
    python scripts/phase_2_5_real_world_testing.py --select-articles  # Interactive article selection
    python scripts/phase_2_5_real_world_testing.py --test-all         # Test with pre-selected articles
    python scripts/phase_2_5_real_world_testing.py --article-ids 123,456,789  # Test specific articles
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

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

print("🚀 Phase 2.5 Real-World Testing - Bitcoin Newsletter Signal Analysis")
print("=" * 70)

# Import required modules
try:
    from crypto_newsletter.analysis.agents.orchestrator import orchestrator
    from crypto_newsletter.analysis.agents.settings import analysis_settings
    from crypto_newsletter.analysis.dependencies import (
        AnalysisDependencies,
        CostTracker,
    )
    from crypto_newsletter.core.storage.repository import ArticleRepository
    from crypto_newsletter.shared.database.connection import get_db_session

    print("✅ Successfully imported all required modules")
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    sys.exit(1)


class Phase25TestRunner:
    """Manages Phase 2.5 real-world testing workflow."""

    def __init__(self):
        self.test_results = []
        self.total_cost = 0.0
        self.start_time = None
        self.end_time = None

    async def get_analysis_ready_articles(
        self, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get analysis-ready articles from the database."""
        print(f"📊 Querying database for analysis-ready articles (limit: {limit})...")

        async with get_db_session() as db:
            repo = ArticleRepository(db)
            articles = await repo.get_analysis_ready_articles(
                limit=limit, min_content_length=2000
            )

        print(f"✅ Found {len(articles)} analysis-ready articles")
        return articles

    async def get_article_details(self, article_id: int) -> Optional[dict[str, Any]]:
        """Get full article details including body content."""
        from crypto_newsletter.shared.models.models import Article, Publisher
        from sqlalchemy import select

        async with get_db_session() as db:
            query = (
                select(Article, Publisher.name.label("publisher_name"))
                .join(Publisher, isouter=True)
                .where(Article.id == article_id)
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
                "published_on": (
                    article.published_on.isoformat() if article.published_on else None
                ),
                "url": article.url,
                "content_length": len(article.body) if article.body else 0,
            }

    def display_article_selection(self, articles: list[dict[str, Any]]) -> None:
        """Display articles for selection."""
        print("\n📰 Available Analysis-Ready Articles:")
        print("-" * 70)

        for i, article in enumerate(articles, 1):
            content_len = article["content_length"]
            title = article["title"][:60]
            published = article.get("published_on", "Unknown")
            url = article["url"][:80]

            print(f"{i:2d}. [{content_len:4d} chars] {title}...")
            print(f"    Published: {published}")
            print(f"    URL: {url}...")
            print()

    async def select_test_articles(self, articles: list[dict[str, Any]]) -> list[int]:
        """Interactive article selection for testing."""
        self.display_article_selection(articles)

        print("🎯 Phase 2.5 Testing Strategy:")
        print("   - Select 5 diverse articles for comprehensive testing")
        print("   - Recommended: 2 NewsBTC, 2 CoinDesk, 1 Crypto Potato")
        print("   - Focus on different content types and lengths")
        print()

        selected_ids = []
        while len(selected_ids) < 5:
            try:
                choice = input(
                    f"Select article {len(selected_ids) + 1}/5 (enter number 1-{len(articles)}): "
                )
                if choice.lower() in ["q", "quit", "exit"]:
                    break

                idx = int(choice) - 1
                if 0 <= idx < len(articles):
                    article_id = articles[idx]["id"]
                    if article_id not in selected_ids:
                        selected_ids.append(article_id)
                        print(f"✅ Selected: {articles[idx]['title'][:50]}...")
                    else:
                        print("⚠️  Article already selected")
                else:
                    print("❌ Invalid selection")
            except (ValueError, KeyboardInterrupt):
                print("\n👋 Selection cancelled")
                break

        return selected_ids

    async def test_article_analysis(self, article_id: int) -> dict[str, Any]:
        """Test analysis on a single article."""
        print(f"\n🔬 Testing Analysis for Article ID: {article_id}")
        print("-" * 50)

        # Get article details
        article = await self.get_article_details(article_id)
        if not article:
            return {
                "article_id": article_id,
                "success": False,
                "error": "Article not found",
                "cost": 0.0,
                "processing_time": 0.0,
            }

        print(f"📰 Title: {article['title']}")
        print(f"📊 Publisher: {article['publisher']}")
        print(f"📏 Content Length: {article['content_length']} characters")
        print(f"📅 Published: {article['published_on']}")

        # Set up analysis dependencies
        cost_tracker = CostTracker(daily_budget=5.0)  # Conservative budget per article

        async with get_db_session() as db:
            deps = AnalysisDependencies(
                db_session=db,
                cost_tracker=cost_tracker,
                current_publisher=article["publisher"],
                current_article_id=article_id,
                max_searches_per_validation=3,  # Limit external searches
                min_signal_confidence=0.3,
            )

            # Run analysis
            start_time = time.time()

            try:
                result = await orchestrator.analyze_article(
                    article_id=article_id,
                    title=article["title"],
                    body=article["body"],
                    publisher=article["publisher"],
                    deps=deps,
                )

                processing_time = time.time() - start_time

                # Add metadata to result
                result.update(
                    {
                        "article_metadata": {
                            "title": article["title"],
                            "publisher": article["publisher"],
                            "content_length": article["content_length"],
                            "published_on": article["published_on"],
                            "url": article["url"],
                        },
                        "processing_time": processing_time,
                    }
                )

                return result

            except Exception as e:
                processing_time = time.time() - start_time
                return {
                    "article_id": article_id,
                    "success": False,
                    "error": str(e),
                    "cost": cost_tracker.total_cost,
                    "processing_time": processing_time,
                    "article_metadata": {
                        "title": article["title"],
                        "publisher": article["publisher"],
                        "content_length": article["content_length"],
                    },
                }

    def display_analysis_results(self, result: dict[str, Any]) -> None:
        """Display detailed analysis results."""
        article_id = result["article_id"]
        metadata = result.get("article_metadata", {})

        print(f"\n📊 ANALYSIS RESULTS - Article {article_id}")
        print("=" * 60)
        print(f"📰 Title: {metadata.get('title', 'Unknown')}")
        print(f"📊 Publisher: {metadata.get('publisher', 'Unknown')}")
        print(f"⏱️  Processing Time: {result.get('processing_time', 0):.2f} seconds")
        print(f"💰 Cost: ${result.get('costs', {}).get('total', 0):.4f}")

        if result["success"]:
            content_analysis = result.get("content_analysis")
            if content_analysis:
                print("\n🎯 CONTENT ANALYSIS:")
                print(f"   Sentiment: {content_analysis.sentiment}")
                print(f"   Impact Score: {content_analysis.impact_score:.2f}")
                print(
                    f"   Analysis Confidence: {content_analysis.analysis_confidence:.2f}"
                )
                print(f"   Signal Strength: {content_analysis.signal_strength:.2f}")
                print(f"   Summary: {content_analysis.summary[:100]}...")

                print(f"\n🔍 WEAK SIGNALS ({len(content_analysis.weak_signals)}):")
                for i, signal in enumerate(
                    content_analysis.weak_signals[:3], 1
                ):  # Show first 3
                    print(f"   {i}. {signal.signal_type}: {signal.description[:80]}...")
                    print(
                        f"      Confidence: {signal.confidence:.2f} | Timeframe: {signal.timeframe}"
                    )

                if len(content_analysis.weak_signals) > 3:
                    print(
                        f"   ... and {len(content_analysis.weak_signals) - 3} more signals"
                    )

            # Show validation results if available
            validation = result.get("signal_validation")
            if validation:
                print(f"\n🔬 SIGNAL VALIDATION ({len(validation.validation_results)}):")
                for val_result in validation.validation_results[:2]:  # Show first 2
                    print(f"   Signal: {val_result.signal_id}")
                    print(f"   Status: {val_result.validation_status}")
                    print(
                        f"   Supporting Evidence: {len(val_result.supporting_evidence)} items"
                    )
        else:
            print(f"\n❌ ANALYSIS FAILED: {result.get('error', 'Unknown error')}")

        print("-" * 60)

    async def run_comprehensive_test(self, article_ids: list[int]) -> None:
        """Run comprehensive testing on selected articles."""
        self.start_time = datetime.now()
        print("\n🚀 Starting Phase 2.5 Comprehensive Testing")
        print(f"📅 Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Testing {len(article_ids)} articles with real APIs")
        print("💰 Budget: $5.00 per article (estimated)")
        print("=" * 70)

        for i, article_id in enumerate(article_ids, 1):
            print(f"\n🔄 Processing Article {i}/{len(article_ids)}")

            result = await self.test_article_analysis(article_id)
            self.test_results.append(result)
            self.total_cost += result.get("costs", {}).get("total", 0)

            self.display_analysis_results(result)

            # Brief pause between articles
            if i < len(article_ids):
                print("\n⏳ Pausing 5 seconds before next article...")
                await asyncio.sleep(5)

        self.end_time = datetime.now()
        self.display_final_summary()

    def display_final_summary(self) -> None:
        """Display final testing summary."""
        duration = (self.end_time - self.start_time).total_seconds()
        successful_tests = sum(1 for r in self.test_results if r["success"])

        print("\n🎉 PHASE 2.5 TESTING COMPLETE")
        print("=" * 70)
        print(f"📅 Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"✅ Successful Analyses: {successful_tests}/{len(self.test_results)}")
        print(f"💰 Total Cost: ${self.total_cost:.4f}")
        print(
            f"📊 Average Cost per Article: ${self.total_cost/len(self.test_results):.4f}"
        )
        print(
            f"⏱️  Average Processing Time: {sum(r.get('processing_time', 0) for r in self.test_results)/len(self.test_results):.1f}s"
        )

        # Success rate analysis
        if successful_tests == len(self.test_results):
            print("🎯 SUCCESS: 100% analysis completion rate!")
        elif successful_tests >= len(self.test_results) * 0.8:
            print("⚠️  WARNING: Some analyses failed - review error details")
        else:
            print("❌ CONCERN: High failure rate - investigate issues before Phase 3")

        # Cost analysis
        if self.total_cost <= len(self.test_results) * 0.30:
            print("💰 COST: Within expected range ($0.20-$0.30 per article)")
        else:
            print("💸 COST: Higher than expected - review API usage")

        print("\n📋 Next Steps:")
        print("   1. Review individual analysis results above")
        print("   2. Validate signal quality and relevance")
        print("   3. Check for any error patterns")
        print("   4. Proceed to Phase 3 planning if results are satisfactory")

        # Save results to file
        self.save_results_to_file()

    def save_results_to_file(self) -> None:
        """Save test results to JSON file for analysis."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"phase_2_5_results_{timestamp}.json"
        filepath = Path(__file__).parent / filename

        summary_data = {
            "test_metadata": {
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration_seconds": (self.end_time - self.start_time).total_seconds(),
                "total_articles": len(self.test_results),
                "successful_analyses": sum(
                    1 for r in self.test_results if r["success"]
                ),
                "total_cost": self.total_cost,
                "average_cost_per_article": self.total_cost / len(self.test_results)
                if self.test_results
                else 0,
            },
            "test_results": self.test_results,
        }

        with open(filepath, "w") as f:
            json.dump(summary_data, f, indent=2, default=str)

        print(f"💾 Results saved to: {filepath}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Phase 2.5 Real-World Testing")
    parser.add_argument(
        "--select-articles", action="store_true", help="Interactive article selection"
    )
    parser.add_argument(
        "--test-all", action="store_true", help="Test with pre-selected articles"
    )
    parser.add_argument(
        "--article-ids", type=str, help="Comma-separated article IDs to test"
    )
    parser.add_argument("--limit", type=int, default=20, help="Limit for article query")

    args = parser.parse_args()

    # Ensure we're using real APIs, not test mode
    analysis_settings.testing = False
    print("🔧 Configuration: Using REAL APIs (Gemini + Tavily)")
    print(
        f"🔑 Gemini API Key: {'✅ Set' if analysis_settings.gemini_api_key else '❌ Missing'}"
    )
    print(
        f"🔑 Tavily API Key: {'✅ Set' if analysis_settings.tavily_api_key else '❌ Missing'}"
    )

    if not analysis_settings.gemini_api_key or not analysis_settings.tavily_api_key:
        print("❌ Missing required API keys. Check your .env.development file.")
        sys.exit(1)

    runner = Phase25TestRunner()

    if args.article_ids:
        # Test specific article IDs
        article_ids = [int(id.strip()) for id in args.article_ids.split(",")]
        await runner.run_comprehensive_test(article_ids)

    elif args.test_all:
        # Use pre-selected diverse articles (you'll need to update these IDs)
        print("🎯 Using pre-selected diverse articles for testing")
        print("⚠️  Update article IDs in script based on your database")
        # Example IDs - replace with actual IDs from your database
        article_ids = [1, 2, 3, 4, 5]  # Update these!
        await runner.run_comprehensive_test(article_ids)

    else:
        # Interactive selection (default)
        articles = await runner.get_analysis_ready_articles(args.limit)
        if not articles:
            print("❌ No analysis-ready articles found")
            return

        selected_ids = await runner.select_test_articles(articles)
        if selected_ids:
            await runner.run_comprehensive_test(selected_ids)
        else:
            print("👋 No articles selected for testing")


if __name__ == "__main__":
    asyncio.run(main())
