#!/usr/bin/env python3
"""
Test script for newsletter generation agents.

This script tests the simplified newsletter generation system with sample data
to validate the agent workflow before deploying to production.
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to the path
sys.path.insert(0, "/Users/rick/---projects/bitcoin_newsletter")

from crypto_newsletter.newsletter.agents.orchestrator import newsletter_orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_articles() -> List[Dict[str, Any]]:
    """Create sample analyzed articles for testing."""
    
    return [
        {
            "id": 1,
            "title": "Bitcoin Whales Add 20K BTC Post-Dip: Historical Data Hints at Upward Price Momentum",
            "publisher": "Crypto Potato",
            "published_on": "2025-08-19T15:29:12.000Z",
            "body": "Bitcoin whales have been accumulating significant amounts of BTC following the recent market dip, with on-chain data showing a net addition of over 20,000 BTC to whale wallets in the past 48 hours. This accumulation pattern has historically preceded major upward price movements, according to blockchain analytics firms. The whale activity coincides with increased institutional interest and regulatory clarity in several key markets. Market analysts suggest this could signal the beginning of a new bullish phase, particularly as the accumulation is happening at key technical support levels. The pattern mirrors similar whale behavior seen before previous major rallies in 2020 and 2023.",
            "signal_strength": 0.85,
            "uniqueness_score": 0.78,
            "analysis_confidence": 0.82,
            "weak_signals": [
                {"signal": "Whale Accumulation Pattern", "description": "Large holders adding to positions during dip"},
                {"signal": "Technical Support Confluence", "description": "Accumulation at key support levels"},
                {"signal": "Institutional Interest Uptick", "description": "Increased institutional wallet activity"}
            ],
            "pattern_anomalies": [
                {"pattern": "Counter-Trend Accumulation", "description": "Buying during market fear periods"},
                {"pattern": "Coordinated Whale Activity", "description": "Multiple large wallets acting simultaneously"}
            ],
            "adjacent_connections": [
                {"connection": "Traditional Finance", "description": "Correlation with institutional treasury strategies"},
                {"connection": "Regulatory Environment", "description": "Timing with regulatory clarity announcements"}
            ]
        },
        {
            "id": 2,
            "title": "Ethereum Leads $3.75 Billion Crypto Inflows, XRP And Solana Join The Party",
            "publisher": "NewsBTC",
            "published_on": "2025-08-19T15:00:36.000Z",
            "body": "Ethereum has captured the lion's share of this week's record-breaking $3.75 billion in cryptocurrency inflows, with ETH products alone accounting for $2.1 billion. The surge represents the largest weekly inflow since the launch of spot ETH ETFs, signaling renewed institutional confidence in the Ethereum ecosystem. XRP and Solana also saw significant inflows of $450 million and $380 million respectively, suggesting a broader altcoin rotation is underway. The inflows coincide with major network upgrades and increased DeFi activity across these platforms. Analysts note this represents a shift from Bitcoin-dominated flows to a more diversified institutional approach to crypto investing.",
            "signal_strength": 0.79,
            "uniqueness_score": 0.73,
            "analysis_confidence": 0.86,
            "weak_signals": [
                {"signal": "Altcoin Institutional Rotation", "description": "Shift from BTC-only to diversified crypto allocation"},
                {"signal": "ETF Flow Acceleration", "description": "Record inflows to Ethereum ETF products"},
                {"signal": "DeFi Renaissance", "description": "Increased activity across multiple DeFi protocols"}
            ],
            "pattern_anomalies": [
                {"pattern": "Multi-Asset Institutional Adoption", "description": "Simultaneous inflows across different crypto assets"},
                {"pattern": "Network Effect Amplification", "description": "Upgrades driving disproportionate capital flows"}
            ],
            "adjacent_connections": [
                {"connection": "Traditional ETF Market", "description": "Crypto ETFs following traditional fund flow patterns"},
                {"connection": "Technology Sector", "description": "Correlation with enterprise blockchain adoption"}
            ]
        },
        {
            "id": 3,
            "title": "Bitcoin Bull Run Hinges On Trump's Pick For Fed Chair: Analyst",
            "publisher": "NewsBTC",
            "published_on": "2025-08-19T19:00:15.000Z",
            "body": "A prominent crypto analyst suggests that Bitcoin's next major bull run could be significantly influenced by former President Trump's potential Federal Reserve Chair appointment, should he return to office. The analysis points to the critical role monetary policy plays in Bitcoin's price dynamics, with dovish Fed policies historically correlating with crypto market rallies. The analyst notes that Trump's previous Fed appointments favored more accommodative monetary policies, which could create favorable conditions for risk assets including Bitcoin. This political-monetary nexus represents a new dimension in crypto market analysis, where traditional political cycles increasingly intersect with digital asset valuations. The timing of potential policy shifts could coincide with Bitcoin's halving cycle effects, creating a potential perfect storm for price appreciation.",
            "signal_strength": 0.72,
            "uniqueness_score": 0.81,
            "analysis_confidence": 0.75,
            "weak_signals": [
                {"signal": "Political-Crypto Convergence", "description": "Political appointments directly impacting crypto markets"},
                {"signal": "Monetary Policy Anticipation", "description": "Markets pricing in future Fed policy changes"},
                {"signal": "Cycle Convergence", "description": "Political and Bitcoin halving cycles aligning"}
            ],
            "pattern_anomalies": [
                {"pattern": "Forward Political Pricing", "description": "Markets reacting to potential future appointments"},
                {"pattern": "Cross-Asset Policy Correlation", "description": "Crypto following traditional monetary policy patterns"}
            ],
            "adjacent_connections": [
                {"connection": "Political Science", "description": "Electoral cycles affecting financial markets"},
                {"connection": "Monetary Economics", "description": "Fed policy transmission to digital assets"}
            ]
        }
    ]


async def test_story_selection():
    """Test the story selection agent."""
    logger.info("Testing story selection agent...")
    
    sample_articles = create_sample_articles()
    formatted_input = newsletter_orchestrator.format_articles_for_selection(sample_articles)
    
    try:
        result = await newsletter_orchestrator.story_agent.run(formatted_input)
        logger.info(f"Story selection completed: {len(result.data.selected_stories)} stories selected")
        
        for story in result.data.selected_stories:
            logger.info(f"Selected: {story.title} (signal: {story.signal_strength:.2f})")
        
        return result.data
    except Exception as e:
        logger.error(f"Story selection failed: {e}")
        return None


async def test_synthesis(selection_result):
    """Test the synthesis agent."""
    logger.info("Testing synthesis agent...")
    
    if not selection_result:
        logger.error("No selection result to synthesize")
        return None
    
    sample_articles = create_sample_articles()
    formatted_input = newsletter_orchestrator.format_selection_for_synthesis(
        selection_result, sample_articles
    )
    
    try:
        result = await newsletter_orchestrator.synthesis_agent.run(formatted_input)
        logger.info(f"Synthesis completed: {len(result.data.primary_themes)} themes identified")
        
        for theme in result.data.primary_themes:
            logger.info(f"Theme: {theme}")
        
        return result.data
    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        return None


async def test_newsletter_writing(synthesis_result, selection_result):
    """Test the newsletter writer agent."""
    logger.info("Testing newsletter writer agent...")
    
    if not synthesis_result or not selection_result:
        logger.error("Missing synthesis or selection results")
        return None
    
    formatted_input = newsletter_orchestrator.format_synthesis_for_writing(
        synthesis_result, selection_result
    )
    
    try:
        result = await newsletter_orchestrator.writer_agent.run(formatted_input)
        logger.info(f"Newsletter writing completed: {result.data.title}")
        logger.info(f"Quality score: {result.data.editorial_quality_score:.2f}")
        logger.info(f"Read time: {result.data.estimated_read_time} minutes")
        
        return result.data
    except Exception as e:
        logger.error(f"Newsletter writing failed: {e}")
        return None


async def test_full_workflow():
    """Test the complete newsletter generation workflow."""
    logger.info("Testing complete newsletter generation workflow...")
    
    sample_articles = create_sample_articles()
    
    try:
        result = await newsletter_orchestrator.generate_daily_newsletter(sample_articles)
        
        if result["success"]:
            logger.info("✅ Newsletter generation successful!")
            logger.info(f"Title: {result['newsletter_content'].title}")
            logger.info(f"Quality: {result['newsletter_content'].editorial_quality_score:.2f}")
            logger.info(f"Stories selected: {result['generation_metadata']['stories_selected']}")
            logger.info(f"Generation cost: ${result['generation_metadata']['generation_cost']:.4f}")
            
            # Print executive summary
            logger.info("\nExecutive Summary:")
            for i, summary in enumerate(result['newsletter_content'].executive_summary, 1):
                logger.info(f"{i}. {summary}")
                
        else:
            logger.error(f"❌ Newsletter generation failed: {result['error']}")
            
        return result
        
    except Exception as e:
        logger.error(f"Full workflow test failed: {e}")
        return None


async def main():
    """Main test execution."""
    logger.info("🧪 Starting Newsletter Agents Test Suite")
    logger.info("=" * 60)
    
    try:
        # Test individual agents
        logger.info("\n1. Testing Story Selection Agent...")
        selection_result = await test_story_selection()
        
        if selection_result:
            logger.info("\n2. Testing Synthesis Agent...")
            synthesis_result = await test_synthesis(selection_result)
            
            if synthesis_result:
                logger.info("\n3. Testing Newsletter Writer Agent...")
                newsletter_result = await test_newsletter_writing(synthesis_result, selection_result)
                
                if newsletter_result:
                    logger.info("\n4. Testing Full Workflow...")
                    workflow_result = await test_full_workflow()
                    
                    if workflow_result and workflow_result["success"]:
                        logger.info("\n✅ All tests passed! Newsletter generation system is working.")
                        return True
        
        logger.error("\n❌ Some tests failed. Check logs for details.")
        return False
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
