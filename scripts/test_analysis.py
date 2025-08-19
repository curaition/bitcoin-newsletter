#!/usr/bin/env python3
"""
Test script for PydanticAI analysis agents.

Usage:
    python scripts/test_analysis.py --test-mode  # Use TestModel
    python scripts/test_analysis.py --article-id 123  # Analyze specific article
    python scripts/test_analysis.py --sample  # Use sample content
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("🔧 Testing PydanticAI 0.7.2 Integration...")

try:
    import pydantic_ai

    print(f"✅ PydanticAI version: {pydantic_ai.__version__}")
except ImportError as e:
    print(f"❌ Failed to import PydanticAI: {e}")
    sys.exit(1)

try:
    from crypto_newsletter.analysis.agents.content_analysis import (
        content_analysis_agent,
    )
    from crypto_newsletter.analysis.agents.settings import analysis_settings
    from crypto_newsletter.analysis.agents.signal_validation import (
        signal_validation_agent,
    )
    from crypto_newsletter.analysis.dependencies import (
        AnalysisDependencies,
        CostTracker,
    )

    print("✅ Successfully imported analysis agents")
except ImportError as e:
    print(f"❌ Failed to import analysis components: {e}")
    sys.exit(1)


async def test_with_sample_content():
    """Test analysis with sample Bitcoin article content."""

    sample_title = "Bitcoin ETF Sees Record Inflows Amid Institutional Adoption"
    sample_body = """
    Bitcoin exchange-traded funds experienced unprecedented inflows of $1.2 billion
    last week, marking the highest weekly inflow since their launch earlier this year.
    The surge comes as institutional investors increasingly view Bitcoin as a viable
    hedge against inflation and currency debasement.

    Several major pension funds, including the California Public Employees' Retirement
    System (CalPERS), have reportedly allocated portions of their portfolios to Bitcoin
    ETFs, signaling a significant shift in institutional sentiment toward cryptocurrency.

    "We're seeing a fundamental change in how traditional finance views Bitcoin," said
    Sarah Chen, a portfolio manager at Institutional Crypto Advisors. "What was once
    considered too risky is now being viewed as a necessary diversification tool."

    The development comes amid growing concerns about monetary policy and inflation.
    Central banks worldwide have maintained accommodative policies, leading some
    institutional investors to seek alternative stores of value.

    Market analysts note that this institutional adoption could lead to reduced
    volatility in Bitcoin prices over time, as large institutional holders typically
    have longer investment horizons compared to retail traders.

    However, some critics argue that the correlation between Bitcoin and traditional
    risk assets has increased during market stress periods, potentially undermining
    its effectiveness as a hedge.
    """

    sample_publisher = "CoinDesk"

    # Set up dependencies
    deps = AnalysisDependencies(
        db_session=None,  # Mock for testing
        cost_tracker=CostTracker(daily_budget=10.0),
        current_publisher=sample_publisher,
        current_article_id=999,  # Test ID
        max_searches_per_validation=3,
        min_signal_confidence=0.3,
    )

    print("🚀 Starting analysis of sample Bitcoin article...")
    print(f"📰 Title: {sample_title}")
    print(f"📊 Publisher: {sample_publisher}")
    print(f"💰 Budget: ${deps.cost_tracker.daily_budget}")
    print("-" * 60)

    try:
        result = await orchestrator.analyze_article(
            article_id=999,
            title=sample_title,
            body=sample_body,
            publisher=sample_publisher,
            deps=deps,
        )

        if result["success"]:
            print("✅ Analysis completed successfully!")
            print(f"💰 Total cost: ${result['costs']['total']:.4f}")
            print(f"🔍 Signals found: {result['processing_metadata']['signals_found']}")
            print(
                f"✅ Signals validated: {result['processing_metadata']['signals_validated']}"
            )
            print(
                f"📊 Analysis confidence: {result['processing_metadata']['analysis_confidence']:.2f}"
            )
            print(
                f"💪 Signal strength: {result['processing_metadata']['signal_strength']:.2f}"
            )

            # Show content analysis results
            content_analysis = result["content_analysis"]
            print("\n📋 CONTENT ANALYSIS RESULTS:")
            print(f"Sentiment: {content_analysis.sentiment}")
            print(f"Impact Score: {content_analysis.impact_score:.2f}")
            print(f"Summary: {content_analysis.summary}")

            print(f"\n🔍 WEAK SIGNALS ({len(content_analysis.weak_signals)}):")
            for i, signal in enumerate(content_analysis.weak_signals, 1):
                print(f"{i}. {signal.signal_type}: {signal.description}")
                print(f"   Confidence: {signal.confidence:.2f}")
                print(f"   Implications: {signal.implications}")
                print(f"   Evidence: {'; '.join(signal.evidence[:2])}...")
                print()

            # Show validation results if available
            if result.get("signal_validation"):
                validation = result["signal_validation"]
                print(f"🔬 VALIDATION RESULTS ({len(validation.validation_results)}):")
                for val_result in validation.validation_results:
                    print(f"Signal: {val_result.signal_id}")
                    print(f"Status: {val_result.validation_status}")
                    print(
                        f"Confidence Adjustment: {val_result.confidence_adjustment:+.2f}"
                    )
                    print()
        else:
            print("❌ Analysis failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            if result.get("requires_manual_review"):
                print("🔍 Requires manual review")

    except Exception as e:
        print(f"❌ Analysis failed with exception: {str(e)}")
        import traceback

        traceback.print_exc()


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test PydanticAI analysis agents")
    parser.add_argument(
        "--test-mode", action="store_true", help="Use TestModel instead of real LLM"
    )
    parser.add_argument("--article-id", type=int, help="Analyze specific article by ID")
    parser.add_argument("--sample", action="store_true", help="Use sample content")

    args = parser.parse_args()

    # Set testing mode if requested
    if args.test_mode:
        analysis_settings.testing = True
        print("🧪 Running in test mode (using TestModel)")

    if args.sample or not args.article_id:
        await test_with_sample_content()
    else:
        print(f"📰 Article ID analysis not implemented yet: {args.article_id}")
        print("Use --sample flag to test with sample content")


if __name__ == "__main__":
    asyncio.run(main())
