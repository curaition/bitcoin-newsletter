"""Agent orchestration for multi-step analysis workflow."""

import logging
from typing import Any, Optional

from pydantic_ai.usage import Usage

from ...shared.models.models import ArticleAnalysis
from ..dependencies import AnalysisDependencies
from ..models.analysis import ContentAnalysis
from ..models.validation import SignalValidation
from .content_analysis import content_analysis_agent, format_article_for_analysis
from .signal_validation import format_signals_for_validation, signal_validation_agent

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """Orchestrates multi-agent analysis workflow."""

    def __init__(self):
        self.max_retries = 2
        self.retry_delays = [60, 300]  # 1min, 5min

    async def analyze_article(
        self,
        article_id: int,
        title: str,
        body: str,
        publisher: str,
        deps: AnalysisDependencies,
    ) -> dict[str, Any]:
        """
        Complete analysis workflow: content analysis + signal validation.

        Returns:
            Dict with analysis results, validation results, costs, and metadata
        """
        try:
            # Update dependencies with current context
            deps.current_article_id = article_id
            deps.current_publisher = publisher

            # Step 1: Content Analysis
            logger.info(f"Starting content analysis for article {article_id}")
            formatted_content = format_article_for_analysis(title, body, publisher)

            content_result = await content_analysis_agent.run(
                formatted_content, deps=deps
            )

            content_analysis: ContentAnalysis = content_result.output
            content_usage: Usage = content_result.usage()

            # Calculate cost based on token usage (Gemini 2.5 Flash pricing)
            # Approximate cost: $0.075 per 1M input tokens, $0.30 per 1M output tokens
            input_tokens = content_usage.request_tokens or 0
            output_tokens = content_usage.response_tokens or 0
            estimated_cost = (input_tokens * 0.075 / 1_000_000) + (
                output_tokens * 0.30 / 1_000_000
            )

            # Track costs
            deps.cost_tracker.add_cost(estimated_cost)

            logger.info(
                f"Content analysis complete. Found {len(content_analysis.weak_signals)} signals. "
                f"Tokens: {input_tokens + output_tokens}, Cost: ${estimated_cost:.4f}"
            )

            # Step 2: Signal Validation (if we have signals and budget)
            validation_result = None
            validation_usage = None

            if content_analysis.weak_signals and deps.cost_tracker.can_afford(
                0.10
            ):  # Reserve budget for validation
                logger.info(
                    f"Starting signal validation for {len(content_analysis.weak_signals)} signals"
                )

                # Filter signals by confidence threshold
                high_confidence_signals = [
                    signal
                    for signal in content_analysis.weak_signals
                    if signal.confidence >= deps.min_signal_confidence
                ]

                if high_confidence_signals:
                    formatted_signals = format_signals_for_validation(
                        high_confidence_signals
                    )

                    validation_result_obj = await signal_validation_agent.run(
                        formatted_signals, deps=deps
                    )

                    validation_result: SignalValidation = validation_result_obj.output
                    validation_usage: Usage = validation_result_obj.usage()

                    # Calculate validation cost based on token usage
                    val_input_tokens = validation_usage.request_tokens or 0
                    val_output_tokens = validation_usage.response_tokens or 0
                    validation_cost = (val_input_tokens * 0.075 / 1_000_000) + (
                        val_output_tokens * 0.30 / 1_000_000
                    )

                    # Track additional costs
                    deps.cost_tracker.add_cost(validation_cost)

                    logger.info(
                        f"Signal validation complete. "
                        f"Tokens: {val_input_tokens + val_output_tokens}, Cost: ${validation_cost:.4f}"
                    )
                else:
                    logger.info("No signals met confidence threshold for validation")
            else:
                logger.info("Skipping validation: no signals or insufficient budget")

            # Combine results
            total_cost = deps.cost_tracker.total_cost

            # Store results in database (only if db_session is provided)
            analysis_record_id = None
            if deps.db_session is not None:
                analysis_record_id = await self._store_analysis_results(
                    article_id=article_id,
                    content_analysis=content_analysis,
                    validation_result=validation_result,
                    total_cost=total_cost,
                    content_usage=content_usage,
                    validation_usage=validation_usage,
                    deps=deps,
                )
            else:
                logger.info("Skipping database storage - will be handled by calling task")

            return {
                "success": True,
                "article_id": article_id,
                "analysis_record_id": analysis_record_id,
                "content_analysis": content_analysis,
                "signal_validation": validation_result,
                "costs": {
                    "content_analysis": estimated_cost,
                    "signal_validation": validation_cost if validation_usage else 0.0,
                    "total": total_cost,
                },
                "usage_stats": {
                    "content_tokens": content_usage.total_tokens or 0,
                    "validation_tokens": validation_usage.total_tokens or 0
                    if validation_usage
                    else 0,
                    "total_tokens": (content_usage.total_tokens or 0)
                    + (validation_usage.total_tokens or 0 if validation_usage else 0),
                },
                "processing_metadata": {
                    "signals_found": len(content_analysis.weak_signals),
                    "signals_validated": len(validation_result.validation_results)
                    if validation_result
                    else 0,
                    "analysis_confidence": content_analysis.analysis_confidence,
                    "signal_strength": content_analysis.signal_strength,
                },
            }

        except Exception as e:
            logger.error(f"Analysis failed for article {article_id}: {str(e)}")
            return {
                "success": False,
                "article_id": article_id,
                "error": str(e),
                "requires_manual_review": True,
                "costs": {"total": deps.cost_tracker.total_cost},
            }

    async def _store_analysis_results(
        self,
        article_id: int,
        content_analysis: ContentAnalysis,
        validation_result: Optional[SignalValidation],
        total_cost: float,
        content_usage: Usage,
        validation_usage: Optional[Usage],
        deps: AnalysisDependencies,
    ) -> int:
        """Store analysis results in the database."""
        try:
            # Calculate processing time (estimate based on token usage)
            total_tokens = (content_usage.total_tokens or 0) + (
                validation_usage.total_tokens or 0 if validation_usage else 0
            )
            processing_time_ms = int(total_tokens * 0.1)  # Rough estimate

            # Create ArticleAnalysis record
            analysis_record = ArticleAnalysis(
                article_id=article_id,
                analysis_version="1.0",
                # Core analysis fields
                sentiment=content_analysis.sentiment,
                impact_score=content_analysis.impact_score,
                summary=content_analysis.summary,
                context=content_analysis.context,
                # Signal detection fields (convert to JSONB)
                weak_signals=[
                    signal.model_dump() for signal in content_analysis.weak_signals
                ],
                pattern_anomalies=[
                    anomaly.model_dump()
                    for anomaly in content_analysis.pattern_anomalies
                ],
                adjacent_connections=[
                    conn.model_dump() for conn in content_analysis.adjacent_connections
                ],
                narrative_gaps=content_analysis.narrative_gaps,
                edge_indicators=content_analysis.edge_indicators,
                # Validation fields
                verified_facts=[
                    result.model_dump()
                    for result in validation_result.validation_results
                ]
                if validation_result
                else [],
                research_sources=[],  # Could be extracted from validation results
                validation_status="COMPLETED" if validation_result else "PENDING",
                # Quality metrics
                analysis_confidence=content_analysis.analysis_confidence,
                signal_strength=content_analysis.signal_strength,
                uniqueness_score=content_analysis.uniqueness_score,
                # Processing metadata
                processing_time_ms=processing_time_ms,
                token_usage=total_tokens,
                cost_usd=total_cost,
            )

            # Store in database
            deps.db_session.add(analysis_record)
            await deps.db_session.commit()
            await deps.db_session.refresh(analysis_record)

            logger.info(
                f"Stored analysis results for article {article_id} with ID {analysis_record.id}"
            )
            return analysis_record.id

        except Exception as e:
            logger.error(
                f"Failed to store analysis results for article {article_id}: {str(e)}"
            )
            await deps.db_session.rollback()
            raise


# Global orchestrator instance
orchestrator = AnalysisOrchestrator()
