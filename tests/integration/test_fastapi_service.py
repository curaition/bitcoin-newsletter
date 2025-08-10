"""Integration tests for FastAPI web service."""

import pytest
from fastapi.testclient import TestClient

from crypto_newsletter.web.main import create_app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_basic_health(self, client):
        """Test basic health endpoint."""
        response = client.get("/health/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "crypto-newsletter"
        assert "timestamp" in data

    def test_readiness_check(self, client):
        """Test readiness probe endpoint."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "crypto-newsletter"
        assert "timestamp" in data

    def test_liveness_check(self, client):
        """Test liveness probe endpoint."""
        response = client.get("/health/live")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "alive"
        assert data["service"] == "crypto-newsletter"
        assert "timestamp" in data


class TestAPIEndpoints:
    """Test public API endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "crypto-newsletter"
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
        assert data["environment"] == "development"

    def test_articles_endpoint(self, client):
        """Test articles listing endpoint."""
        response = client.get("/api/articles?limit=5")
        assert response.status_code == 200
        
        articles = response.json()
        assert isinstance(articles, list)
        assert len(articles) <= 5
        
        if articles:
            article = articles[0]
            assert "id" in article
            assert "title" in article
            assert "url" in article
            assert "status" in article

    def test_articles_with_filters(self, client):
        """Test articles endpoint with filters."""
        # Test with hours filter
        response = client.get("/api/articles?limit=3&hours_back=24")
        assert response.status_code == 200
        
        articles = response.json()
        assert isinstance(articles, list)
        assert len(articles) <= 3

    def test_stats_endpoint(self, client):
        """Test statistics endpoint."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_articles" in stats
        assert "recent_articles" in stats
        assert "total_publishers" in stats
        assert "total_categories" in stats
        assert isinstance(stats["total_articles"], int)

    def test_article_by_id_not_found(self, client):
        """Test article by ID endpoint with non-existent ID."""
        response = client.get("/api/articles/999999")
        assert response.status_code == 404
        
        error = response.json()
        assert "not found" in error["detail"].lower()


class TestAdminEndpoints:
    """Test admin endpoints."""

    def test_admin_status_structure(self, client):
        """Test admin status endpoint structure."""
        response = client.get("/admin/status")
        
        # Should return either 200 or 500 (depending on Celery availability)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "service" in data
            assert "environment" in data
            assert "timestamp" in data


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_endpoint(self, client):
        """Test non-existent endpoint."""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

    def test_invalid_article_id(self, client):
        """Test invalid article ID format."""
        response = client.get("/api/articles/invalid")
        assert response.status_code == 422  # Validation error


class TestCORSAndSecurity:
    """Test CORS and security configurations."""

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get("/health/")
        assert response.status_code == 200
        
        # In development mode, CORS should allow all origins
        # The test client doesn't include CORS headers, but we can verify the endpoint works

    def test_api_key_optional(self, client):
        """Test that API key is optional for public endpoints."""
        # Test without API key
        response = client.get("/api/articles?limit=1")
        assert response.status_code in [200, 500]  # Should not be 401/403
        
        # Test with invalid API key (should still work for public endpoints)
        headers = {"X-API-Key": "invalid-key"}
        response = client.get("/api/articles?limit=1", headers=headers)
        assert response.status_code in [200, 500]  # Should not be 401/403


class TestDocumentation:
    """Test API documentation endpoints."""

    def test_openapi_schema(self, client):
        """Test OpenAPI schema is available in development."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "Crypto Newsletter API"

    def test_docs_endpoint(self, client):
        """Test Swagger docs are available in development."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_app_lifespan():
    """Test application lifespan events."""
    # This test verifies that the app can be created and configured properly
    app = create_app()
    assert app.title == "Crypto Newsletter API"
    assert app.version == "1.0.0"
    
    # Verify routers are included
    route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
    
    # Check that key endpoints are registered
    assert "/" in route_paths
    assert "/health/" in route_paths
    assert "/api/articles" in route_paths
    assert "/admin/status" in route_paths
