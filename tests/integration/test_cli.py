"""Integration tests for the CLI interface."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from typer.testing import CliRunner

from crypto_newsletter.cli.main import app


@pytest.mark.integration
class TestCLICommands:
    """Test CLI command functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_environment(self):
        """Mock environment variables for testing."""
        env_vars = {
            'DATABASE_URL': 'sqlite:///test.db',
            'REDIS_URL': 'redis://localhost:6379/1',
            'COINDESK_API_KEY': 'test-api-key',
            'TESTING': 'true',
            'DEBUG': 'true'
        }
        with patch.dict(os.environ, env_vars):
            yield

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Crypto Newsletter CLI" in result.output
        assert "Commands" in result.output

    def test_version_command(self, runner):
        """Test version command."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Crypto Newsletter CLI v0.1.0" in result.output
        assert "Built with FastAPI, SQLAlchemy, and Celery" in result.output

    def test_commands_command(self, runner):
        """Test commands listing command."""
        result = runner.invoke(app, ["commands"])
        assert result.exit_code == 0
        assert "Available Commands" in result.output
        assert "Health & Monitoring" in result.output
        assert "Data Management" in result.output
        assert "health" in result.output
        assert "ingest" in result.output

    @patch('crypto_newsletter.cli.main.get_settings')
    def test_config_show_command(self, mock_get_settings, runner, mock_environment):
        """Test config-show command."""
        mock_settings = MagicMock()
        mock_settings.railway_environment = "development"
        mock_settings.service_type = "web"
        mock_settings.debug = True
        mock_settings.database_url = "postgresql://test@localhost/test"
        mock_settings.redis_url = "redis://localhost:6379/0"
        mock_settings.coindesk_base_url = "https://data-api.coindesk.com"
        mock_settings.coindesk_api_key = "test-api-key"
        mock_settings.enable_celery = True
        mock_get_settings.return_value = mock_settings

        result = runner.invoke(app, ["config-show"])
        assert result.exit_code == 0
        assert "Current Configuration" in result.output
        assert "development" in result.output
        assert "web" in result.output

    @patch('crypto_newsletter.cli.main.pipeline_health_check')
    def test_health_command_success(self, mock_health_check, runner, mock_environment):
        """Test health command with successful health check."""
        mock_health_check.return_value = {
            "status": "healthy",
            "timestamp": "2025-01-01T00:00:00Z",
            "checks": {
                "database": {"status": "healthy", "message": "Connected"},
                "coindesk_api": {"status": "healthy", "message": "API accessible"}
            }
        }

        result = runner.invoke(app, ["health"])
        assert result.exit_code == 0
        assert "Pipeline is healthy" in result.output

    @patch('crypto_newsletter.cli.main.pipeline_health_check')
    def test_health_command_failure(self, mock_health_check, runner, mock_environment):
        """Test health command with health check failure."""
        mock_health_check.side_effect = Exception("Health check failed")

        result = runner.invoke(app, ["health"])
        assert result.exit_code == 1
        assert "Health check failed" in result.output

    @patch('crypto_newsletter.cli.main.quick_ingestion_test')
    def test_test_command_success(self, mock_test, runner, mock_environment):
        """Test test command with successful pipeline test."""
        mock_test.return_value = True

        result = runner.invoke(app, ["test"])
        assert result.exit_code == 0
        assert "Pipeline test successful" in result.output

    @patch('crypto_newsletter.cli.main.quick_ingestion_test')
    def test_test_command_failure(self, mock_test, runner, mock_environment):
        """Test test command with pipeline test failure."""
        mock_test.return_value = False

        result = runner.invoke(app, ["test"])
        assert result.exit_code == 1
        assert "Pipeline test failed" in result.output

    @patch('crypto_newsletter.cli.main.run_article_ingestion')
    def test_ingest_command_success(self, mock_ingest, runner, mock_environment):
        """Test ingest command with successful ingestion."""
        mock_ingest.return_value = {
            "summary": {
                "articles_fetched": 10,
                "articles_processed": 8,
                "duplicates_skipped": 2,
                "success_rate": 0.8,
                "errors": 0
            },
            "processing_time_seconds": 5.5
        }

        result = runner.invoke(app, ["ingest", "--limit", "10"])
        assert result.exit_code == 0
        assert "Ingestion completed" in result.output
        assert "Articles fetched: 10" in result.output
        assert "Articles processed: 8" in result.output

    @patch('crypto_newsletter.cli.main.run_article_ingestion')
    def test_ingest_command_with_categories(self, mock_ingest, runner, mock_environment):
        """Test ingest command with category filtering."""
        mock_ingest.return_value = {
            "summary": {
                "articles_fetched": 5,
                "articles_processed": 5,
                "duplicates_skipped": 0,
                "success_rate": 1.0,
                "errors": 0
            },
            "processing_time_seconds": 3.2
        }

        result = runner.invoke(app, ["ingest", "--categories", "BTC,ETH", "--verbose"])
        assert result.exit_code == 0
        assert "Ingestion completed" in result.output

    @patch('crypto_newsletter.cli.main.get_recent_articles_with_stats')
    def test_stats_command(self, mock_stats, runner, mock_environment):
        """Test stats command."""
        mock_stats.return_value = {
            "statistics": {
                "total_articles": 100,
                "recent_articles_24h": 15,
                "last_updated": "2025-01-01T00:00:00Z",
                "top_publishers": [
                    {"publisher": "CoinDesk", "count": 50},
                    {"publisher": "CoinTelegraph", "count": 30}
                ],
                "top_categories": [
                    {"category": "Bitcoin", "count": 60},
                    {"category": "Ethereum", "count": 40}
                ]
            },
            "articles": [
                {
                    "title": "Test Article 1",
                    "publisher_id": 1
                },
                {
                    "title": "Test Article 2",
                    "publisher_id": 2
                }
            ]
        }

        result = runner.invoke(app, ["stats"])
        assert result.exit_code == 0
        assert "Article Statistics" in result.output
        assert "Total articles: 100" in result.output
        assert "Recent (24h): 15" in result.output

    def test_serve_command_validation(self, runner, mock_environment):
        """Test serve command parameter validation."""
        # Test conflicting dev and production flags
        result = runner.invoke(app, ["serve", "--dev", "--production"])
        assert result.exit_code == 1
        assert "Cannot enable both dev and production modes" in result.output

        # Test missing mode specification
        result = runner.invoke(app, ["serve"])
        assert result.exit_code == 1
        assert "Must specify either --dev or --production mode" in result.output

    @patch('crypto_newsletter.cli.main.start_worker')
    def test_worker_command(self, mock_start_worker, runner, mock_environment):
        """Test worker command."""
        result = runner.invoke(app, ["worker", "--loglevel", "DEBUG", "--concurrency", "4"])
        assert result.exit_code == 0
        mock_start_worker.assert_called_once_with(
            loglevel="DEBUG",
            concurrency=4,
            queues="default,ingestion,monitoring,maintenance"
        )

    @patch('crypto_newsletter.cli.main.start_beat')
    def test_beat_command(self, mock_start_beat, runner, mock_environment):
        """Test beat command."""
        result = runner.invoke(app, ["beat"])
        assert result.exit_code == 0
        mock_start_beat.assert_called_once()

    @patch('crypto_newsletter.cli.main.start_flower')
    def test_flower_command(self, mock_start_flower, runner, mock_environment):
        """Test flower command."""
        result = runner.invoke(app, ["flower", "--port", "5556"])
        assert result.exit_code == 0
        mock_start_flower.assert_called_once_with(port=5556)

    def test_dev_setup_command_missing_files(self, runner):
        """Test dev-setup command with missing required files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            result = runner.invoke(app, ["dev-setup"])
            assert result.exit_code == 1
            assert "Missing required files" in result.output

    def test_dev_setup_command_success(self, runner):
        """Test dev-setup command with required files present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            # Create required files
            Path(".env.development").touch()
            Path("pyproject.toml").touch()
            
            result = runner.invoke(app, ["dev-setup"])
            assert result.exit_code == 0
            assert "Development environment ready" in result.output

    @patch('crypto_newsletter.cli.main.get_settings')
    @patch('redis.from_url')
    def test_dev_reset_command(self, mock_redis, mock_get_settings, runner, mock_environment):
        """Test dev-reset command."""
        mock_settings = MagicMock()
        mock_settings.redis_url = "redis://localhost:6379/1"
        mock_get_settings.return_value = mock_settings
        
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            # Create some temporary files
            Path(".celerybeat-schedule").touch()
            Path("celerybeat.pid").touch()
            
            result = runner.invoke(app, ["dev-reset"])
            assert result.exit_code == 0
            assert "Development environment reset complete" in result.output
            mock_redis_client.flushdb.assert_called_once()

    def test_export_data_command_json(self, runner, mock_environment):
        """Test export-data command with JSON format."""
        with patch('crypto_newsletter.cli.main.get_db_session') as mock_get_session:
            with patch('crypto_newsletter.cli.main.ArticleRepository') as mock_repo_class:
                mock_session = AsyncMock()
                mock_get_session.return_value.__aenter__.return_value = mock_session
                
                mock_repo = AsyncMock()
                mock_article = MagicMock()
                mock_article.id = 1
                mock_article.title = "Test Article"
                mock_article.url = "https://test.com"
                mock_article.published_on = None
                mock_article.publisher_id = 1
                mock_repo.get_recent_articles.return_value = [mock_article]
                mock_repo_class.return_value = mock_repo

                with tempfile.TemporaryDirectory() as temp_dir:
                    output_file = Path(temp_dir) / "test_export.json"
                    
                    result = runner.invoke(app, [
                        "export-data",
                        "--output", str(output_file),
                        "--format", "json",
                        "--days", "7"
                    ])
                    
                    assert result.exit_code == 0
                    assert "Exported 1 articles" in result.output
                    assert output_file.exists()

    @patch('crypto_newsletter.cli.main.get_task_status')
    def test_task_status_command(self, mock_get_status, runner, mock_environment):
        """Test task-status command."""
        mock_get_status.return_value = {
            "task_id": "test-task-123",
            "status": "SUCCESS",
            "result": {"processed": 5},
            "date_done": "2025-01-01T00:00:00Z",
            "traceback": None
        }

        result = runner.invoke(app, ["task-status", "test-task-123"])
        assert result.exit_code == 0
        assert "Task Status: test-task-123" in result.output
        assert "Status: SUCCESS" in result.output
