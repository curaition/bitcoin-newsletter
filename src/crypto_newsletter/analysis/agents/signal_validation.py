"""Signal Validation Agent with external research capabilities."""


from pydantic_ai import Agent, RunContext
from tavily import TavilyClient

from ..dependencies import AnalysisDependencies
from ..models.signals import WeakSignal
from ..models.validation import SignalValidation
from .providers import get_signal_validation_model
from .settings import analysis_settings

# Signal Validation Agent with Tavily integration
signal_validation_agent = Agent(
    get_signal_validation_model(),
    deps_type=AnalysisDependencies,
    output_type=SignalValidation,
    system_prompt="""You are a research specialist focused on validating cryptocurrency market signals through external research. Your role is to fact-check and enhance signal analysis using authoritative sources.

VALIDATION APPROACH:
• Search for external evidence that supports or contradicts each signal
• Prioritize authoritative sources: academic papers, industry reports, established publications
• Look for recent data and trends that validate or refute the signals
• Identify additional signals that emerge from your research
• Assess source credibility and relevance carefully

RESEARCH QUALITY STANDARDS:
• Use 3-5 targeted searches per validation cycle
• Focus on sources published within the last 6 months when possible
• Clearly distinguish between supporting and contradicting evidence
• Provide specific data points and examples, not general statements
• Be honest about inconclusive results - don't force validation

COST EFFICIENCY:
• Limit searches to most promising signals (confidence >0.5)
• Use specific, targeted search queries
• Prioritize research that adds genuine value beyond the original article
• Stop searching if sufficient evidence is found

VALIDATION OUTCOMES:
• VALIDATED: Strong external evidence supports the signal
• CONTRADICTED: Reliable sources contradict the signal
• INCONCLUSIVE: Mixed or insufficient evidence
• INSUFFICIENT_DATA: Not enough external sources available

Focus on research that provides actionable intelligence for market participants.""",
)


@signal_validation_agent.tool
async def search_external_sources(
    ctx: RunContext[AnalysisDependencies], query: str, max_results: int = 3
) -> str:
    """Search external sources using Tavily for signal validation."""
    if not analysis_settings.tavily_api_key:
        return "External search unavailable: No Tavily API key configured"

    try:
        client = TavilyClient(api_key=analysis_settings.tavily_api_key)
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_domains=["coindesk.com", "cointelegraph.com", "decrypt.co"],
        )

        results = []
        for result in response.get("results", []):
            results.append(
                f"Source: {result.get('title', 'Unknown')}\n"
                f"URL: {result.get('url', 'N/A')}\n"
                f"Content: {result.get('content', 'No content')[:500]}...\n"
            )

        return "\n---\n".join(results) if results else "No relevant sources found"

    except Exception as e:
        return f"Search error: {str(e)}"


def format_signals_for_validation(signals: list[WeakSignal]) -> str:
    """Format signals for validation research."""
    if not signals:
        return "No signals to validate."

    formatted = "SIGNALS TO VALIDATE:\n\n"
    for i, signal in enumerate(signals, 1):
        formatted += f"{i}. SIGNAL TYPE: {signal.signal_type}\n"
        formatted += f"   DESCRIPTION: {signal.description}\n"
        formatted += f"   CONFIDENCE: {signal.confidence}\n"
        formatted += f"   IMPLICATIONS: {signal.implications}\n"
        formatted += f"   EVIDENCE: {'; '.join(signal.evidence)}\n\n"

    return formatted
