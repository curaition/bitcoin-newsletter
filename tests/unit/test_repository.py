"""Unit tests for the article repository."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from crypto_newsletter.core.storage.repository import ArticleRepository
from crypto_newsletter.shared.models import Article, Publisher, Category


@pytest.mark.unit
class TestArticleRepository:
    """Test cases for ArticleRepository."""

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
    def repository(self, mock_db_session):
        """Create ArticleRepository instance."""
        return ArticleRepository(mock_db_session)

    @pytest.fixture
    def sample_article(self):
        """Create a sample article for testing."""
        return Article(
            id=1,
            external_id=12345,
            guid="test-guid",
            title="Test Article",
            url="https://test.com/article",
            body="Test article body",
            published_on=datetime.now(timezone.utc),
            status="ACTIVE",
            publisher_id=1
        )

    @pytest.mark.asyncio
    async def test_repository_initialization(self, repository, mock_db_session):
        """Test repository initialization."""
        assert repository.db == mock_db_session

    @pytest.mark.asyncio
    async def test_get_recent_articles(self, repository, mock_db_session, sample_article):
        """Test getting recent articles."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_article]
        mock_db_session.execute.return_value = mock_result

        articles = await repository.get_recent_articles(hours=24, limit=10)

        assert len(articles) == 1
        assert articles[0] == sample_article
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_articles_empty(self, repository, mock_db_session):
        """Test getting recent articles when none exist."""
        # Mock empty database response
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        articles = await repository.get_recent_articles(hours=24, limit=10)

        assert len(articles) == 0

    @pytest.mark.asyncio
    async def test_get_article_by_external_id(self, repository, mock_db_session, sample_article):
        """Test getting article by external ID."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_article
        mock_db_session.execute.return_value = mock_result

        article = await repository.get_article_by_external_id(12345)

        assert article == sample_article
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_article_by_external_id_not_found(self, repository, mock_db_session):
        """Test getting article by external ID when not found."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        article = await repository.get_article_by_external_id(99999)

        assert article is None

    @pytest.mark.asyncio
    async def test_get_article_by_url(self, repository, mock_db_session, sample_article):
        """Test getting article by URL."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_article
        mock_db_session.execute.return_value = mock_result

        article = await repository.get_article_by_url("https://test.com/article")

        assert article == sample_article
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_article_by_guid(self, repository, mock_db_session, sample_article):
        """Test getting article by GUID."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_article
        mock_db_session.execute.return_value = mock_result

        article = await repository.get_article_by_guid("test-guid")

        assert article == sample_article
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_articles_by_publisher(self, repository, mock_db_session, sample_article):
        """Test getting articles by publisher."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_article]
        mock_db_session.execute.return_value = mock_result

        articles = await repository.get_articles_by_publisher(1, limit=10)

        assert len(articles) == 1
        assert articles[0] == sample_article

    @pytest.mark.asyncio
    async def test_get_articles_by_category(self, repository, mock_db_session, sample_article):
        """Test getting articles by category."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_article]
        mock_db_session.execute.return_value = mock_result

        articles = await repository.get_articles_by_category("BTC", limit=10)

        assert len(articles) == 1
        assert articles[0] == sample_article

    @pytest.mark.asyncio
    async def test_get_article_statistics(self, repository, mock_db_session):
        """Test getting article statistics."""
        # Mock database responses for different queries
        mock_results = [
            MagicMock(scalar=MagicMock(return_value=100)),  # Total articles
            MagicMock(scalar=MagicMock(return_value=10)),   # Recent articles
            MagicMock(all=MagicMock(return_value=[          # Top publishers
                MagicMock(name="Publisher 1", article_count=50),
                MagicMock(name="Publisher 2", article_count=30)
            ])),
            MagicMock(all=MagicMock(return_value=[          # Top categories
                MagicMock(name="Bitcoin", article_count=60),
                MagicMock(name="Ethereum", article_count=40)
            ]))
        ]
        mock_db_session.execute.side_effect = mock_results

        stats = await repository.get_article_statistics()

        assert stats["total_articles"] == 100
        assert stats["recent_articles_24h"] == 10
        assert len(stats["top_publishers"]) == 2
        assert len(stats["top_categories"]) == 2
        assert stats["top_publishers"][0]["publisher"] == "Publisher 1"
        assert stats["top_categories"][0]["category"] == "Bitcoin"
        assert "last_updated" in stats

    @pytest.mark.asyncio
    async def test_mark_articles_as_deleted(self, repository, mock_db_session):
        """Test marking old articles as deleted."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        
        # Mock database response
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_db_session.execute.return_value = mock_result

        deleted_count = await repository.mark_articles_as_deleted(cutoff_date)

        assert deleted_count == 5
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_articles_by_status(self, repository, mock_db_session):
        """Test counting articles by status."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalar.return_value = 85
        mock_db_session.execute.return_value = mock_result

        count = await repository.count_articles_by_status("ACTIVE")

        assert count == 85
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_articles_by_date_range(self, repository, mock_db_session, sample_article):
        """Test getting articles by date range."""
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)

        # Mock database response
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_article]
        mock_db_session.execute.return_value = mock_result

        articles = await repository.get_articles_by_date_range(start_date, end_date)

        assert len(articles) == 1
        assert articles[0] == sample_article

    @pytest.mark.asyncio
    async def test_search_articles_by_title(self, repository, mock_db_session, sample_article):
        """Test searching articles by title."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_article]
        mock_db_session.execute.return_value = mock_result

        articles = await repository.search_articles_by_title("Bitcoin", limit=10)

        assert len(articles) == 1
        assert articles[0] == sample_article

    @pytest.mark.asyncio
    async def test_get_top_publishers(self, repository, mock_db_session):
        """Test getting top publishers by article count."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.all.return_value = [
            MagicMock(name="CoinDesk", article_count=100),
            MagicMock(name="CoinTelegraph", article_count=75)
        ]
        mock_db_session.execute.return_value = mock_result

        publishers = await repository.get_top_publishers(limit=5)

        assert len(publishers) == 2
        assert publishers[0]["publisher"] == "CoinDesk"
        assert publishers[0]["count"] == 100

    @pytest.mark.asyncio
    async def test_get_top_categories(self, repository, mock_db_session):
        """Test getting top categories by article count."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.all.return_value = [
            MagicMock(name="Bitcoin", article_count=150),
            MagicMock(name="Ethereum", article_count=100)
        ]
        mock_db_session.execute.return_value = mock_result

        categories = await repository.get_top_categories(limit=5)

        assert len(categories) == 2
        assert categories[0]["category"] == "Bitcoin"
        assert categories[0]["count"] == 150

    @pytest.mark.asyncio
    async def test_get_articles_with_pagination(self, repository, mock_db_session, sample_article):
        """Test getting articles with pagination."""
        # Mock database response
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_article]
        mock_db_session.execute.return_value = mock_result

        articles = await repository.get_articles_with_pagination(
            offset=10, 
            limit=20, 
            status="ACTIVE"
        )

        assert len(articles) == 1
        assert articles[0] == sample_article
