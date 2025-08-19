#!/usr/bin/env python3
"""
Test script for PydanticAI 0.7.2 integration.

This script tests the updated PydanticAI agents with the latest API.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set testing mode
os.environ["TESTING"] = "true"


async def test_content_analysis():
    """Test the content analysis agent."""
    print("🧪 Testing Content Analysis Agent...")

    try:
        from crypto_newsletter.analysis.agents.content_analysis import (
            content_analysis_agent,
        )
        from crypto_newsletter.analysis.dependencies import (
            AnalysisDependencies,
            CostTracker,
        )

        # Create test dependencies (we'll use None for db_session in testing)
        deps = AnalysisDependencies(
            db_session=None,  # Not needed for testing
            cost_tracker=CostTracker(daily_budget=50.0),
            current_article_id=123,
            current_publisher="Test Publisher",
        )

        # Test article content
        test_content = """
        TITLE: Bitcoin Reaches New All-Time High Amid Institutional Adoption

        PUBLISHER: CoinDesk

        CONTENT: Bitcoin has surged to a new all-time high of $75,000 as major institutions
        continue to adopt the cryptocurrency. The rally comes amid growing acceptance from
        traditional financial institutions and increasing regulatory clarity. Market analysts
        point to several factors driving the current bull run, including corporate treasury
        adoption, the launch of Bitcoin ETFs, and growing retail investor interest.

        The cryptocurrency has gained over 150% this year, outperforming traditional assets
        like gold and stocks. Institutional investors, including pension funds and insurance
        companies, are increasingly viewing Bitcoin as a hedge against inflation and currency
        debasement. This institutional adoption represents a significant shift from Bitcoin's
        early days as a niche digital asset.
        """

        # Run the agent (this will use TestModel in testing mode)
        result = await content_analysis_agent.run(test_content, deps=deps)

        print("✅ Content analysis completed!")
        print(f"📊 Result type: {type(result.output).__name__}")
        print(f"💰 Usage: {result.usage}")

        # Check if we got a proper ContentAnalysis result
        analysis = result.output
        print(f"📈 Sentiment: {analysis.sentiment}")
        print(f"🎯 Impact Score: {analysis.impact_score}")
        print(f"📝 Summary: {analysis.summary[:100]}...")
        print(f"🔍 Weak Signals: {len(analysis.weak_signals)} detected")

        return True

    except Exception as e:
        print(f"❌ Content analysis test failed: {e}")
        return False


async def test_signal_validation():
    """Test the signal validation agent."""
    print("\n🧪 Testing Signal Validation Agent...")

    try:
        from crypto_newsletter.analysis.agents.signal_validation import (
            signal_validation_agent,
        )
        from crypto_newsletter.analysis.dependencies import (
            AnalysisDependencies,
            CostTracker,
        )
        from crypto_newsletter.analysis.models.signals import WeakSignal

        # Create test dependencies (we'll use None for db_session in testing)
        deps = AnalysisDependencies(
            db_session=None,  # Not needed for testing
            cost_tracker=CostTracker(daily_budget=50.0),
            current_article_id=123,
            current_publisher="Test Publisher",
        )

        # Test signals for validation
        test_signals = [
            WeakSignal(
                signal_type="institutional_behavior",
                description="Institutional adoption accelerating",
                confidence=0.8,
                implications="Could drive sustained price growth",
                evidence=["ETF launches and corporate treasury adoption"],
                timeframe="medium-term",
            )
        ]

        validation_prompt = f"""
        SIGNALS TO VALIDATE:
        {test_signals[0].description}
        Confidence: {test_signals[0].confidence}
        Evidence: {test_signals[0].evidence[0]}

        Please validate this signal using external research.
        """

        # Run the agent (this will use TestModel in testing mode)
        result = await signal_validation_agent.run(validation_prompt, deps=deps)

        print("✅ Signal validation completed!")
        print(f"📊 Result type: {type(result.output).__name__}")
        print(f"💰 Usage: {result.usage}")

        # Check if we got a proper SignalValidation result
        validation = result.output
        print(f"✅ Validation Results: {len(validation.validation_results)} results")
        if validation.validation_results:
            sources_count = len(validation.validation_results[0].research_sources)
            print(f"🔗 Research Sources: {sources_count} sources")
        print(f"💡 Additional Signals: {len(validation.additional_signals)} found")

        return True

    except Exception as e:
        print(f"❌ Signal validation test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Testing PydanticAI 0.7.2 Integration")
    print("=" * 50)

    # Test content analysis
    content_test = await test_content_analysis()

    # Test signal validation
    validation_test = await test_signal_validation()

    print("\n" + "=" * 50)
    print("📋 Test Results:")
    print(f"✅ Content Analysis: {'PASSED' if content_test else 'FAILED'}")
    print(f"✅ Signal Validation: {'PASSED' if validation_test else 'FAILED'}")

    if content_test and validation_test:
        print(
            "\n🎉 All tests passed! PydanticAI 0.7.2 integration is working correctly."
        )
        return 0
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
