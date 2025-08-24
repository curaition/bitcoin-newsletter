"""Enhanced newsletter orchestrator with progress tracking and quality validation."""

from datetime import datetime, timedelta
from typing import Any, Optional

from crypto_newsletter.newsletter.agents.orchestrator import NewsletterOrchestrator
from crypto_newsletter.newsletter.models.progress import (
    SelectionQuality,
    SynthesisQuality,
    WritingQuality,
)
from crypto_newsletter.newsletter.services.progress_tracker import ProgressTracker
from crypto_newsletter.newsletter.utils.citation_validator import citation_validator
from loguru import logger


class ProgressAwareNewsletterOrchestrator(NewsletterOrchestrator):
    """Enhanced newsletter orchestrator with progress tracking and quality gates."""

    def __init__(self):
        super().__init__()
        self.current_task_id: Optional[str] = None

    def set_task_id(self, task_id: str) -> None:
        """Set the current task ID for progress tracking."""
        self.current_task_id = task_id

    async def generate_daily_newsletter_with_progress(
        self, articles: list[dict[str, Any]], newsletter_type: str = "DAILY"
    ) -> dict[str, Any]:
        """Enhanced newsletter generation with progress tracking and quality gates."""

        if not self.current_task_id:
            raise ValueError("Task ID must be set before generating newsletter")

        task_id = self.current_task_id
        start_time = datetime.utcnow()
        estimated_completion = start_time + timedelta(minutes=5)  # Estimate 5 minutes

        async with ProgressTracker() as progress_tracker:
            try:
                # Initialize progress tracking
                await progress_tracker.initialize_progress(
                    task_id=task_id,
                    articles_count=len(articles),
                    estimated_completion=estimated_completion,
                )

                # STEP 1: Story Selection (0-33%)
                await progress_tracker.update_progress(
                    task_id,
                    "selection",
                    0.0,
                    {
                        "status": "Starting story selection",
                        "articles_count": len(articles),
                        "step_description": "Analyzing articles and selecting the most revealing stories",
                    },
                )

                # Use enhanced formatting with URLs
                selection_input = self.format_articles_for_selection(articles)
                selection_result = await self.story_agent.run(selection_input)

                # Validate selection quality
                selection_quality = await self.validate_story_selection(
                    selection_result.output, articles
                )

                await progress_tracker.update_progress(
                    task_id,
                    "selection",
                    1.0,
                    {
                        "status": "Story selection complete",
                        "selected_count": len(selection_result.output.selected_stories),
                        "quality_score": selection_quality.overall_score,
                        "citations_available": selection_quality.urls_available,
                        "step_description": f"Selected {len(selection_result.output.selected_stories)} high-quality stories",
                    },
                    intermediate_result={
                        "selected_stories": [
                            {
                                "title": story.title,
                                "publisher": story.publisher,
                                "signal_strength": story.signal_strength,
                                "reasoning": story.selection_reasoning[:100] + "...",
                            }
                            for story in selection_result.output.selected_stories
                        ]
                    },
                )

                # STEP 2: Synthesis (33-66%)
                await progress_tracker.update_progress(
                    task_id,
                    "synthesis",
                    0.0,
                    {
                        "status": "Analyzing patterns and connections",
                        "step_description": "Identifying themes and connections across selected stories",
                    },
                )

                synthesis_input = self.format_selection_for_synthesis(
                    selection_result.output, articles
                )
                synthesis_result = await self.synthesis_agent.run(synthesis_input)

                synthesis_quality = await self.validate_synthesis(
                    synthesis_result.output
                )

                await progress_tracker.update_progress(
                    task_id,
                    "synthesis",
                    1.0,
                    {
                        "status": "Pattern synthesis complete",
                        "themes_identified": len(
                            synthesis_result.output.primary_themes
                        ),
                        "quality_score": synthesis_quality.overall_score,
                        "unique_insights": synthesis_quality.uniqueness_score,
                        "step_description": f"Identified {len(synthesis_result.output.primary_themes)} key themes",
                    },
                    intermediate_result={
                        "primary_themes": synthesis_result.output.primary_themes,
                        "market_narrative_preview": synthesis_result.output.market_narrative[
                            :200
                        ]
                        + "...",
                    },
                )

                # STEP 3: Newsletter Writing (66-90%)
                await progress_tracker.update_progress(
                    task_id,
                    "writing",
                    0.0,
                    {
                        "status": "Generating newsletter content",
                        "step_description": "Creating compelling newsletter with citations and insights",
                    },
                )

                writing_input = self.format_synthesis_for_writing(
                    synthesis_result.output, selection_result.output
                )
                newsletter_result = await self.writer_agent.run(writing_input)

                writing_quality = await self.validate_newsletter_content(
                    newsletter_result.output, articles
                )

                await progress_tracker.update_progress(
                    task_id,
                    "writing",
                    1.0,
                    {
                        "status": "Newsletter content complete",
                        "word_count": writing_quality.word_count,
                        "citation_count": writing_quality.citation_count,
                        "quality_score": writing_quality.overall_score,
                        "step_description": f"Generated {writing_quality.word_count} words with {writing_quality.citation_count} citations",
                    },
                    intermediate_result={
                        "title": newsletter_result.output.title,
                        "executive_summary": newsletter_result.output.executive_summary,
                        "citation_count": len(
                            newsletter_result.output.source_citations
                        ),
                    },
                )

                # STEP 4: Storage & Finalization (90-100%)
                await progress_tracker.update_progress(
                    task_id,
                    "storage",
                    0.5,
                    {
                        "status": "Storing newsletter",
                        "step_description": "Saving newsletter to database",
                    },
                )

                # Store newsletter (using existing storage logic)
                from crypto_newsletter.newsletter.storage import NewsletterStorage
                from crypto_newsletter.shared.database.connection import get_db_session

                async with get_db_session() as db:
                    storage = NewsletterStorage(db)
                    newsletter = await storage.create_newsletter(
                        newsletter_content=newsletter_result.output,
                        story_selection=selection_result.output,
                        synthesis=synthesis_result.output,
                        generation_metadata={
                            "articles_reviewed": len(articles),
                            "stories_selected": len(
                                selection_result.output.selected_stories
                            ),
                            "generation_cost": self.calculate_generation_cost(
                                [
                                    selection_result.usage(),
                                    synthesis_result.usage(),
                                    newsletter_result.usage(),
                                ]
                            ),
                            "quality_score": newsletter_result.output.editorial_quality_score,
                            "content_quality": await self._validate_content_quality(
                                newsletter_result.output
                            ),
                        },
                    )

                await progress_tracker.complete_generation(
                    task_id,
                    newsletter.id,
                    {
                        "status": "Newsletter generation complete",
                        "newsletter_id": newsletter.id,
                        "final_quality_score": newsletter.quality_score,
                        "step_description": f"Newsletter #{newsletter.id} ready for review",
                    },
                )

                return {
                    "success": True,
                    "newsletter_id": newsletter.id,
                    "newsletter_content": newsletter_result.output.model_dump(
                        mode="json"
                    ),
                    "quality_metrics": {
                        "selection_quality": selection_quality.model_dump(mode="json"),
                        "synthesis_quality": synthesis_quality.model_dump(mode="json"),
                        "writing_quality": writing_quality.model_dump(mode="json"),
                    },
                    "generation_time": (datetime.utcnow() - start_time).total_seconds(),
                }

            except Exception as e:
                await progress_tracker.mark_failed(
                    task_id,
                    str(e),
                    {
                        "error_step": "unknown",  # Could be enhanced to track current step
                        "error_details": str(e),
                    },
                )
                logger.error(f"Newsletter generation failed: {e}")
                raise

    async def validate_story_selection(self, selection, articles) -> SelectionQuality:
        """Validate story selection quality."""
        urls_available = sum(
            1
            for story in selection.selected_stories
            if any(a.get("url") for a in articles if a["id"] == story.article_id)
        )

        signal_utilization = (
            sum(story.signal_strength for story in selection.selected_stories)
            / len(selection.selected_stories)
            if selection.selected_stories
            else 0
        )

        return SelectionQuality(
            overall_score=min(1.0, len(selection.selected_stories) / 5.0),
            urls_available=urls_available,
            signal_utilization=signal_utilization,
            unique_insights=len(selection.selection_themes),
            coverage_breadth=min(1.0, len(selection.coverage_gaps) / 3.0),
        )

    async def validate_synthesis(self, synthesis) -> SynthesisQuality:
        """Validate synthesis quality."""
        return SynthesisQuality(
            overall_score=synthesis.synthesis_confidence,
            uniqueness_score=min(1.0, len(synthesis.primary_themes) / 4.0),
            pattern_strength=min(1.0, len(synthesis.pattern_insights) / 3.0),
            connection_count=len(synthesis.cross_story_connections),
            theme_coherence=synthesis.synthesis_confidence,
        )

    async def validate_newsletter_content(self, content, articles) -> WritingQuality:
        """Validate newsletter content quality."""
        word_count = len(content.main_analysis.split())
        citation_count = len(content.source_citations)

        return WritingQuality(
            word_count=word_count,
            citation_count=citation_count,
            overall_score=content.editorial_quality_score,
            has_proper_citations=citation_count >= 5,
            readability_score=min(1.0, word_count / 1000.0),  # Simple heuristic
            actionability_score=min(1.0, len(content.action_items) / 4.0),
        )

    async def _validate_content_quality(self, content: Any) -> dict:
        """
        Validate newsletter content quality using citation validator.

        Args:
            content: NewsletterContent object to validate

        Returns:
            Dictionary with quality metrics and validation results
        """
        try:
            # Convert content to string for validation
            full_content = f"{content.title}\n\n{content.main_analysis}\n\n{content.pattern_spotlight}\n\n{content.adjacent_watch}\n\n{content.signal_radar}"

            # Get citation metrics
            citation_metrics = citation_validator.validate_citations(full_content)

            # Validate content sections length
            content_sections = {
                "main_analysis": content.main_analysis,
                "pattern_spotlight": content.pattern_spotlight,
                "adjacent_watch": content.adjacent_watch,
                "signal_radar": content.signal_radar,
            }
            length_metrics = citation_validator.validate_content_length(
                content_sections
            )

            # Generate quality report
            quality_report = citation_validator.generate_quality_report(
                full_content, content_sections
            )

            # Validate source URLs (async)
            if citation_metrics.get("urls_for_validation"):
                url_validation = await citation_validator.validate_source_urls(
                    citation_metrics["urls_for_validation"]
                )
                quality_report["url_validation"] = url_validation
                quality_report["accessible_urls"] = sum(url_validation.values())
                quality_report["total_urls"] = len(url_validation)

            logger.info(
                f"Content quality validation complete: {quality_report['overall_quality_score']:.2f}"
            )

            return quality_report

        except Exception as e:
            logger.error(f"Content quality validation failed: {e}")
            return {
                "error": str(e),
                "overall_quality_score": 0.0,
                "citation_metrics": {"total_citations": 0},
                "recommendations": ["Content quality validation failed"],
            }
