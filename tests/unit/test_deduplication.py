"""Unit tests for article deduplication functionality."""

import pytest
from crypto_newsletter.core.ingestion.deduplication import deduplicate_articles


@pytest.mark.unit
class TestDeduplication:
    """Test cases for article deduplication."""

    def test_deduplicate_by_external_id(self, test_data_factory):
        """Test deduplication by external ID."""
        articles = [
            test_data_factory.create_article_data(article_id=12345, title="Article 1"),
            test_data_factory.create_article_data(article_id=12345, title="Article 1 Duplicate"),
            test_data_factory.create_article_data(article_id=12346, title="Article 2"),
        ]

        unique_articles = deduplicate_articles(articles)

        assert len(unique_articles) == 2
        # Should keep the first occurrence
        assert unique_articles[0]["ID"] == 12345
        assert unique_articles[0]["TITLE"] == "Article 1"
        assert unique_articles[1]["ID"] == 12346

    def test_deduplicate_by_guid(self, test_data_factory):
        """Test deduplication by GUID."""
        articles = [
            test_data_factory.create_article_data(
                article_id=12345, 
                title="Article 1",
                GUID="same-guid"
            ),
            test_data_factory.create_article_data(
                article_id=12346, 
                title="Article 1 Duplicate",
                GUID="same-guid"
            ),
            test_data_factory.create_article_data(
                article_id=12347, 
                title="Article 2",
                GUID="different-guid"
            ),
        ]

        unique_articles = deduplicate_articles(articles)

        assert len(unique_articles) == 2
        # Should keep the first occurrence
        assert unique_articles[0]["GUID"] == "same-guid"
        assert unique_articles[0]["TITLE"] == "Article 1"
        assert unique_articles[1]["GUID"] == "different-guid"

    def test_deduplicate_by_url(self, test_data_factory):
        """Test deduplication by URL."""
        articles = [
            test_data_factory.create_article_data(
                article_id=12345,
                title="Article 1",
                url="https://example.com/article-1"
            ),
            test_data_factory.create_article_data(
                article_id=12346,
                title="Article 1 Duplicate",
                url="https://example.com/article-1"
            ),
            test_data_factory.create_article_data(
                article_id=12347,
                title="Article 2",
                url="https://example.com/article-2"
            ),
        ]

        unique_articles = deduplicate_articles(articles)

        assert len(unique_articles) == 2
        # Should keep the first occurrence
        assert unique_articles[0]["URL"] == "https://example.com/article-1"
        assert unique_articles[0]["TITLE"] == "Article 1"
        assert unique_articles[1]["URL"] == "https://example.com/article-2"

    def test_deduplicate_mixed_criteria(self, test_data_factory):
        """Test deduplication with mixed criteria."""
        articles = [
            test_data_factory.create_article_data(
                article_id=12345,
                title="Article 1",
                url="https://example.com/article-1",
                GUID="guid-1"
            ),
            test_data_factory.create_article_data(
                article_id=12346,
                title="Article 2",
                url="https://example.com/article-1",  # Same URL
                GUID="guid-2"
            ),
            test_data_factory.create_article_data(
                article_id=12347,
                title="Article 3",
                url="https://example.com/article-3",
                GUID="guid-1"  # Same GUID
            ),
            test_data_factory.create_article_data(
                article_id=12345,  # Same ID
                title="Article 4",
                url="https://example.com/article-4",
                GUID="guid-4"
            ),
            test_data_factory.create_article_data(
                article_id=12348,
                title="Article 5",
                url="https://example.com/article-5",
                GUID="guid-5"
            ),
        ]

        unique_articles = deduplicate_articles(articles)

        # Should have 2 unique articles:
        # - First article (ID: 12345, URL: article-1, GUID: guid-1)
        # - Last article (ID: 12348, URL: article-5, GUID: guid-5)
        assert len(unique_articles) == 2
        assert unique_articles[0]["ID"] == 12345
        assert unique_articles[1]["ID"] == 12348

    def test_deduplicate_empty_list(self):
        """Test deduplication with empty list."""
        articles = []
        unique_articles = deduplicate_articles(articles)
        assert unique_articles == []

    def test_deduplicate_single_article(self, test_data_factory):
        """Test deduplication with single article."""
        articles = [test_data_factory.create_article_data()]
        unique_articles = deduplicate_articles(articles)
        assert len(unique_articles) == 1
        assert unique_articles[0] == articles[0]

    def test_deduplicate_no_duplicates(self, test_data_factory):
        """Test deduplication when no duplicates exist."""
        articles = test_data_factory.create_multiple_articles(count=5)
        unique_articles = deduplicate_articles(articles)
        assert len(unique_articles) == 5
        assert unique_articles == articles

    def test_deduplicate_all_duplicates(self, test_data_factory):
        """Test deduplication when all articles are duplicates."""
        base_article = test_data_factory.create_article_data()
        articles = [base_article.copy() for _ in range(5)]
        
        unique_articles = deduplicate_articles(articles)
        assert len(unique_articles) == 1
        assert unique_articles[0] == base_article

    def test_deduplicate_missing_fields(self, test_data_factory):
        """Test deduplication with articles missing key fields."""
        articles = [
            {
                "ID": 12345,
                "TITLE": "Article 1",
                # Missing GUID and URL
            },
            {
                "GUID": "guid-1",
                "TITLE": "Article 2",
                # Missing ID and URL
            },
            {
                "URL": "https://example.com/article-3",
                "TITLE": "Article 3",
                # Missing ID and GUID
            },
            {
                "ID": 12345,  # Same as first
                "TITLE": "Article 4",
            }
        ]

        unique_articles = deduplicate_articles(articles)
        
        # Should deduplicate based on available fields
        # Articles 1 and 4 have same ID, so should be deduplicated
        assert len(unique_articles) == 3

    def test_deduplicate_preserves_order(self, test_data_factory):
        """Test that deduplication preserves the order of first occurrences."""
        articles = [
            test_data_factory.create_article_data(article_id=12345, title="First"),
            test_data_factory.create_article_data(article_id=12346, title="Second"),
            test_data_factory.create_article_data(article_id=12347, title="Third"),
            test_data_factory.create_article_data(article_id=12345, title="Duplicate First"),
            test_data_factory.create_article_data(article_id=12348, title="Fourth"),
            test_data_factory.create_article_data(article_id=12346, title="Duplicate Second"),
        ]

        unique_articles = deduplicate_articles(articles)

        assert len(unique_articles) == 4
        assert unique_articles[0]["TITLE"] == "First"
        assert unique_articles[1]["TITLE"] == "Second"
        assert unique_articles[2]["TITLE"] == "Third"
        assert unique_articles[3]["TITLE"] == "Fourth"

    def test_deduplicate_case_sensitive_urls(self, test_data_factory):
        """Test that URL deduplication is case sensitive."""
        articles = [
            test_data_factory.create_article_data(
                article_id=12345,
                url="https://example.com/Article-1"
            ),
            test_data_factory.create_article_data(
                article_id=12346,
                url="https://example.com/article-1"  # Different case
            ),
        ]

        unique_articles = deduplicate_articles(articles)
        
        # URLs should be treated as different (case sensitive)
        assert len(unique_articles) == 2

    def test_deduplicate_with_none_values(self, test_data_factory):
        """Test deduplication with None values in key fields."""
        articles = [
            {
                "ID": None,
                "GUID": None,
                "URL": None,
                "TITLE": "Article 1"
            },
            {
                "ID": None,
                "GUID": None,
                "URL": None,
                "TITLE": "Article 2"
            },
            test_data_factory.create_article_data(article_id=12345)
        ]

        unique_articles = deduplicate_articles(articles)
        
        # Articles with None values should not be considered duplicates
        assert len(unique_articles) == 3

    def test_deduplicate_performance_large_dataset(self, test_data_factory):
        """Test deduplication performance with larger dataset."""
        # Create a larger dataset with some duplicates
        articles = []
        for i in range(1000):
            articles.append(test_data_factory.create_article_data(
                article_id=i % 100,  # This will create duplicates
                title=f"Article {i}"
            ))

        unique_articles = deduplicate_articles(articles)
        
        # Should have 100 unique articles (based on ID)
        assert len(unique_articles) == 100
        
        # Verify the first occurrence is preserved
        assert unique_articles[0]["TITLE"] == "Article 0"
        assert unique_articles[1]["TITLE"] == "Article 1"
