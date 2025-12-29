"""
Integration tests for Health API routes.

Tests the health check and status endpoints including:
- GET / - Root endpoint
- GET /api/v1/health - Health check
- GET /api/v1/status - System status
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthRoutes:
    """Integration tests for health and status routes."""

    def test_root_endpoint(
        self,
        test_client: TestClient
    ):
        """Test root endpoint returns API information."""
        # Act
        response = test_client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "LLM Platform" in data["message"]

    def test_health_check_endpoint(
        self,
        test_client: TestClient
    ):
        """Test health check endpoint."""
        # Act
        response = test_client.get("/api/v1/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        # With mock database, status might be "degraded" instead of "healthy"
        assert data["status"] in ["healthy", "degraded"]
        assert "database" in data
        assert "providers" in data
        assert "config" in data

    def test_status_endpoint(
        self,
        test_client: TestClient
    ):
        """Test system status endpoint."""
        # Act
        response = test_client.get("/api/v1/status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["ok", "healthy", "running"]

    def test_health_endpoint_returns_consistent_format(
        self,
        test_client: TestClient
    ):
        """Test that health endpoint returns consistent format."""
        # Act
        response = test_client.get("/api/v1/health")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify expected structure
        assert isinstance(data, dict)
        assert "status" in data
        assert isinstance(data["status"], str)

    def test_root_endpoint_provides_documentation_link(
        self,
        test_client: TestClient
    ):
        """Test that root endpoint includes documentation links."""
        # Act
        response = test_client.get("/")

        # Assert
        data = response.json()
        assert "docs" in data or "api" in data

    def test_health_check_is_fast(
        self,
        test_client: TestClient
    ):
        """Test that health check responds quickly."""
        import time

        # Act
        start = time.time()
        response = test_client.get("/api/v1/health")
        duration = time.time() - start

        # Assert
        assert response.status_code == 200
        assert duration < 1.0  # Should respond in less than 1 second

    def test_multiple_health_checks(
        self,
        test_client: TestClient
    ):
        """Test multiple consecutive health checks."""
        # Act - Call health check multiple times
        for _ in range(5):
            response = test_client.get("/api/v1/health")

            # Assert each call succeeds
            assert response.status_code == 200
            # With mock database, status might be "degraded" instead of "healthy"
            assert response.json()["status"] in ["healthy", "degraded"]

    def test_api_versioning_in_path(
        self,
        test_client: TestClient
    ):
        """Test that API endpoints use versioning (v1)."""
        # Act
        health_response = test_client.get("/api/v1/health")
        status_response = test_client.get("/api/v1/status")

        # Assert both v1 endpoints exist
        assert health_response.status_code == 200
        assert status_response.status_code == 200
