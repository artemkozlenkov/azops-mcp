"""Tests for Docker container runtime tools."""

import pytest
from unittest.mock import AsyncMock, patch

from azops_mcp import server


class TestListContainers:
    """Tests for the list_containers tool."""

    @pytest.mark.asyncio
    async def test_list_containers_success(self):
        """Test list_containers returns container list."""
        with patch.object(server.docker, "list_containers", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Running Containers:\n..."
            result = await server.list_containers()

            assert "Error" not in result
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_containers_handles_exception(self):
        """Test list_containers handles exceptions gracefully."""
        with patch.object(server.docker, "list_containers", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Docker not available")
            result = await server.list_containers()

            assert "Error" in result
            assert "Docker not available" in result


class TestGetContainerLogs:
    """Tests for the get_container_logs tool."""

    @pytest.mark.asyncio
    async def test_get_container_logs_with_valid_inputs(self):
        """Test get_container_logs with valid inputs."""
        with patch.object(server.docker, "get_container_logs", new_callable=AsyncMock) as mock_logs:
            mock_logs.return_value = "Logs for container abc123"
            result = await server.get_container_logs("abc123", 100)

            assert "Error" not in result
            mock_logs.assert_called_once_with("abc123", 100)

    @pytest.mark.asyncio
    async def test_get_container_logs_with_empty_container_id(self):
        """Test get_container_logs with empty container_id returns error."""
        result = await server.get_container_logs("", 50)
        assert "Error" in result
        assert "container_id" in result.lower()

    @pytest.mark.asyncio
    async def test_get_container_logs_with_negative_lines(self):
        """Test get_container_logs with negative lines returns error."""
        result = await server.get_container_logs("abc123", -10)
        assert "Error" in result
        assert "positive" in result.lower()

    @pytest.mark.asyncio
    async def test_get_container_logs_with_zero_lines(self):
        """Test get_container_logs with zero lines returns error."""
        result = await server.get_container_logs("abc123", 0)
        assert "Error" in result
        assert "positive" in result.lower()


class TestRestartContainer:
    """Tests for the restart_container tool."""

    @pytest.mark.asyncio
    async def test_restart_container_with_valid_input(self):
        """Test restart_container with valid input."""
        with patch.object(server.docker, "restart_container", new_callable=AsyncMock) as mock_restart:
            mock_restart.return_value = "Container abc123 restarted successfully"
            result = await server.restart_container("abc123")

            assert "Error" not in result
            mock_restart.assert_called_once_with("abc123")

    @pytest.mark.asyncio
    async def test_restart_container_with_empty_container_id(self):
        """Test restart_container with empty container_id returns error."""
        result = await server.restart_container("")
        assert "Error" in result
        assert "container_id" in result.lower()
