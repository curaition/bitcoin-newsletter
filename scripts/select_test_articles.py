#!/usr/bin/env python3
"""
Article Selection Helper for Phase 2.5 Testing

This script helps identify and select diverse, high-quality articles
for Phase 2.5 real-world testing.

Usage:
    python scripts/select_test_articles.py --show-stats    # Show database statistics
    python scripts/select_test_articles.py --recommend    # Get recommended test articles
    python scripts/select_test_articles.py --publisher NewsBTC  # Filter by publisher
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from crypto_newsletter.core.storage.repository import ArticleRepository
    from crypto_newsletter.shared.database.connection import get_db_session
    from crypto_newsletter.shared.models.models import Article, Publisher
    from sqlalchemy import desc, func, select

    print("✅ Successfully imported database modules")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    sys.exit(1)


class ArticleSelector:
    """Helper for selecting test articles."""

    async def get_database_stats(self) -> dict[str, Any]:
        """Get comprehensive database statistics."""
        async with get_db_session() as db:
            # Total articles
            total_result = await db.execute(select(func.count(Article.id)))
            total_articles = total_result.scalar()

            # Analysis-ready articles (≥2000 chars)
            analysis_ready_result = await db.execute(
                select(func.count(Article.id)).where(
                    Article.status == "ACTIVE",
                    func.length(Article.body) >= 2000,
                    Article.body.is_not(None),
                )
            )
            analysis_ready = analysis_ready_result.scalar()

            # Publisher breakdown
            publisher_stats_result = await db.execute(
                select(
                    Publisher.name,
                    func.count(Article.id).label("total"),
                    func.count(
                        func.case(
                            (func.length(Article.body) >= 2000, Article.id), else_=None
                        )
                    ).label("analysis_ready"),
                )
                .select_from(Article)
                .join(Publisher, isouter=True)
                .where(Article.status == "ACTIVE")
                .group_by(Publisher.name)
                .order_by(desc("analysis_ready"))
            )

            publisher_stats = []
            for row in publisher_stats_result:
                publisher_stats.append(
                    {
                        "name": row.name or "Unknown",
                        "total": row.total,
                        "analysis_ready": row.analysis_ready,
                        "ready_percentage": (row.analysis_ready / row.total * 100)
                        if row.total > 0
                        else 0,
                    }
                )

            return {
                "total_articles": total_articles,
                "analysis_ready": analysis_ready,
                "ready_percentage": (analysis_ready / total_articles * 100)
                if total_articles > 0
                else 0,
                "publisher_stats": publisher_stats,
            }

    async def get_recommended_test_articles(self) -> list[dict[str, Any]]:
        """Get recommended articles for Phase 2.5 testing."""
        quality_publishers = ["NewsBTC", "CoinDesk", "Crypto Potato"]

        async with get_db_session() as db:
            # Get diverse articles from quality publishers
            recommendations = []

            for publisher in quality_publishers:
                # Get 2-3 articles per publisher with different characteristics
                query = (
                    select(
                        Article.id,
                        Article.title,
                        Article.published_on,
                        Article.url,
                        func.length(Article.body).label("content_length"),
                        Publisher.name.label("publisher_name"),
                    )
                    .join(Publisher)
                    .where(
                        Article.status == "ACTIVE",
                        func.length(Article.body) >= 2000,
                        Publisher.name == publisher,
                        Article.body.is_not(None),
                    )
                    .order_by(desc(Article.published_on))
                    .limit(3)
                )

                result = await db.execute(query)
                articles = result.all()

                for article in articles:
                    recommendations.append(
                        {
                            "id": article.id,
                            "title": article.title,
                            "publisher": article.publisher_name,
                            "published_on": (
                                article.published_on.isoformat()
                                if article.published_on
                                else None
                            ),
                            "url": article.url,
                            "content_length": article.content_length,
                            "recommendation_reason": f"Recent {publisher} article",
                        }
                    )

            # Sort by content length diversity and recency
            recommendations.sort(
                key=lambda x: (-x["content_length"], x["published_on"]), reverse=True
            )

            return recommendations[:8]  # Return top 8 for selection

    async def get_articles_by_publisher(
        self, publisher_name: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get articles from specific publisher."""
        async with get_db_session() as db:
            query = (
                select(
                    Article.id,
                    Article.title,
                    Article.published_on,
                    Article.url,
                    func.length(Article.body).label("content_length"),
                    Publisher.name.label("publisher_name"),
                )
                .join(Publisher)
                .where(
                    Article.status == "ACTIVE",
                    func.length(Article.body) >= 2000,
                    Publisher.name.ilike(f"%{publisher_name}%"),
                    Article.body.is_not(None),
                )
                .order_by(desc(Article.published_on))
                .limit(limit)
            )

            result = await db.execute(query)
            articles = result.all()

            return [
                {
                    "id": article.id,
                    "title": article.title,
                    "publisher": article.publisher_name,
                    "published_on": (
                        article.published_on.isoformat()
                        if article.published_on
                        else None
                    ),
                    "url": article.url,
                    "content_length": article.content_length,
                }
                for article in articles
            ]

    def display_stats(self, stats: dict[str, Any]) -> None:
        """Display database statistics."""
        print("\n📊 DATABASE STATISTICS")
        print("=" * 50)
        print(f"Total Articles: {stats['total_articles']:,}")
        print(f"Analysis-Ready (≥2000 chars): {stats['analysis_ready']:,}")
        print(f"Ready Percentage: {stats['ready_percentage']:.1f}%")

        print("\n📈 PUBLISHER BREAKDOWN:")
        print("-" * 50)
        print(f"{'Publisher':<20} {'Total':<8} {'Ready':<8} {'%':<6}")
        print("-" * 50)

        for pub in stats["publisher_stats"][:10]:  # Top 10 publishers
            name = pub["name"][:19]
            print(
                f"{name:<20} {pub['total']:<8} {pub['analysis_ready']:<8} "
                f"{pub['ready_percentage']:<6.1f}"
            )

    def display_recommendations(self, articles: list[dict[str, Any]]) -> None:
        """Display recommended test articles."""
        print("\n🎯 RECOMMENDED TEST ARTICLES")
        print("=" * 70)
        print("Select 5 diverse articles for comprehensive Phase 2.5 testing:")
        print()

        for i, article in enumerate(articles, 1):
            print(
                f"{i:2d}. [{article['content_length']:4d} chars] "
                f"{article['publisher']}"
            )
            print(f"    {article['title'][:65]}...")
            print(f"    Published: {article['published_on']}")
            print(f"    ID: {article['id']}")
            print()

        print("💡 SELECTION STRATEGY:")
        print("   • Choose 2 NewsBTC articles (highest quality rate)")
        print("   • Choose 2 CoinDesk articles (good volume)")
        print("   • Choose 1 Crypto Potato article (good quality)")
        print("   • Vary content lengths (2000-5000+ chars)")
        print("   • Mix recent and slightly older articles")

        # Generate command for easy copy-paste
        if len(articles) >= 5:
            suggested_ids = [articles[i]["id"] for i in [0, 1, 2, 3, 4]]
            print("\n🚀 SUGGESTED COMMAND:")
            print(
                f"python scripts/phase_2_5_real_world_testing.py "
                f"--article-ids {','.join(map(str, suggested_ids))}"
            )

    def display_publisher_articles(
        self, articles: list[dict[str, Any]], publisher: str
    ) -> None:
        """Display articles from specific publisher."""
        print(f"\n📰 {publisher.upper()} ARTICLES")
        print("=" * 50)

        if not articles:
            print("No analysis-ready articles found for this publisher.")
            return

        for i, article in enumerate(articles, 1):
            print(
                f"{i:2d}. [{article['content_length']:4d} chars] "
                f"ID: {article['id']}"
            )
            print(f"    {article['title'][:65]}...")
            print(f"    Published: {article['published_on']}")
            print()


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Article Selection Helper")
    parser.add_argument(
        "--show-stats", action="store_true", help="Show database statistics"
    )
    parser.add_argument(
        "--recommend", action="store_true", help="Get recommended test articles"
    )
    parser.add_argument("--publisher", type=str, help="Filter by publisher name")
    parser.add_argument(
        "--limit", type=int, default=10, help="Limit for publisher query"
    )

    args = parser.parse_args()

    selector = ArticleSelector()

    if args.show_stats:
        print("📊 Gathering database statistics...")
        stats = await selector.get_database_stats()
        selector.display_stats(stats)

    elif args.publisher:
        print(f"📰 Getting articles from {args.publisher}...")
        articles = await selector.get_articles_by_publisher(args.publisher, args.limit)
        selector.display_publisher_articles(articles, args.publisher)

    else:
        # Default: show recommendations
        print("🎯 Generating article recommendations for Phase 2.5 testing...")
        recommendations = await selector.get_recommended_test_articles()
        selector.display_recommendations(recommendations)

        print("\n📊 For detailed statistics, run:")
        print("python scripts/select_test_articles.py --show-stats")


if __name__ == "__main__":
    asyncio.run(main())
