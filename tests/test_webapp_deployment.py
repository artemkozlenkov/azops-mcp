"""Tests for Web App for Containers deployment tools."""

from unittest.mock import AsyncMock, patch

import pytest

from azops_mcp import server


class TestWebappCreateForContainer:
    """Tests for the webapp_create_for_container tool."""

    @pytest.mark.asyncio
    async def test_create_for_container_success(self):
        """Test webapp_create_for_container creates a web app."""
        with patch.object(
            server.webapp_deployment, "webapp_create_for_container", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = "Web App for Containers created successfully!"
            result = await server.webapp_create_for_container(
                name="my-app",
                resource_group="my-rg",
                plan_name="my-plan",
                image="myacr.azurecr.io/myapp:latest",
            )

            assert "Error" not in result
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_for_container_handles_exception(self):
        """Test webapp_create_for_container handles exceptions gracefully."""
        with patch.object(
            server.webapp_deployment, "webapp_create_for_container", new_callable=AsyncMock
        ) as mock_create:
            mock_create.side_effect = Exception("Deployment failed")
            result = await server.webapp_create_for_container(
                name="my-app",
                resource_group="my-rg",
                plan_name="my-plan",
            )

            assert "Error" in result


class TestWebappGrantCrAccess:
    """Tests for the webapp_grant_cr_access tool."""

    @pytest.mark.asyncio
    async def test_grant_cr_access_success(self):
        """Test webapp_grant_cr_access grants access."""
        with patch.object(server.webapp_deployment, "webapp_grant_cr_access", new_callable=AsyncMock) as mock_grant:
            mock_grant.return_value = "RBAC permission granted for 'my-app'"
            result = await server.webapp_grant_cr_access("my-app", "my-rg", "myacr", "my-rg", "AcrPull")

            assert "Error" not in result
            mock_grant.assert_called_once()

    @pytest.mark.asyncio
    async def test_grant_cr_access_missing_params(self):
        """Test webapp_grant_cr_access with missing params returns error."""
        result = await server.webapp_grant_cr_access("", "my-rg", "myacr", "my-rg")
        assert "Error" in result


class TestWebappConfigureVnetIntegration:
    """Tests for the webapp_configure_vnet_integration tool."""

    @pytest.mark.asyncio
    async def test_configure_vnet_success(self):
        """Test webapp_configure_vnet_integration succeeds."""
        with patch.object(
            server.webapp_deployment, "webapp_configure_vnet_integration", new_callable=AsyncMock
        ) as mock_vnet:
            mock_vnet.return_value = "VNet integration configured"
            result = await server.webapp_configure_vnet_integration(
                "my-app", "my-rg", "/subscriptions/.../subnets/default"
            )

            assert "Error" not in result
            mock_vnet.assert_called_once()

    @pytest.mark.asyncio
    async def test_configure_vnet_missing_params(self):
        """Test webapp_configure_vnet_integration with missing params returns error."""
        result = await server.webapp_configure_vnet_integration("", "my-rg", "/sub/id")
        assert "Error" in result


class TestWebappAssignIdentity:
    """Tests for the webapp_assign_identity tool."""

    @pytest.mark.asyncio
    async def test_assign_identity_success(self):
        """Test webapp_assign_identity succeeds."""
        with patch.object(server.webapp_deployment, "webapp_assign_identity", new_callable=AsyncMock) as mock_identity:
            mock_identity.return_value = "Managed identity assigned"
            result = await server.webapp_assign_identity("my-app", "my-rg")

            assert "Error" not in result
            mock_identity.assert_called_once()


class TestWebappViewLogs:
    """Tests for the webapp_view_logs tool."""

    @pytest.mark.asyncio
    async def test_view_logs_success(self):
        """Test webapp_view_logs returns logs."""
        with patch.object(server.webapp_deployment, "webapp_view_logs", new_callable=AsyncMock) as mock_logs:
            mock_logs.return_value = "Web App Activity Log:\n..."
            result = await server.webapp_view_logs("my-app", "my-rg", 3)

            assert "Error" not in result
            mock_logs.assert_called_once_with("my-app", "my-rg", 3)


class TestWebappDelete:
    """Tests for the webapp_delete tool."""

    @pytest.mark.asyncio
    async def test_delete_success(self):
        """Test webapp_delete deletes a web app."""
        with patch.object(server.webapp_deployment, "webapp_delete", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = "Web app 'my-app' deleted."
            result = await server.webapp_delete("my-app", "my-rg")

            assert "Error" not in result
            mock_delete.assert_called_once_with("my-app", "my-rg")
