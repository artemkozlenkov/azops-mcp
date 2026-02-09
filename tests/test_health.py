"""Tests for health check and rate limiting."""

import pytest
from unittest.mock import AsyncMock, patch

from azops_mcp import server


class TestHealthCheck:
    """Tests for the health_check tool."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_status(self):
        """Test that health_check returns healthy status."""
        result = await server.health_check()

        assert result["status"] == "healthy"
        assert "dependencies" in result
        assert "timestamp" in result
        assert "version" in result

    @pytest.mark.asyncio
    async def test_health_check_includes_dependencies(self):
        """Test that health_check includes Azure SDK dependency status."""
        result = await server.health_check()

        deps = result["dependencies"]
        assert "azure-identity" in deps
        assert "azure-mgmt-compute" in deps
        assert "azure-mgmt-resource" in deps
        assert "azure-mgmt-appconfiguration" in deps
        assert "azure-mgmt-web" in deps


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_allows_request(self):
        """Test that rate limiting allows requests within limit."""
        server.rate_limit_storage.clear()

        result = await server.check_rate_limit("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_blocks_when_exceeded(self):
        """Test that rate limiting blocks requests when limit exceeded."""
        server.rate_limit_storage.clear()

        original_limit = server.config.rate_limit_requests_per_minute
        server.config.rate_limit_requests_per_minute = 5

        try:
            for _ in range(5):
                await server.check_rate_limit("test_key_2")

            result = await server.check_rate_limit("test_key_2")
            assert result is False
        finally:
            server.config.rate_limit_requests_per_minute = original_limit

    @pytest.mark.asyncio
    async def test_check_rate_limit_disabled(self):
        """Test that rate limiting can be disabled."""
        original_enabled = server.config.rate_limit_enabled
        server.config.rate_limit_enabled = False

        try:
            for _ in range(100):
                result = await server.check_rate_limit("test_key_3")
                assert result is True
        finally:
            server.config.rate_limit_enabled = original_enabled
