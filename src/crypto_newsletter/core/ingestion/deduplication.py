"""Deduplication utilities for article processing."""

import hashlib
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from loguru import logger


class ArticleDeduplicator:
    """Handles article deduplication logic."""

    def __init__(self) -> None:
        """Initialize the deduplicator."""
        self._seen_urls: Set[str] = set()
        self._seen_guids: Set[str] = set()
        self._seen_ids: Set[int] = set()
        self._seen_content_hashes: Set[str] = set()

    def is_duplicate(self, article_data: Dict[str, Any]) -> bool:
        """
        Check if an article is a duplicate based on multiple criteria.

        Args:
            article_data: Article data from CoinDesk API

        Returns:
            True if article is a duplicate, False otherwise
        """
        # Check by external ID
        external_id = article_data.get("ID")
        if external_id and external_id in self._seen_ids:
            logger.debug(f"Duplicate found by ID: {external_id}")
            return True

        # Check by GUID
        guid = article_data.get("GUID")
        if guid and guid in self._seen_guids:
            logger.debug(f"Duplicate found by GUID: {guid}")
            return True

        # Check by URL
        url = article_data.get("URL")
        if url:
            normalized_url = self._normalize_url(url)
            if normalized_url in self._seen_urls:
                logger.debug(f"Duplicate found by URL: {normalized_url}")
                return True

        # Check by content hash (title + body)
        content_hash = self._generate_content_hash(article_data)
        if content_hash and content_hash in self._seen_content_hashes:
            logger.debug(f"Duplicate found by content hash: {content_hash}")
            return True

        return False

    def mark_as_seen(self, article_data: Dict[str, Any]) -> None:
        """
        Mark an article as seen to prevent future duplicates.

        Args:
            article_data: Article data from CoinDesk API
        """
        # Mark ID as seen
        external_id = article_data.get("ID")
        if external_id:
            self._seen_ids.add(external_id)

        # Mark GUID as seen
        guid = article_data.get("GUID")
        if guid:
            self._seen_guids.add(guid)

        # Mark URL as seen
        url = article_data.get("URL")
        if url:
            normalized_url = self._normalize_url(url)
            self._seen_urls.add(normalized_url)

        # Mark content hash as seen
        content_hash = self._generate_content_hash(article_data)
        if content_hash:
            self._seen_content_hashes.add(content_hash)

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL for comparison.

        Args:
            url: Raw URL string

        Returns:
            Normalized URL string
        """
        try:
            parsed = urlparse(url.lower().strip())
            # Remove common tracking parameters
            query_params = []
            if parsed.query:
                params = parsed.query.split("&")
                for param in params:
                    if not any(
                        param.startswith(tracking)
                        for tracking in ["utm_", "ref=", "source=", "campaign="]
                    ):
                        query_params.append(param)

            query = "&".join(query_params) if query_params else ""
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if query:
                normalized += f"?{query}"

            return normalized

        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {e}")
            return url.lower().strip()

    def _generate_content_hash(self, article_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate a hash of article content for duplicate detection.

        Args:
            article_data: Article data from CoinDesk API

        Returns:
            SHA-256 hash of content or None if insufficient data
        """
        title = article_data.get("TITLE", "").strip()
        body = article_data.get("BODY", "").strip()

        if not title and not body:
            return None

        # Combine title and first 500 chars of body for hashing
        content = f"{title}|{body[:500]}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get_stats(self) -> Dict[str, int]:
        """
        Get deduplication statistics.

        Returns:
            Dictionary with counts of seen items
        """
        return {
            "seen_ids": len(self._seen_ids),
            "seen_guids": len(self._seen_guids),
            "seen_urls": len(self._seen_urls),
            "seen_content_hashes": len(self._seen_content_hashes),
        }

    def reset(self) -> None:
        """Reset all seen items."""
        self._seen_urls.clear()
        self._seen_guids.clear()
        self._seen_ids.clear()
        self._seen_content_hashes.clear()


def deduplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate articles from a list.

    Args:
        articles: List of article data from CoinDesk API

    Returns:
        List of unique articles
    """
    deduplicator = ArticleDeduplicator()
    unique_articles = []

    logger.info(f"Deduplicating {len(articles)} articles")

    for article in articles:
        if not deduplicator.is_duplicate(article):
            unique_articles.append(article)
            deduplicator.mark_as_seen(article)
        else:
            logger.debug(f"Skipping duplicate article: {article.get('TITLE', 'Unknown')}")

    stats = deduplicator.get_stats()
    logger.info(
        f"Deduplication complete: {len(unique_articles)} unique articles "
        f"from {len(articles)} total. Stats: {stats}"
    )

    return unique_articles


def find_similar_articles(
    articles: List[Dict[str, Any]], similarity_threshold: float = 0.8
) -> List[List[Dict[str, Any]]]:
    """
    Find groups of similar articles based on content.

    Args:
        articles: List of article data
        similarity_threshold: Minimum similarity score (0.0 to 1.0)

    Returns:
        List of groups, where each group contains similar articles
    """
    # This is a placeholder for more sophisticated similarity detection
    # Could be enhanced with NLP techniques like TF-IDF or embeddings
    similar_groups = []

    # Simple implementation based on title similarity
    processed = set()

    for i, article1 in enumerate(articles):
        if i in processed:
            continue

        group = [article1]
        title1 = article1.get("TITLE", "").lower()

        for j, article2 in enumerate(articles[i + 1 :], i + 1):
            if j in processed:
                continue

            title2 = article2.get("TITLE", "").lower()

            # Simple word overlap similarity
            words1 = set(title1.split())
            words2 = set(title2.split())

            if words1 and words2:
                similarity = len(words1 & words2) / len(words1 | words2)
                if similarity >= similarity_threshold:
                    group.append(article2)
                    processed.add(j)

        if len(group) > 1:
            similar_groups.append(group)

        processed.add(i)

    logger.info(f"Found {len(similar_groups)} groups of similar articles")
    return similar_groups
