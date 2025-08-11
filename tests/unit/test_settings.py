"""Unit tests for application settings."""

import os
import pytest
from unittest.mock import patch

from crypto_newsletter.shared.config.settings import Settings, get_settings


@pytest.mark.unit
class TestSettings:
    """Test cases for application settings."""

    def test_settings_initialization_with_defaults(self):
        """Test settings initialization with default values."""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key'
        }, clear=True):
            settings = Settings()
            
            assert settings.railway_environment == "development"
            assert settings.service_type == "web"
            assert settings.debug is True
            assert settings.testing is False
            assert settings.database_url == 'postgresql://test:test@localhost/test'
            assert settings.redis_url == "redis://localhost:6379/0"
            assert settings.coindesk_api_key == 'test-api-key'
            assert settings.coindesk_base_url == "https://data-api.coindesk.com"

    def test_settings_with_environment_variables(self):
        """Test settings with custom environment variables."""
        env_vars = {
            'RAILWAY_ENVIRONMENT': 'production',
            'SERVICE_TYPE': 'worker',
            'DEBUG': 'false',
            'TESTING': 'true',
            'DATABASE_URL': 'postgresql://prod:prod@prod.db/prod',
            'REDIS_URL': 'redis://prod.redis:6379/0',
            'COINDESK_API_KEY': 'prod-api-key',
            'COINDESK_BASE_URL': 'https://custom-api.coindesk.com',
            'ARTICLE_RETENTION_HOURS': '48',
            'LOG_LEVEL': 'ERROR',
            'ENABLE_CELERY': 'true',
            'SECRET_KEY': 'super-secret-key',
            'PORT': '9000'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            assert settings.railway_environment == "production"
            assert settings.service_type == "worker"
            assert settings.debug is False
            assert settings.testing is True
            assert settings.database_url == 'postgresql://prod:prod@prod.db/prod'
            assert settings.redis_url == 'redis://prod.redis:6379/0'
            assert settings.coindesk_api_key == 'prod-api-key'
            assert settings.coindesk_base_url == 'https://custom-api.coindesk.com'
            assert settings.article_retention_hours == 48
            assert settings.log_level == 'ERROR'
            assert settings.enable_celery is True
            assert settings.secret_key == 'super-secret-key'
            assert settings.port == 9000

    def test_is_production_property(self):
        """Test is_production property."""
        with patch.dict(os.environ, {
            'RAILWAY_ENVIRONMENT': 'production',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key'
        }, clear=True):
            settings = Settings()
            assert settings.is_production is True

        with patch.dict(os.environ, {
            'RAILWAY_ENVIRONMENT': 'development',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key'
        }, clear=True):
            settings = Settings()
            assert settings.is_production is False

    def test_is_development_property(self):
        """Test is_development property."""
        with patch.dict(os.environ, {
            'RAILWAY_ENVIRONMENT': 'development',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key'
        }, clear=True):
            settings = Settings()
            assert settings.is_development is True

        with patch.dict(os.environ, {
            'RAILWAY_ENVIRONMENT': 'production',
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key'
        }, clear=True):
            settings = Settings()
            assert settings.is_development is False

    def test_effective_celery_broker_url(self):
        """Test effective Celery broker URL property."""
        # Test with explicit Celery broker URL
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key',
            'REDIS_URL': 'redis://localhost:6379/0',
            'CELERY_BROKER_URL': 'redis://celery.redis:6379/1'
        }, clear=True):
            settings = Settings()
            assert settings.effective_celery_broker_url == 'redis://celery.redis:6379/1'

        # Test fallback to Redis URL
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key',
            'REDIS_URL': 'redis://localhost:6379/0'
        }, clear=True):
            settings = Settings()
            assert settings.effective_celery_broker_url == 'redis://localhost:6379/0'

    def test_effective_celery_result_backend(self):
        """Test effective Celery result backend property."""
        # Test with explicit Celery result backend
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key',
            'REDIS_URL': 'redis://localhost:6379/0',
            'CELERY_RESULT_BACKEND': 'redis://celery.redis:6379/2'
        }, clear=True):
            settings = Settings()
            assert settings.effective_celery_result_backend == 'redis://celery.redis:6379/2'

        # Test fallback to Redis URL
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key',
            'REDIS_URL': 'redis://localhost:6379/0'
        }, clear=True):
            settings = Settings()
            assert settings.effective_celery_result_backend == 'redis://localhost:6379/0'

    def test_railway_specific_settings(self):
        """Test Railway-specific environment variables."""
        env_vars = {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key',
            'RAILWAY_PROJECT_ID': 'project-123',
            'RAILWAY_SERVICE_ID': 'service-456',
            'RAILWAY_DEPLOYMENT_ID': 'deployment-789',
            'RAILWAY_PUBLIC_DOMAIN': 'myapp.railway.app',
            'RAILWAY_PRIVATE_DOMAIN': 'myapp.railway.internal'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            assert settings.railway_project_id == 'project-123'
            assert settings.railway_service_id == 'service-456'
            assert settings.railway_deployment_id == 'deployment-789'
            assert settings.railway_public_domain == 'myapp.railway.app'
            assert settings.railway_private_domain == 'myapp.railway.internal'

    def test_optional_email_settings(self):
        """Test optional email configuration settings."""
        env_vars = {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key',
            'SMTP_HOST': 'smtp.gmail.com',
            'SMTP_PORT': '465',
            'SMTP_USERNAME': 'test@gmail.com',
            'SMTP_PASSWORD': 'app-password',
            'FROM_EMAIL': 'newsletter@example.com'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            
            assert settings.smtp_host == 'smtp.gmail.com'
            assert settings.smtp_port == 465
            assert settings.smtp_username == 'test@gmail.com'
            assert settings.smtp_password == 'app-password'
            assert settings.from_email == 'newsletter@example.com'

    def test_boolean_environment_variables(self):
        """Test boolean environment variable parsing."""
        # Test various boolean representations
        boolean_tests = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('0', False),
            ('no', False),
            ('', False)
        ]
        
        for env_value, expected in boolean_tests:
            with patch.dict(os.environ, {
                'DATABASE_URL': 'postgresql://test:test@localhost/test',
                'COINDESK_API_KEY': 'test-api-key',
                'DEBUG': env_value,
                'TESTING': env_value,
                'ENABLE_CELERY': env_value
            }, clear=True):
                settings = Settings()
                assert settings.debug == expected
                assert settings.testing == expected
                assert settings.enable_celery == expected

    def test_get_settings_singleton(self):
        """Test get_settings function returns singleton."""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key'
        }, clear=True):
            # Clear any existing singleton
            import crypto_newsletter.shared.config.settings
            crypto_newsletter.shared.config.settings._settings = None
            
            settings1 = get_settings()
            settings2 = get_settings()
            
            assert settings1 is settings2

    def test_missing_required_settings(self):
        """Test behavior with missing required settings."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception):  # Should raise validation error
                Settings()

    def test_settings_with_env_file(self):
        """Test settings loading from environment file."""
        # This would test .env file loading in a real scenario
        # For now, we'll test the configuration is set up correctly
        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://test:test@localhost/test',
            'COINDESK_API_KEY': 'test-api-key'
        }, clear=True):
            settings = Settings()
            
            # Verify the model config is set up for env file loading
            assert hasattr(settings.model_config, 'env_file')
            assert '.env.development' in settings.model_config['env_file']
            assert '.env' in settings.model_config['env_file']
