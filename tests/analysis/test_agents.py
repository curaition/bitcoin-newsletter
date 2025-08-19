"""Tests for PydanticAI analysis agents."""

from unittest.mock import AsyncMock

import pytest
from crypto_newsletter.analysis.agents.content_analysis import content_analysis_agent
from crypto_newsletter.analysis.agents.signal_validation import signal_validation_agent
from crypto_newsletter.analysis.dependencies import AnalysisDependencies, CostTracker
from crypto_newsletter.analysis.models.analysis import ContentAnalysis
from crypto_newsletter.analysis.models.signals import WeakSignal
from pydantic_ai.models.test import TestModel


class TestContentAnalysisAgent:
    """Test the content analysis agent."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for testing."""
        return AnalysisDependencies(
            db_session=AsyncMock(),
            cost_tracker=CostTracker(daily_budget=10.0),
            current_publisher="CoinDesk",
            current_article_id=123,
        )

    def test_agent_initialization(self):
        """Test that the agent initializes correctly."""
        assert content_analysis_agent is not None
        assert content_analysis_agent.result_type == ContentAnalysis

    @pytest.mark.asyncio
    async def test_content_analysis_with_test_model(self, mock_dependencies):
        """Test content analysis with TestModel."""

        # Use TestModel for testing
        test_model = TestModel()

        # Sample article content
        article_content = """
        TITLE: Bitcoin ETF Sees Record Inflows

        PUBLISHER: CoinDesk

        CONTENT: Bitcoin exchange-traded funds saw record inflows of $1.2 billion
        last week, marking the highest weekly inflow since launch. The surge comes
        as institutional investors increasingly view Bitcoin as a hedge against
        inflation. Several pension funds have reportedly allocated portions of
        their portfolios to Bitcoin ETFs, signaling a shift in institutional
        sentiment. Market analysts note this could indicate broader acceptance
        of cryptocurrency in traditional finance portfolios.
        """

        # Override the agent's model for testing
        with content_analysis_agent.override(model=test_model):
            result = await content_analysis_agent.run(
                article_content, deps=mock_dependencies
            )

            # Verify we get a result
            assert result is not None
            assert hasattr(result, "output")

            # The TestModel returns structured data based on the result_type
            analysis = result.output
            assert isinstance(analysis, ContentAnalysis)

            # Verify required fields are present
            assert hasattr(analysis, "sentiment")
            assert hasattr(analysis, "weak_signals")
            assert hasattr(analysis, "analysis_confidence")

    def test_prompt_quality(self):
        """Test that the system prompt contains key elements."""
        # Get the system prompt (it's a string in this simple implementation)
        system_prompt = content_analysis_agent.system_prompt

        # Verify key elements are present
        assert "cryptocurrency market analyst" in system_prompt.lower()
        assert "weak signals" in system_prompt.lower()
        assert "pattern anomalies" in system_prompt.lower()
        assert "confidence scores" in system_prompt.lower()
        assert "evidence" in system_prompt.lower()


class TestSignalValidationAgent:
    """Test the signal validation agent."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for testing."""
        return AnalysisDependencies(
            db_session=AsyncMock(),
            cost_tracker=CostTracker(daily_budget=10.0),
            max_searches_per_validation=3,
        )

    @pytest.fixture
    def sample_signals(self):
        """Create sample signals for testing."""
        return [
            WeakSignal(
                signal_type="institutional_behavior",
                description="Pension funds allocating to Bitcoin ETFs",
                confidence=0.8,
                implications="Increased institutional adoption could drive price stability",
                evidence=["Several pension funds have reportedly allocated portions"],
                timeframe="medium-term",
            )
        ]

    def test_agent_initialization(self):
        """Test that the validation agent initializes correctly."""
        assert signal_validation_agent is not None

    def test_prompt_quality(self):
        """Test that the validation prompt contains key elements."""
        system_prompt = signal_validation_agent.system_prompt

        # Verify key elements are present
        assert "research specialist" in system_prompt.lower()
        assert "external research" in system_prompt.lower()
        assert "authoritative sources" in system_prompt.lower()
        assert "validated" in system_prompt.lower()
        assert "contradicted" in system_prompt.lower()


class TestAgentIntegration:
    """Test agent integration and workflow."""

    @pytest.mark.asyncio
    async def test_agent_workflow_simulation(self):
        """Test a simulated workflow between agents."""

        # This test simulates the workflow without external dependencies
        mock_deps = AnalysisDependencies(
            db_session=AsyncMock(), cost_tracker=CostTracker(daily_budget=10.0)
        )

        # Test that we can create the workflow structure
        assert content_analysis_agent is not None
        assert signal_validation_agent is not None

        # Verify the agents have the expected configuration
        assert content_analysis_agent.result_type == ContentAnalysis
        assert content_analysis_agent.deps_type == AnalysisDependencies
