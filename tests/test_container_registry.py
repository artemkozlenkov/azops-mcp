"""Tests for Azure Container Registry (ACR) tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from azops_mcp import server


class TestAcrListRegistries:
    """Tests for the acr_list_registries tool."""

    @pytest.mark.asyncio
    async def test_list_registries_success(self):
        """Test acr_list_registries returns registries."""
        with patch.object(server.container_registry, "acr_list_registries", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Container Registries:\n- myacr (Basic)"
            result = await server.acr_list_registries("my-rg")

            assert "Error" not in result
            mock_list.assert_called_once_with("my-rg")

    @pytest.mark.asyncio
    async def test_list_registries_subscription_level(self):
        """Test acr_list_registries at subscription level."""
        with patch.object(server.container_registry, "acr_list_registries", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Container Registries:\n..."
            result = await server.acr_list_registries("")

            assert "Error" not in result
            mock_list.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_list_registries_handles_exception(self):
        """Test acr_list_registries handles exceptions gracefully."""
        with patch.object(server.container_registry, "acr_list_registries", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("ACR SDK not available")
            result = await server.acr_list_registries("")

            assert "Error" in result


class TestAcrShowRegistry:
    """Tests for the acr_show_registry tool."""

    @pytest.mark.asyncio
    async def test_show_registry_success(self):
        """Test acr_show_registry returns registry details."""
        with patch.object(server.container_registry, "acr_show_registry", new_callable=AsyncMock) as mock_show:
            mock_show.return_value = "Registry: myacr\nSKU: Basic\nLocation: eastus"
            result = await server.acr_show_registry("my-rg", "myacr")

            assert "Error" not in result
            mock_show.assert_called_once_with("my-rg", "myacr")

    @pytest.mark.asyncio
    async def test_show_registry_missing_params(self):
        """Test acr_show_registry with missing params returns error."""
        result = await server.acr_show_registry("", "myacr")
        assert "Error" in result

        result = await server.acr_show_registry("my-rg", "")
        assert "Error" in result


class TestAcrCreateRegistry:
    """Tests for the acr_create_registry tool."""

    @pytest.mark.asyncio
    async def test_create_registry_success(self):
        """Test acr_create_registry creates a registry."""
        with patch.object(server.container_registry, "acr_create_registry", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "Registry 'myacr' created in 'eastus'"
            result = await server.acr_create_registry("my-rg", "myacr", "eastus", "Basic", False)

            assert "Error" not in result
            mock_create.assert_called_once()


class TestAcrDeleteRegistry:
    """Tests for the acr_delete_registry tool."""

    @pytest.mark.asyncio
    async def test_delete_registry_success(self):
        """Test acr_delete_registry deletes a registry."""
        with patch.object(server.container_registry, "acr_delete_registry", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = "Registry 'myacr' deleted."
            result = await server.acr_delete_registry("my-rg", "myacr")

            assert "Error" not in result
            mock_delete.assert_called_once_with("my-rg", "myacr")


class TestAcrGetCredentials:
    """Tests for the acr_get_credentials tool."""

    @pytest.mark.asyncio
    async def test_get_credentials_success(self):
        """Test acr_get_credentials returns credentials."""
        with patch.object(server.container_registry, "acr_get_credentials", new_callable=AsyncMock) as mock_creds:
            mock_creds.return_value = "Credentials:\nUsername: myacr\nPassword: ***"
            result = await server.acr_get_credentials("my-rg", "myacr")

            assert "Error" not in result
            mock_creds.assert_called_once_with("my-rg", "myacr")


class TestAcrResetClient:
    """Tests for the acr_reset_client tool."""

    @pytest.mark.asyncio
    async def test_reset_client_success(self):
        """Test acr_reset_client clears client cache."""
        with patch.object(server.container_registry, "reset_acr_client") as mock_reset:
            result = await server.acr_reset_client()

            assert "Error" not in result
            assert "cleared" in result.lower()
            mock_reset.assert_called_once()
