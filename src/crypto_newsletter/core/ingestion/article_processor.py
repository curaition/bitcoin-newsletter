"""Article processor for handling CoinDesk API data and database operations."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from crypto_newsletter.shared.models import Article, ArticleCategory, Category, Publisher


class ArticleProcessor:
    """Processes articles from CoinDesk API and stores them in the database."""

    def __init__(self, db_session: AsyncSession) -> None:
        """Initialize the article processor with a database session."""
        self.db = db_session

    async def process_articles(self, articles: List[Dict[str, Any]]) -> int:
        """
        Process a list of articles from CoinDesk API response.

        Args:
            articles: List of article dictionaries from CoinDesk API

        Returns:
            Number of articles successfully processed and stored

        Raises:
            Exception: If database operations fail
        """
        processed_count = 0
        skipped_count = 0

        logger.info(f"Processing {len(articles)} articles")

        for article_data in articles:
            try:
                # Check if article already exists
                if await self._article_exists(article_data):
                    skipped_count += 1
                    logger.debug(
                        f"Skipping duplicate article: {article_data.get('ID')}"
                    )
                    continue

                # Process publisher first
                publisher = await self._process_publisher(
                    article_data.get("SOURCE_DATA", {})
                )

                # Create article
                article = await self._create_article(article_data, publisher.id if publisher else None)

                # Process categories
                await self._process_categories(
                    article, article_data.get("CATEGORY_DATA", [])
                )

                processed_count += 1
                logger.debug(f"Successfully processed article: {article.external_id}")

            except Exception as e:
                logger.error(
                    f"Error processing article {article_data.get('ID')}: {e}"
                )
                # Continue processing other articles
                continue

        # Commit all changes
        try:
            await self.db.commit()
            logger.info(
                f"Successfully processed {processed_count} articles, "
                f"skipped {skipped_count} duplicates"
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to commit article processing: {e}")
            raise

        return processed_count

    async def _article_exists(self, article_data: Dict[str, Any]) -> bool:
        """
        Check if article already exists using deduplication logic.

        Uses multiple criteria for deduplication:
        - external_id (CoinDesk ID)
        - guid (CoinDesk GUID)
        - url (Article URL)

        Args:
            article_data: Article data from CoinDesk API

        Returns:
            True if article exists, False otherwise
        """
        external_id = article_data.get("ID")
        guid = article_data.get("GUID")
        url = article_data.get("URL")

        if not any([external_id, guid, url]):
            logger.warning("Article missing all deduplication identifiers")
            return False

        # Check multiple deduplication criteria
        query = select(Article).where(
            (Article.external_id == external_id) |
            (Article.guid == guid) |
            (Article.url == url)
        ).limit(1)

        result = await self.db.execute(query)
        exists = result.first() is not None

        if exists:
            logger.debug(
                f"Article exists - ID: {external_id}, GUID: {guid}, URL: {url}"
            )

        return exists

    async def _process_publisher(
        self, source_data: Dict[str, Any]
    ) -> Optional[Publisher]:
        """
        Process publisher data from CoinDesk SOURCE_DATA.

        Args:
            source_data: SOURCE_DATA from CoinDesk API

        Returns:
            Publisher instance or None if no source data
        """
        if not source_data:
            return None

        source_id = source_data.get("ID")
        if not source_id:
            return None

        # Check if publisher already exists
        query = select(Publisher).where(Publisher.source_id == source_id)
        result = await self.db.execute(query)
        publisher = result.scalar_one_or_none()

        if publisher:
            # Update existing publisher if needed
            publisher.name = source_data.get("NAME", publisher.name)
            publisher.image_url = source_data.get("IMAGE_URL")
            publisher.url = source_data.get("URL")
            publisher.last_updated_ts = int(datetime.now(timezone.utc).timestamp())
            return publisher

        # Create new publisher
        try:
            publisher = Publisher(
                source_id=source_id,
                source_key=source_data.get("KEY"),
                name=source_data.get("NAME", "Unknown"),
                image_url=source_data.get("IMAGE_URL"),
                url=source_data.get("URL"),
                language=source_data.get("LANG", "EN"),
                source_type="API",
                status="ACTIVE",
                last_updated_ts=int(datetime.now(timezone.utc).timestamp()),
            )

            self.db.add(publisher)
            await self.db.flush()  # Get the ID without committing
            logger.debug(f"Created new publisher: {publisher.name}")
            return publisher

        except IntegrityError as e:
            await self.db.rollback()
            logger.warning(f"Publisher creation failed (likely duplicate): {e}")
            # Try to fetch existing publisher
            result = await self.db.execute(query)
            return result.scalar_one_or_none()

    async def _create_article(
        self, article_data: Dict[str, Any], publisher_id: Optional[int]
    ) -> Article:
        """
        Create article from CoinDesk API data.

        Args:
            article_data: Article data from CoinDesk API
            publisher_id: ID of the associated publisher

        Returns:
            Created Article instance
        """
        # Convert timestamps
        published_on = None
        created_on = None
        updated_on = None

        if article_data.get("PUBLISHED_ON"):
            published_on = datetime.fromtimestamp(
                article_data["PUBLISHED_ON"], tz=timezone.utc
            )

        if article_data.get("CREATED_ON"):
            created_on = datetime.fromtimestamp(
                article_data["CREATED_ON"], tz=timezone.utc
            )

        if article_data.get("UPDATED_ON"):
            updated_on = datetime.fromtimestamp(
                article_data["UPDATED_ON"], tz=timezone.utc
            )

        article = Article(
            external_id=article_data.get("ID"),
            guid=article_data.get("GUID"),
            title=article_data.get("TITLE", ""),
            subtitle=article_data.get("SUBTITLE"),
            authors=article_data.get("AUTHORS"),
            url=article_data.get("URL", ""),
            body=article_data.get("BODY"),
            keywords=article_data.get("KEYWORDS"),
            language=article_data.get("LANG"),
            image_url=article_data.get("IMAGE_URL"),
            published_on=published_on,
            published_on_ns=article_data.get("PUBLISHED_ON_NS"),
            upvotes=article_data.get("UPVOTES", 0),
            downvotes=article_data.get("DOWNVOTES", 0),
            score=article_data.get("SCORE", 0),
            sentiment=article_data.get("SENTIMENT"),
            status="ACTIVE",
            created_on=created_on,
            updated_on=updated_on,
            publisher_id=publisher_id,
            source_id=article_data.get("SOURCE_ID"),
        )

        self.db.add(article)
        await self.db.flush()  # Get the ID without committing
        logger.debug(f"Created article: {article.title[:50]}...")
        return article

    async def _process_categories(
        self, article: Article, category_data: List[Dict[str, Any]]
    ) -> None:
        """
        Process categories for an article.

        Args:
            article: Article instance
            category_data: List of category data from CoinDesk API
        """
        if not category_data:
            return

        for cat_data in category_data:
            category_id = cat_data.get("ID")
            if not category_id:
                continue

            # Get or create category
            category = await self._get_or_create_category(cat_data)

            if category:
                # Create article-category relationship
                try:
                    article_category = ArticleCategory(
                        article_id=article.id,
                        category_id=category.id,
                    )
                    self.db.add(article_category)
                except IntegrityError:
                    # Relationship already exists
                    await self.db.rollback()
                    continue

    async def _get_or_create_category(
        self, category_data: Dict[str, Any]
    ) -> Optional[Category]:
        """
        Get existing category or create new one.

        Args:
            category_data: Category data from CoinDesk API

        Returns:
            Category instance or None
        """
        category_id = category_data.get("ID")
        if not category_id:
            return None

        # Check if category exists
        query = select(Category).where(Category.category_id == category_id)
        result = await self.db.execute(query)
        category = result.scalar_one_or_none()

        if category:
            return category

        # Create new category
        try:
            category = Category(
                category_id=category_id,
                name=category_data.get("NAME", "Unknown"),
                category=category_data.get("CATEGORY", "Unknown"),
            )

            self.db.add(category)
            await self.db.flush()
            logger.debug(f"Created new category: {category.name}")
            return category

        except IntegrityError:
            await self.db.rollback()
            # Try to fetch existing category
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
