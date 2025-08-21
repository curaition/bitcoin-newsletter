"""Web utilities for the crypto newsletter application."""

from .newsletter_formatting import NewsletterFormatter
from .newsletter_validation import NewsletterValidator, validate_newsletter_request_data

__all__ = [
    "NewsletterValidator",
    "validate_newsletter_request_data",
    "NewsletterFormatter",
]
