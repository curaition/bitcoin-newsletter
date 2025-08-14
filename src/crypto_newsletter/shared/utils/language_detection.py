"""
Language Detection Utilities

Provides language detection and validation for article content to prevent
non-English articles from being stored in the database.
"""

import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Cyrillic character ranges
CYRILLIC_PATTERN = re.compile(r'[\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F]')

# Common non-English patterns
NON_ENGLISH_PATTERNS = {
    'cyrillic': CYRILLIC_PATTERN,
    'chinese': re.compile(r'[\u4e00-\u9fff]'),
    'japanese': re.compile(r'[\u3040-\u309f\u30a0-\u30ff]'),
    'korean': re.compile(r'[\uac00-\ud7af]'),
    'arabic': re.compile(r'[\u0600-\u06ff]'),
    'hebrew': re.compile(r'[\u0590-\u05ff]'),
    'thai': re.compile(r'[\u0e00-\u0e7f]'),
}

def detect_language_from_content(title: str, body: Optional[str] = None) -> str:
    """
    Detect language from article title and body content.
    
    Args:
        title: Article title
        body: Article body content (optional)
        
    Returns:
        Language code ('EN' for English, detected language code for others)
    """
    if not title:
        return 'EN'  # Default to English if no title
    
    # Combine title and first 500 chars of body for analysis
    content = title
    if body:
        content += " " + body[:500]
    
    # Check for non-English character patterns
    for lang_code, pattern in NON_ENGLISH_PATTERNS.items():
        if pattern.search(content):
            logger.debug(f"Detected {lang_code} characters in content")
            return lang_code.upper()[:2]  # Return 2-letter code
    
    # Default to English if no non-English patterns found
    return 'EN'

def is_english_content(title: str, body: Optional[str] = None) -> bool:
    """
    Check if article content is in English.
    
    Args:
        title: Article title
        body: Article body content (optional)
        
    Returns:
        True if content appears to be English, False otherwise
    """
    detected_lang = detect_language_from_content(title, body)
    return detected_lang == 'EN'

def validate_article_language(article_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and correct article language based on content analysis.
    
    Args:
        article_data: Article data dictionary
        
    Returns:
        Updated article data with corrected language
    """
    title = article_data.get('TITLE', '')
    body = article_data.get('BODY', '')
    api_language = article_data.get('LANG', 'EN')
    
    # Detect actual language from content
    detected_language = detect_language_from_content(title, body)
    
    # Log discrepancies
    if api_language != detected_language:
        logger.warning(
            f"Language mismatch - API: {api_language}, Detected: {detected_language} "
            f"for article: {article_data.get('ID', 'unknown')}"
        )
    
    # Update language in article data
    article_data['LANG'] = detected_language
    article_data['ORIGINAL_LANG'] = api_language  # Keep original for reference
    
    return article_data

def should_filter_article(article_data: Dict[str, Any], allowed_languages: list = None) -> bool:
    """
    Determine if article should be filtered out based on language.
    
    Args:
        article_data: Article data dictionary
        allowed_languages: List of allowed language codes (default: ['EN'])
        
    Returns:
        True if article should be filtered out, False if it should be kept
    """
    if allowed_languages is None:
        allowed_languages = ['EN']
    
    title = article_data.get('TITLE', '')
    body = article_data.get('BODY', '')
    
    # Check if content is in allowed languages
    detected_language = detect_language_from_content(title, body)
    
    should_filter = detected_language not in allowed_languages
    
    if should_filter:
        logger.info(
            f"Filtering out article {article_data.get('ID', 'unknown')} "
            f"- Language: {detected_language} not in allowed: {allowed_languages}"
        )
    
    return should_filter

def get_language_stats(articles: list) -> Dict[str, int]:
    """
    Get language statistics for a list of articles.
    
    Args:
        articles: List of article data dictionaries
        
    Returns:
        Dictionary with language codes and counts
    """
    language_counts = {}
    
    for article in articles:
        title = article.get('TITLE', '')
        body = article.get('BODY', '')
        detected_lang = detect_language_from_content(title, body)
        
        language_counts[detected_lang] = language_counts.get(detected_lang, 0) + 1
    
    return language_counts
