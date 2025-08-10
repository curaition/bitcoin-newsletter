"""CoinDesk API client for fetching cryptocurrency articles."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from crypto_newsletter.shared.config.settings import get_settings


class CoinDeskAPIClient:
    """Client for interacting with the CoinDesk API."""

    def __init__(self, settings: Optional[Any] = None) -> None:
        """Initialize the CoinDesk API client."""
        self.settings = settings or get_settings()
        self.base_url = self.settings.coindesk_base_url
        self.api_key = self.settings.coindesk_api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "CoinDeskAPIClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get HTTP client, creating if necessary."""
        if self._client is None:
            raise RuntimeError("Client not initialized. Use async context manager.")
        return self._client

    async def get_latest_articles(
        self,
        limit: int = 50,
        language: str = "EN",
        categories: Optional[List[str]] = None,
        source_ids: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Fetch latest articles from CoinDesk API.

        Args:
            limit: Maximum number of articles to fetch (default: 50)
            language: Language code (default: "EN")
            categories: List of categories to filter by (default: ["BTC"])
            source_ids: Comma-separated source IDs to filter by

        Returns:
            Dict containing the API response with articles data

        Raises:
            httpx.HTTPStatusError: If API request fails
            httpx.TimeoutException: If request times out
        """
        if categories is None:
            categories = ["BTC"]

        # Default source IDs from PRD if not provided
        if source_ids is None:
            source_ids = (
                "coindesk,cointelegraph,bitcoinmagazine,coingape,blockworks,"
                "dailyhodl,cryptoslate,cryptopotato,decrypt,theblock,"
                "cryptobriefing,bitcoin.com,newsbtc"
            )

        params = {
            "lang": language,
            "limit": limit,
            "categories": ",".join(categories),
            "source_ids": source_ids,
            "api_key": self.api_key,
        }

        logger.debug(
            f"Fetching articles from CoinDesk API with params: {params}"
        )

        try:
            response = await self.client.get(
                f"{self.base_url}/news/v1/article/list",
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            logger.info(
                f"Successfully fetched {len(data.get('Data', []))} articles "
                f"from CoinDesk API"
            )

            return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"CoinDesk API request failed with status {e.response.status_code}: "
                f"{e.response.text}"
            )
            raise
        except httpx.TimeoutException as e:
            logger.error(f"CoinDesk API request timed out: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching articles: {e}")
            raise

    def filter_recent_articles(
        self,
        api_response: Dict[str, Any],
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Filter articles to only include those from the last N hours.

        Args:
            api_response: Response from CoinDesk API
            hours: Number of hours to look back (default: 24)

        Returns:
            List of articles published within the specified time window
        """
        cutoff_timestamp = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        recent_articles = []

        articles = api_response.get("Data", [])
        logger.debug(
            f"Filtering {len(articles)} articles for last {hours} hours "
            f"(cutoff: {cutoff_timestamp})"
        )

        for article in articles:
            published_on = article.get("PUBLISHED_ON", 0)
            if published_on > cutoff_timestamp:
                recent_articles.append(article)

        logger.info(
            f"Found {len(recent_articles)} articles published in the last "
            f"{hours} hours"
        )

        return recent_articles

    async def test_connection(self) -> bool:
        """
        Test the connection to CoinDesk API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Make a minimal request to test the connection
            async with self:
                response = await self.get_latest_articles(limit=1)
                return "Data" in response
        except Exception as e:
            logger.error(f"CoinDesk API connection test failed: {e}")
            return False

    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get rate limit information from API response headers.

        Returns:
            Dict with rate limit information if available
        """
        try:
            async with self:
                response = await self.client.get(
                    f"{self.base_url}/news/v1/article/list",
                    params={"limit": 1, "api_key": self.api_key},
                )
                response.raise_for_status()

                # Extract rate limit headers if present
                headers = response.headers
                rate_limit_info = {}

                for header_name in ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]:
                    if header_name in headers:
                        rate_limit_info[header_name.lower().replace("-", "_")] = headers[header_name]

                return rate_limit_info

        except Exception as e:
            logger.error(f"Failed to get rate limit info: {e}")
            return {}


# Convenience function for one-off requests
async def fetch_coindesk_articles(
    limit: int = 50,
    hours: int = 24,
    categories: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch and filter CoinDesk articles.

    Args:
        limit: Maximum number of articles to fetch
        hours: Filter articles from last N hours
        categories: Categories to filter by

    Returns:
        List of recent articles
    """
    async with CoinDeskAPIClient() as client:
        response = await client.get_latest_articles(
            limit=limit,
            categories=categories,
        )
        return client.filter_recent_articles(response, hours=hours)
