"""Tests for system monitoring tools."""

import pytest
from unittest.mock import AsyncMock, patch

from azops_mcp import server


class TestGetSystemMetrics:
    """Tests for the get_system_metrics tool."""

    @pytest.mark.asyncio
    async def test_get_system_metrics_success(self):
        """Test get_system_metrics returns metrics."""
        with patch.object(server.monitoring, "get_system_metrics", new_callable=AsyncMock) as mock_metrics:
            mock_metrics.return_value = "System Metrics:\nCPU: 50%\nMemory: 70%"
            result = await server.get_system_metrics()

            assert "Error" not in result
            mock_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_system_metrics_handles_exception(self):
        """Test get_system_metrics handles exceptions gracefully."""
        with patch.object(server.monitoring, "get_system_metrics", new_callable=AsyncMock) as mock_metrics:
            mock_metrics.side_effect = Exception("Failed to get metrics")
            result = await server.get_system_metrics()

            assert "Error" in result
            assert "Failed to get metrics" in result


class TestCheckServiceHealth:
    """Tests for the check_service_health tool."""

    @pytest.mark.asyncio
    async def test_check_service_health_with_valid_service(self):
        """Test check_service_health with valid service name."""
        with patch.object(server.monitoring, "check_service_health", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = "Service 'nginx' is active"
            result = await server.check_service_health("nginx")

            assert "Error" not in result
            mock_health.assert_called_once_with("nginx")

    @pytest.mark.asyncio
    async def test_check_service_health_with_empty_service_name(self):
        """Test check_service_health with empty service_name returns error."""
        result = await server.check_service_health("")
        assert "Error" in result
        assert "service_name" in result.lower()


class TestGetInfrastructureStatus:
    """Tests for the get_infrastructure_status tool."""

    @pytest.mark.asyncio
    async def test_get_infrastructure_status_success(self):
        """Test get_infrastructure_status returns status."""
        with patch.object(server.monitoring, "get_infrastructure_status", new_callable=AsyncMock) as mock_status:
            mock_status.return_value = "Infrastructure Status:\n✓ Docker: Available"
            result = await server.get_infrastructure_status()

            assert "Error" not in result
            mock_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_infrastructure_status_handles_exception(self):
        """Test get_infrastructure_status handles exceptions gracefully."""
        with patch.object(server.monitoring, "get_infrastructure_status", new_callable=AsyncMock) as mock_status:
            mock_status.side_effect = Exception("Status check failed")
            result = await server.get_infrastructure_status()

            assert "Error" in result
            assert "Status check failed" in result
