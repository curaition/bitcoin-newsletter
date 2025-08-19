"""Model provider abstraction for analysis agents."""

import os
from typing import Union

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.test import TestModel

from .settings import analysis_settings


def get_content_analysis_model() -> Union[GoogleModel, TestModel]:
    """Get the model for content analysis agent."""
    if analysis_settings.testing:
        return TestModel()

    if not analysis_settings.gemini_api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is required for content analysis"
        )

    # GoogleModel now uses environment variables directly
    # Ensure GEMINI_API_KEY is set in environment
    os.environ["GEMINI_API_KEY"] = analysis_settings.gemini_api_key

    return GoogleModel(
        model_name=analysis_settings.content_analysis_model,
    )


def get_signal_validation_model() -> Union[GoogleModel, TestModel]:
    """Get the model for signal validation agent."""
    if analysis_settings.testing:
        return TestModel()

    if not analysis_settings.gemini_api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is required for signal validation"
        )

    # GoogleModel now uses environment variables directly
    # Ensure GEMINI_API_KEY is set in environment
    os.environ["GEMINI_API_KEY"] = analysis_settings.gemini_api_key

    return GoogleModel(
        model_name=analysis_settings.signal_validation_model,
    )
