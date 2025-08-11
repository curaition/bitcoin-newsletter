"""Unit tests for the article processor."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from crypto_newsletter.core.ingestion.article_processor import ArticleProcessor
from crypto_newsletter.shared.models import Article, Publisher, Category


@pytest.mark.unit
class TestArticleProcessor:
    """Test cases for ArticleProcessor."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    def processor(self, mock_db_session):
        """Create ArticleProcessor instance."""
        return ArticleProcessor(mock_db_session)

    @pytest.mark.asyncio
    async def test_processor_initialization(self, processor, mock_db_session):
        """Test processor initialization."""
        assert processor.db == mock_db_session

    @pytest.mark.asyncio
    async def test_article_exists_by_external_id(self, processor, mock_db_session):
        """Test checking if article exists by external ID."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_db_session.execute.return_value = mock_result

        article_data = {"ID": 12345, "GUID": "test-guid", "URL": "https://test.com"}
        
        exists = await processor._article_exists(article_data)
        
        assert exists is True
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_article_does_not_exist(self, processor, mock_db_session):
        """Test checking if article does not exist."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        article_data = {"ID": 99999, "GUID": "new-guid", "URL": "https://new.com"}
        
        exists = await processor._article_exists(article_data)
        
        assert exists is False

    @pytest.mark.asyncio
    async def test_process_publisher_new(self, processor, mock_db_session):
        """Test processing a new publisher."""
        # Mock database response for checking existence
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        publisher_data = {
            "ID": 1,
            "NAME": "Test Publisher",
            "KEY": "test",
            "URL": "https://test.com",
            "LANG": "EN"
        }

        publisher = await processor._process_publisher(publisher_data)

        assert isinstance(publisher, Publisher)
        assert publisher.external_id == 1
        assert publisher.name == "Test Publisher"
        assert publisher.key == "test"
        mock_db_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_publisher_existing(self, processor, mock_db_session):
        """Test processing an existing publisher."""
        # Mock existing publisher
        existing_publisher = Publisher(
            id=1,
            external_id=1,
            name="Test Publisher",
            key="test",
            url="https://test.com",
            language="EN"
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_publisher
        mock_db_session.execute.return_value = mock_result

        publisher_data = {
            "ID": 1,
            "NAME": "Test Publisher",
            "KEY": "test",
            "URL": "https://test.com",
            "LANG": "EN"
        }

        publisher = await processor._process_publisher(publisher_data)

        assert publisher == existing_publisher
        # Should not add new publisher
        mock_db_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_article(self, processor, mock_db_session):
        """Test creating a new article."""
        article_data = {
            "ID": 12345,
            "GUID": "test-guid",
            "TITLE": "Test Article",
            "SUBTITLE": "Test Subtitle",
            "URL": "https://test.com/article",
            "BODY": "Test article body",
            "AUTHORS": "Test Author",
            "KEYWORDS": "test,article",
            "LANG": "EN",
            "IMAGE_URL": "https://test.com/image.jpg",
            "PUBLISHED_ON": 1691683200,
            "PUBLISHED_ON_NS": 1691683200000000000,
            "UPVOTES": 10,
            "DOWNVOTES": 2,
            "SCORE": 8,
            "SENTIMENT": "POSITIVE",
            "SOURCE_ID": 1
        }

        article = await processor._create_article(article_data, publisher_id=1)

        assert isinstance(article, Article)
        assert article.external_id == 12345
        assert article.guid == "test-guid"
        assert article.title == "Test Article"
        assert article.subtitle == "Test Subtitle"
        assert article.url == "https://test.com/article"
        assert article.body == "Test article body"
        assert article.authors == "Test Author"
        assert article.keywords == "test,article"
        assert article.language == "EN"
        assert article.image_url == "https://test.com/image.jpg"
        assert article.upvotes == 10
        assert article.downvotes == 2
        assert article.score == 8
        assert article.sentiment == "POSITIVE"
        assert article.publisher_id == 1
        assert article.source_id == 1
        assert article.status == "ACTIVE"

        mock_db_session.add.assert_called_once_with(article)

    @pytest.mark.asyncio
    async def test_create_article_minimal_data(self, processor, mock_db_session):
        """Test creating article with minimal required data."""
        article_data = {
            "ID": 12345,
            "GUID": "test-guid",
            "TITLE": "Test Article",
            "URL": "https://test.com/article"
        }

        article = await processor._create_article(article_data, publisher_id=None)

        assert isinstance(article, Article)
        assert article.external_id == 12345
        assert article.guid == "test-guid"
        assert article.title == "Test Article"
        assert article.url == "https://test.com/article"
        assert article.publisher_id is None
        assert article.status == "ACTIVE"

    @pytest.mark.asyncio
    async def test_process_categories(self, processor, mock_db_session):
        """Test processing article categories."""
        # Mock article
        article = Article(id=1, external_id=12345, guid="test", title="Test", url="https://test.com")
        
        # Mock category lookup
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Category doesn't exist
        mock_db_session.execute.return_value = mock_result

        category_data = [
            {
                "ID": 1,
                "NAME": "Bitcoin",
                "CATEGORY": "BTC"
            },
            {
                "ID": 2,
                "NAME": "Trading",
                "CATEGORY": "TRADING"
            }
        ]

        await processor._process_categories(article, category_data)

        # Should add 2 categories and 2 article_category relationships
        assert mock_db_session.add.call_count == 4  # 2 categories + 2 relationships

    @pytest.mark.asyncio
    async def test_process_articles_success(self, processor, mock_db_session, sample_article_data):
        """Test processing multiple articles successfully."""
        # Mock article doesn't exist
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        articles = [sample_article_data]

        with patch.object(processor, '_process_publisher', return_value=MagicMock(id=1)):
            with patch.object(processor, '_create_article', return_value=MagicMock()):
                with patch.object(processor, '_process_categories'):
                    processed_count = await processor.process_articles(articles)

        assert processed_count == 1

    @pytest.mark.asyncio
    async def test_process_articles_with_duplicates(self, processor, mock_db_session, sample_article_data):
        """Test processing articles with duplicates."""
        # Mock first article exists, second doesn't
        mock_results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=MagicMock())),  # Exists
            MagicMock(scalar_one_or_none=MagicMock(return_value=None))  # Doesn't exist
        ]
        mock_db_session.execute.side_effect = mock_results

        articles = [
            sample_article_data,
            {**sample_article_data, "ID": 12346, "GUID": "different-guid"}
        ]

        with patch.object(processor, '_process_publisher', return_value=MagicMock(id=1)):
            with patch.object(processor, '_create_article', return_value=MagicMock()):
                with patch.object(processor, '_process_categories'):
                    processed_count = await processor.process_articles(articles)

        # Should process only 1 (the non-duplicate)
        assert processed_count == 1

    @pytest.mark.asyncio
    async def test_process_articles_with_error(self, processor, mock_db_session, sample_article_data):
        """Test processing articles with error handling."""
        # Mock article doesn't exist
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Mock publisher processing to raise an exception
        with patch.object(processor, '_process_publisher', side_effect=Exception("Test error")):
            processed_count = await processor.process_articles([sample_article_data])

        # Should handle error gracefully and return 0
        assert processed_count == 0

    @pytest.mark.asyncio
    async def test_parse_published_date_timestamp(self, processor):
        """Test parsing published date from timestamp."""
        timestamp = 1691683200  # Unix timestamp
        
        parsed_date = processor._parse_published_date(timestamp)
        
        assert isinstance(parsed_date, datetime)
        assert parsed_date.tzinfo == timezone.utc

    @pytest.mark.asyncio
    async def test_parse_published_date_none(self, processor):
        """Test parsing published date when None."""
        parsed_date = processor._parse_published_date(None)
        assert parsed_date is None

    @pytest.mark.asyncio
    async def test_parse_published_date_invalid(self, processor):
        """Test parsing published date with invalid data."""
        parsed_date = processor._parse_published_date("invalid")
        assert parsed_date is None
