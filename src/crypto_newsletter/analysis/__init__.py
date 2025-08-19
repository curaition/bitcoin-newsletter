"""
Bitcoin Newsletter Signal Analysis Module

PydanticAI-powered multi-agent system for detecting weak signals,
pattern anomalies, and adjacent possibilities in cryptocurrency news.
"""

from .agents.content_analysis import content_analysis_agent
from .agents.orchestrator import orchestrator
from .agents.signal_validation import signal_validation_agent
from .dependencies import AnalysisDependencies, CostTracker
from .models.analysis import ContentAnalysis
from .models.signals import AdjacentConnection, PatternAnomaly, WeakSignal
from .models.validation import SignalValidation, ValidationResult
from .tasks import analyze_article_task

__all__ = [
    "content_analysis_agent",
    "signal_validation_agent",
    "orchestrator",
    "ContentAnalysis",
    "WeakSignal",
    "PatternAnomaly",
    "AdjacentConnection",
    "SignalValidation",
    "ValidationResult",
    "AnalysisDependencies",
    "CostTracker",
    "analyze_article_task",
]
