"""Tests for resource groups, tags, locks, and activity log tools."""

import pytest
from unittest.mock import AsyncMock, patch

from azops_mcp import server


class TestListResourceGroups:
    """Tests for the list_resource_groups tool."""

    @pytest.mark.asyncio
    async def test_list_resource_groups_success(self):
        """Test list_resource_groups returns resource groups."""
        with patch.object(server.resource_groups, "list_resource_groups", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure Resource Groups:\n..."
            result = await server.list_resource_groups()

            assert "Error" not in result
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_resource_groups_handles_exception(self):
        """Test list_resource_groups handles exceptions gracefully."""
        with patch.object(server.resource_groups, "list_resource_groups", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Azure SDK not installed")
            result = await server.list_resource_groups()

            assert "Error" in result
            assert "Azure SDK" in result


class TestListTags:
    """Tests for the list_tags tool."""

    @pytest.mark.asyncio
    async def test_list_tags_success(self):
        """Test list_tags returns tags."""
        with patch.object(server.resource_groups, "list_tags", new_callable=AsyncMock) as mock_tags:
            mock_tags.return_value = "Tags:\nenv: production\nteam: platform"
            result = await server.list_tags("my-rg")

            assert "Error" not in result
            mock_tags.assert_called_once_with("my-rg")

    @pytest.mark.asyncio
    async def test_list_tags_subscription_level(self):
        """Test list_tags at subscription level (no RG)."""
        with patch.object(server.resource_groups, "list_tags", new_callable=AsyncMock) as mock_tags:
            mock_tags.return_value = "Subscription Tags:\n..."
            result = await server.list_tags("")

            assert "Error" not in result
            mock_tags.assert_called_once_with(None)


class TestListResourceLocks:
    """Tests for the list_resource_locks tool."""

    @pytest.mark.asyncio
    async def test_list_resource_locks_success(self):
        """Test list_resource_locks returns locks."""
        with patch.object(server.resource_groups, "list_resource_locks", new_callable=AsyncMock) as mock_locks:
            mock_locks.return_value = "Resource Locks:\n..."
            result = await server.list_resource_locks("my-rg")

            assert "Error" not in result
            mock_locks.assert_called_once_with("my-rg")

    @pytest.mark.asyncio
    async def test_list_resource_locks_handles_exception(self):
        """Test list_resource_locks handles exceptions gracefully."""
        with patch.object(server.resource_groups, "list_resource_locks", new_callable=AsyncMock) as mock_locks:
            mock_locks.side_effect = Exception("Permission denied")
            result = await server.list_resource_locks("my-rg")

            assert "Error" in result


class TestGetActivityLog:
    """Tests for the get_activity_log tool."""

    @pytest.mark.asyncio
    async def test_get_activity_log_success(self):
        """Test get_activity_log returns activity entries."""
        with patch.object(server.resource_groups, "get_activity_log", new_callable=AsyncMock) as mock_log:
            mock_log.return_value = "Activity Log:\n..."
            result = await server.get_activity_log("my-rg", 3)

            assert "Error" not in result
            mock_log.assert_called_once_with("my-rg", 3)

    @pytest.mark.asyncio
    async def test_get_activity_log_handles_exception(self):
        """Test get_activity_log handles exceptions gracefully."""
        with patch.object(server.resource_groups, "get_activity_log", new_callable=AsyncMock) as mock_log:
            mock_log.side_effect = Exception("Monitor SDK not available")
            result = await server.get_activity_log("my-rg", 1)

            assert "Error" in result
