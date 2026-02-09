"""Tests for subscription, auth, and account management tools."""

from unittest.mock import AsyncMock, patch

import pytest

from azops_mcp import server


class TestAuthStatus:
    """Tests for the auth_status tool."""

    @pytest.mark.asyncio
    async def test_auth_status_success(self):
        """Test auth_status returns authentication status."""
        with patch.object(server.subscription, "get_auth_status", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "Azure Authentication Status:\nMethod: Azure CLI\nStatus: Authenticated"
            result = await server.auth_status()

            assert "Error" not in result
            mock_auth.assert_called_once()

    @pytest.mark.asyncio
    async def test_auth_status_handles_exception(self):
        """Test auth_status handles exceptions gracefully."""
        with patch.object(server.subscription, "get_auth_status", new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = Exception("Authentication failed")
            result = await server.auth_status()

            assert "Error" in result
            assert "Authentication failed" in result


class TestAccountShow:
    """Tests for the account_show tool."""

    @pytest.mark.asyncio
    async def test_account_show_success(self):
        """Test account_show returns account information."""
        with patch.object(server.subscription, "get_account_info", new_callable=AsyncMock) as mock_account:
            mock_account.return_value = "Azure Account:\nSubscription: my-sub\nTenant: my-tenant"
            result = await server.account_show()

            assert "Error" not in result
            mock_account.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_show_handles_exception(self):
        """Test account_show handles exceptions gracefully."""
        with patch.object(server.subscription, "get_account_info", new_callable=AsyncMock) as mock_account:
            mock_account.side_effect = Exception("Not authenticated")
            result = await server.account_show()

            assert "Error" in result
            assert "Not authenticated" in result


class TestAccountClear:
    """Tests for the account_clear tool."""

    @pytest.mark.asyncio
    async def test_account_clear_success(self):
        """Test account_clear clears cached state."""
        with patch.object(server.subscription, "clear_account", new_callable=AsyncMock) as mock_clear:
            mock_clear.return_value = "Azure account cache cleared successfully."
            result = await server.account_clear()

            assert "Error" not in result
            mock_clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_clear_handles_exception(self):
        """Test account_clear handles exceptions gracefully."""
        with patch.object(server.subscription, "clear_account", new_callable=AsyncMock) as mock_clear:
            mock_clear.side_effect = Exception("Failed to clear")
            result = await server.account_clear()

            assert "Error" in result
            assert "Failed to clear" in result


class TestAccountGetAccessToken:
    """Tests for the account_get_access_token tool."""

    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        """Test account_get_access_token returns token info."""
        with patch.object(server.subscription, "get_access_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = (
                "Azure Access Token:\nToken (masked): eyJ0eXAi...abcd\nExpires On: 2026-02-10T00:00:00"
            )
            result = await server.account_get_access_token()

            assert "Error" not in result
            mock_token.assert_called_once_with("https://management.azure.com/.default")

    @pytest.mark.asyncio
    async def test_get_access_token_custom_resource(self):
        """Test account_get_access_token with a custom resource/scope."""
        with patch.object(server.subscription, "get_access_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = "Azure Access Token:\nResource: https://vault.azure.net/.default"
            result = await server.account_get_access_token("https://vault.azure.net/.default")

            assert "Error" not in result
            mock_token.assert_called_once_with("https://vault.azure.net/.default")

    @pytest.mark.asyncio
    async def test_get_access_token_handles_exception(self):
        """Test account_get_access_token handles exceptions gracefully."""
        with patch.object(server.subscription, "get_access_token", new_callable=AsyncMock) as mock_token:
            mock_token.side_effect = Exception("Not authenticated")
            result = await server.account_get_access_token()

            assert "Error" in result
            assert "Not authenticated" in result


class TestListSubscriptions:
    """Tests for the list_subscriptions tool."""

    @pytest.mark.asyncio
    async def test_list_subscriptions_success(self):
        """Test list_subscriptions returns subscription list."""
        with patch.object(server.subscription, "list_subscriptions", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure Subscriptions:\n1. sub-1\n2. sub-2"
            result = await server.list_subscriptions()

            assert "Error" not in result
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_subscriptions_handles_exception(self):
        """Test list_subscriptions handles exceptions gracefully."""
        with patch.object(server.subscription, "list_subscriptions", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Failed to list subscriptions")
            result = await server.list_subscriptions()

            assert "Error" in result
            assert "Failed to list subscriptions" in result


class TestListLocations:
    """Tests for the list_locations tool."""

    @pytest.mark.asyncio
    async def test_list_locations_success(self):
        """Test list_locations returns locations."""
        with patch.object(server.subscription, "list_locations", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure Locations:\n- eastus\n- westus\n- westeurope"
            result = await server.list_locations()

            assert "Error" not in result
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_locations_handles_exception(self):
        """Test list_locations handles exceptions gracefully."""
        with patch.object(server.subscription, "list_locations", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Failed to list locations")
            result = await server.list_locations()

            assert "Error" in result
            assert "Failed to list locations" in result


class TestListTenants:
    """Tests for the list_tenants tool."""

    @pytest.mark.asyncio
    async def test_list_tenants_success(self):
        """Test list_tenants returns tenant information."""
        with patch.object(server.subscription, "get_tenant_info", new_callable=AsyncMock) as mock_tenant:
            mock_tenant.return_value = "Azure Tenants:\n- tenant-id-1\n- tenant-id-2"
            result = await server.list_tenants()

            assert "Error" not in result
            mock_tenant.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tenants_handles_exception(self):
        """Test list_tenants handles exceptions gracefully."""
        with patch.object(server.subscription, "get_tenant_info", new_callable=AsyncMock) as mock_tenant:
            mock_tenant.side_effect = Exception("Failed to get tenant info")
            result = await server.list_tenants()

            assert "Error" in result
            assert "Failed to get tenant info" in result


class TestSetSubscription:
    """Tests for the set_subscription tool."""

    @pytest.mark.asyncio
    async def test_set_subscription_success(self):
        """Test set_subscription configures subscription."""
        with patch.object(server.subscription, "configure_subscription", new_callable=AsyncMock) as mock_set:
            mock_set.return_value = "Subscription set to: 12345678-1234-1234-1234-123456789012"
            result = await server.set_subscription("12345678-1234-1234-1234-123456789012")

            assert "Error" not in result
            mock_set.assert_called_once_with("12345678-1234-1234-1234-123456789012")

    @pytest.mark.asyncio
    async def test_set_subscription_empty_id(self):
        """Test set_subscription with empty ID returns error."""
        result = await server.set_subscription("")
        assert "Error" in result
