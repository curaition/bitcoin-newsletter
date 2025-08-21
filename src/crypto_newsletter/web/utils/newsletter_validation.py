"""Newsletter validation utilities for API endpoints."""

import re
from typing import Any

from crypto_newsletter.shared.models import Newsletter


class NewsletterValidator:
    """Validator for newsletter content and metadata."""

    # Content validation rules
    MIN_TITLE_LENGTH = 10
    MAX_TITLE_LENGTH = 200
    MIN_CONTENT_LENGTH = 500
    MAX_CONTENT_LENGTH = 50000
    MIN_SUMMARY_LENGTH = 50
    MAX_SUMMARY_LENGTH = 1000

    # Quality thresholds
    MIN_QUALITY_SCORE = 0.0
    MAX_QUALITY_SCORE = 1.0
    RECOMMENDED_MIN_QUALITY = 0.7

    @classmethod
    def validate_newsletter_content(
        cls, newsletter: Newsletter
    ) -> tuple[bool, list[str], list[str]]:
        """
        Validate newsletter content and return validation results.

        Args:
            newsletter: Newsletter instance to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Validate title
        if not newsletter.title or not newsletter.title.strip():
            errors.append("Newsletter title is required")
        elif len(newsletter.title) < cls.MIN_TITLE_LENGTH:
            errors.append(
                f"Newsletter title too short (minimum {cls.MIN_TITLE_LENGTH} characters)"
            )
        elif len(newsletter.title) > cls.MAX_TITLE_LENGTH:
            errors.append(
                f"Newsletter title too long (maximum {cls.MAX_TITLE_LENGTH} characters)"
            )

        # Validate content
        if not newsletter.content or not newsletter.content.strip():
            errors.append("Newsletter content is required")
        elif len(newsletter.content) < cls.MIN_CONTENT_LENGTH:
            errors.append(
                f"Newsletter content too short (minimum {cls.MIN_CONTENT_LENGTH} characters)"
            )
        elif len(newsletter.content) > cls.MAX_CONTENT_LENGTH:
            errors.append(
                f"Newsletter content too long (maximum {cls.MAX_CONTENT_LENGTH} characters)"
            )

        # Validate summary
        if newsletter.summary:
            if len(newsletter.summary) < cls.MIN_SUMMARY_LENGTH:
                warnings.append(
                    f"Newsletter summary is short (recommended minimum {cls.MIN_SUMMARY_LENGTH} characters)"
                )
            elif len(newsletter.summary) > cls.MAX_SUMMARY_LENGTH:
                errors.append(
                    f"Newsletter summary too long (maximum {cls.MAX_SUMMARY_LENGTH} characters)"
                )

        # Validate quality score
        if newsletter.quality_score is not None:
            if (
                newsletter.quality_score < cls.MIN_QUALITY_SCORE
                or newsletter.quality_score > cls.MAX_QUALITY_SCORE
            ):
                errors.append(
                    f"Quality score must be between {cls.MIN_QUALITY_SCORE} and {cls.MAX_QUALITY_SCORE}"
                )
            elif newsletter.quality_score < cls.RECOMMENDED_MIN_QUALITY:
                warnings.append(
                    f"Quality score is below recommended minimum ({cls.RECOMMENDED_MIN_QUALITY})"
                )

        # Validate status
        valid_statuses = ["DRAFT", "REVIEW", "PUBLISHED", "ARCHIVED"]
        if newsletter.status not in valid_statuses:
            errors.append(
                f"Invalid status '{newsletter.status}'. Must be one of: {', '.join(valid_statuses)}"
            )

        # Validate generation date
        if not newsletter.generation_date:
            errors.append("Generation date is required")

        # Content quality checks
        content_warnings = cls._validate_content_quality(newsletter.content)
        warnings.extend(content_warnings)

        is_valid = len(errors) == 0
        return is_valid, errors, warnings

    @classmethod
    def _validate_content_quality(cls, content: str) -> list[str]:
        """Validate content quality and return warnings."""
        warnings = []

        if not content:
            return warnings

        # Check for basic formatting
        if not re.search(r"\n\n", content):
            warnings.append("Content appears to lack paragraph breaks")

        # Check for excessive repetition
        words = content.lower().split()
        if len(words) > 100:
            word_freq = {}
            for word in words:
                if len(word) > 4:  # Only check longer words
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Check for words that appear too frequently
            total_words = len(words)
            for word, count in word_freq.items():
                if count / total_words > 0.05:  # More than 5% of content
                    warnings.append(f"Word '{word}' appears frequently ({count} times)")

        # Check for placeholder text
        placeholders = ["lorem ipsum", "placeholder", "todo", "tbd", "xxx"]
        content_lower = content.lower()
        for placeholder in placeholders:
            if placeholder in content_lower:
                warnings.append(f"Content contains placeholder text: '{placeholder}'")

        return warnings

    @classmethod
    def get_content_metrics(cls, newsletter: Newsletter) -> dict[str, Any]:
        """Get content metrics for a newsletter."""
        if not newsletter.content:
            return {}

        content = newsletter.content
        words = content.split()
        sentences = re.split(r"[.!?]+", content)
        paragraphs = content.split("\n\n")

        # Calculate readability metrics
        avg_words_per_sentence = len(words) / max(len(sentences), 1)
        avg_sentences_per_paragraph = len(sentences) / max(len(paragraphs), 1)

        # Estimate reading time (average 200 words per minute)
        estimated_read_time = max(1, len(words) // 200)

        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "character_count": len(content),
            "avg_words_per_sentence": round(avg_words_per_sentence, 1),
            "avg_sentences_per_paragraph": round(avg_sentences_per_paragraph, 1),
            "estimated_read_time_minutes": estimated_read_time,
            "content_density": round(len(words) / max(len(paragraphs), 1), 1),
        }

    @classmethod
    def validate_newsletter_type(cls, newsletter_type: str) -> bool:
        """Validate newsletter type."""
        valid_types = ["DAILY", "WEEKLY"]
        return newsletter_type.upper() in valid_types

    @classmethod
    def validate_status_transition(
        cls, current_status: str, new_status: str
    ) -> tuple[bool, str]:
        """
        Validate status transition rules.

        Args:
            current_status: Current newsletter status
            new_status: Desired new status

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Define valid transitions
        valid_transitions = {
            "DRAFT": ["REVIEW", "ARCHIVED"],
            "REVIEW": ["DRAFT", "PUBLISHED", "ARCHIVED"],
            "PUBLISHED": ["ARCHIVED"],
            "ARCHIVED": ["DRAFT"],  # Allow unarchiving
        }

        if current_status not in valid_transitions:
            return False, f"Invalid current status: {current_status}"

        if new_status not in valid_transitions[current_status]:
            return False, f"Cannot transition from {current_status} to {new_status}"

        return True, ""

    @classmethod
    def validate_generation_metadata(cls, metadata: dict[str, Any]) -> list[str]:
        """Validate generation metadata and return warnings."""
        warnings = []

        if not metadata:
            warnings.append("No generation metadata available")
            return warnings

        # Check for required fields
        required_fields = ["newsletter_type", "generation_cost"]
        for field in required_fields:
            if field not in metadata:
                warnings.append(f"Missing generation metadata field: {field}")

        # Validate newsletter type
        if "newsletter_type" in metadata:
            if not cls.validate_newsletter_type(metadata["newsletter_type"]):
                warnings.append(
                    f"Invalid newsletter type in metadata: {metadata['newsletter_type']}"
                )

        # Validate generation cost
        if "generation_cost" in metadata:
            cost = metadata["generation_cost"]
            if not isinstance(cost, (int, float)) or cost < 0:
                warnings.append("Invalid generation cost in metadata")
            elif cost > 10.0:  # Arbitrary high cost threshold
                warnings.append(f"High generation cost: ${cost:.4f}")

        # Validate processing time
        if "processing_time_seconds" in metadata:
            time_seconds = metadata["processing_time_seconds"]
            if not isinstance(time_seconds, (int, float)) or time_seconds < 0:
                warnings.append("Invalid processing time in metadata")
            elif time_seconds > 3600:  # More than 1 hour
                warnings.append(f"Long processing time: {time_seconds:.1f} seconds")

        return warnings


def validate_newsletter_request_data(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate newsletter request data from API endpoints.

    Args:
        data: Request data dictionary

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Validate newsletter type if provided
    if "newsletter_type" in data:
        if not NewsletterValidator.validate_newsletter_type(data["newsletter_type"]):
            errors.append(f"Invalid newsletter type: {data['newsletter_type']}")

    # Validate status if provided
    if "status" in data:
        valid_statuses = ["DRAFT", "REVIEW", "PUBLISHED", "ARCHIVED"]
        if data["status"] not in valid_statuses:
            errors.append(f"Invalid status: {data['status']}")

    # Validate title if provided
    if "title" in data and data["title"]:
        title_len = len(data["title"])
        if title_len < NewsletterValidator.MIN_TITLE_LENGTH:
            errors.append(
                f"Title too short (minimum {NewsletterValidator.MIN_TITLE_LENGTH} characters)"
            )
        elif title_len > NewsletterValidator.MAX_TITLE_LENGTH:
            errors.append(
                f"Title too long (maximum {NewsletterValidator.MAX_TITLE_LENGTH} characters)"
            )

    # Validate content if provided
    if "content" in data and data["content"]:
        content_len = len(data["content"])
        if content_len < NewsletterValidator.MIN_CONTENT_LENGTH:
            errors.append(
                f"Content too short (minimum {NewsletterValidator.MIN_CONTENT_LENGTH} characters)"
            )
        elif content_len > NewsletterValidator.MAX_CONTENT_LENGTH:
            errors.append(
                f"Content too long (maximum {NewsletterValidator.MAX_CONTENT_LENGTH} characters)"
            )

    return len(errors) == 0, errors
