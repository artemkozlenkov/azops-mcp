"""Unit tests for the MCP server tools."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Import the server module
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


class TestAuthStatus:
    """Tests for the auth_status tool."""

    @pytest.mark.asyncio
    async def test_auth_status_success(self):
        """Test auth_status returns authentication status."""
        with patch.object(server.cloud, "get_auth_status", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = "Azure Authentication Status:\nMethod: Azure CLI\nStatus: Authenticated"
            result = await server.auth_status()

            assert "Error" not in result
            mock_auth.assert_called_once()

    @pytest.mark.asyncio
    async def test_auth_status_handles_exception(self):
        """Test auth_status handles exceptions gracefully."""
        with patch.object(server.cloud, "get_auth_status", new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = Exception("Authentication failed")
            result = await server.auth_status()

            assert "Error" in result
            assert "Authentication failed" in result


class TestAccountShow:
    """Tests for the account_show tool."""

    @pytest.mark.asyncio
    async def test_account_show_success(self):
        """Test account_show returns account information."""
        with patch.object(server.cloud, "get_account_info", new_callable=AsyncMock) as mock_account:
            mock_account.return_value = "Azure Account:\nSubscription: my-sub\nTenant: my-tenant"
            result = await server.account_show()

            assert "Error" not in result
            mock_account.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_show_handles_exception(self):
        """Test account_show handles exceptions gracefully."""
        with patch.object(server.cloud, "get_account_info", new_callable=AsyncMock) as mock_account:
            mock_account.side_effect = Exception("Not authenticated")
            result = await server.account_show()

            assert "Error" in result
            assert "Not authenticated" in result


class TestAccountClear:
    """Tests for the account_clear tool."""

    @pytest.mark.asyncio
    async def test_account_clear_success(self):
        """Test account_clear clears cached state."""
        with patch.object(server.cloud, "clear_account", new_callable=AsyncMock) as mock_clear:
            mock_clear.return_value = "Azure account cache cleared successfully."
            result = await server.account_clear()

            assert "Error" not in result
            mock_clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_clear_handles_exception(self):
        """Test account_clear handles exceptions gracefully."""
        with patch.object(server.cloud, "clear_account", new_callable=AsyncMock) as mock_clear:
            mock_clear.side_effect = Exception("Failed to clear")
            result = await server.account_clear()

            assert "Error" in result
            assert "Failed to clear" in result


class TestAccountGetAccessToken:
    """Tests for the account_get_access_token tool."""

    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        """Test account_get_access_token returns token info."""
        with patch.object(server.cloud, "get_access_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = (
                "Azure Access Token:\nToken (masked): eyJ0eXAi...abcd\nExpires On: 2026-02-10T00:00:00"
            )
            result = await server.account_get_access_token()

            assert "Error" not in result
            mock_token.assert_called_once_with("https://management.azure.com/.default")

    @pytest.mark.asyncio
    async def test_get_access_token_custom_resource(self):
        """Test account_get_access_token with a custom resource/scope."""
        with patch.object(server.cloud, "get_access_token", new_callable=AsyncMock) as mock_token:
            mock_token.return_value = "Azure Access Token:\nResource: https://vault.azure.net/.default"
            result = await server.account_get_access_token("https://vault.azure.net/.default")

            assert "Error" not in result
            mock_token.assert_called_once_with("https://vault.azure.net/.default")

    @pytest.mark.asyncio
    async def test_get_access_token_handles_exception(self):
        """Test account_get_access_token handles exceptions gracefully."""
        with patch.object(server.cloud, "get_access_token", new_callable=AsyncMock) as mock_token:
            mock_token.side_effect = Exception("Not authenticated")
            result = await server.account_get_access_token()

            assert "Error" in result
            assert "Not authenticated" in result


class TestListSubscriptions:
    """Tests for the list_subscriptions tool."""

    @pytest.mark.asyncio
    async def test_list_subscriptions_success(self):
        """Test list_subscriptions returns subscription list."""
        with patch.object(server.cloud, "list_subscriptions", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure Subscriptions:\n1. sub-1\n2. sub-2"
            result = await server.list_subscriptions()

            assert "Error" not in result
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_subscriptions_handles_exception(self):
        """Test list_subscriptions handles exceptions gracefully."""
        with patch.object(server.cloud, "list_subscriptions", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Failed to list subscriptions")
            result = await server.list_subscriptions()

            assert "Error" in result
            assert "Failed to list subscriptions" in result


class TestListLocations:
    """Tests for the list_locations tool."""

    @pytest.mark.asyncio
    async def test_list_locations_success(self):
        """Test list_locations returns locations."""
        with patch.object(server.cloud, "list_locations", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure Locations:\n- eastus\n- westus\n- westeurope"
            result = await server.list_locations()

            assert "Error" not in result
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_locations_handles_exception(self):
        """Test list_locations handles exceptions gracefully."""
        with patch.object(server.cloud, "list_locations", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Failed to list locations")
            result = await server.list_locations()

            assert "Error" in result
            assert "Failed to list locations" in result


class TestListTenants:
    """Tests for the list_tenants tool."""

    @pytest.mark.asyncio
    async def test_list_tenants_success(self):
        """Test list_tenants returns tenant information."""
        with patch.object(server.cloud, "get_tenant_info", new_callable=AsyncMock) as mock_tenant:
            mock_tenant.return_value = "Azure Tenants:\n- tenant-id-1\n- tenant-id-2"
            result = await server.list_tenants()

            assert "Error" not in result
            mock_tenant.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tenants_handles_exception(self):
        """Test list_tenants handles exceptions gracefully."""
        with patch.object(server.cloud, "get_tenant_info", new_callable=AsyncMock) as mock_tenant:
            mock_tenant.side_effect = Exception("Failed to get tenant info")
            result = await server.list_tenants()

            assert "Error" in result
            assert "Failed to get tenant info" in result


class TestAzureListResourceGroups:
    """Tests for the azure_list_resource_groups tool."""

    @pytest.mark.asyncio
    async def test_list_resource_groups_success(self):
        """Test azure_list_resource_groups returns resource groups."""
        with patch.object(server.cloud, "list_resource_groups", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure Resource Groups:\n..."
            result = await server.azure_list_resource_groups()

            assert "Error" not in result
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_resource_groups_handles_exception(self):
        """Test azure_list_resource_groups handles exceptions gracefully."""
        with patch.object(server.cloud, "list_resource_groups", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Azure SDK not installed")
            result = await server.azure_list_resource_groups()

            assert "Error" in result
            assert "Azure SDK" in result


class TestAzureListResources:
    """Tests for the azure_list_resources tool."""

    @pytest.mark.asyncio
    async def test_list_resources_with_valid_resource_group(self):
        """Test azure_list_resources with valid resource group."""
        with patch.object(server.cloud, "list_resources", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure Resources in 'my-rg':\n..."
            result = await server.azure_list_resources("my-rg", "all")

            assert "Error" not in result
            mock_list.assert_called_once_with("my-rg", "all")

    @pytest.mark.asyncio
    async def test_list_resources_with_empty_resource_group(self):
        """Test azure_list_resources with empty resource_group returns error."""
        result = await server.azure_list_resources("", "all")
        assert "Error" in result
        assert "resource_group" in result.lower()

    @pytest.mark.asyncio
    async def test_list_resources_handles_exception(self):
        """Test azure_list_resources handles exceptions gracefully."""
        with patch.object(server.cloud, "list_resources", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Connection failed")
            result = await server.azure_list_resources("my-rg", "all")

            assert "Error" in result
            assert "Connection failed" in result


class TestAzureGetResourceStatus:
    """Tests for the azure_get_resource_status tool."""

    @pytest.mark.asyncio
    async def test_get_resource_status_with_valid_inputs(self):
        """Test azure_get_resource_status with valid inputs."""
        with patch.object(server.cloud, "get_resource_status", new_callable=AsyncMock) as mock_status:
            mock_status.return_value = "Azure VM Status:\nName: my-vm\nStatus: running"
            result = await server.azure_get_resource_status("my-rg", "my-vm", "vm")

            assert "Error" not in result
            mock_status.assert_called_once_with("my-rg", "my-vm", "vm")

    @pytest.mark.asyncio
    async def test_get_resource_status_with_empty_resource_group(self):
        """Test azure_get_resource_status with empty resource_group returns error."""
        result = await server.azure_get_resource_status("", "my-vm", "vm")
        assert "Error" in result
        assert "resource_group" in result.lower()

    @pytest.mark.asyncio
    async def test_get_resource_status_with_empty_resource_name(self):
        """Test azure_get_resource_status with empty resource_name returns error."""
        result = await server.azure_get_resource_status("my-rg", "", "vm")
        assert "Error" in result
        assert "resource_name" in result.lower()


class TestAzureManageVM:
    """Tests for the azure_manage_vm tool."""

    @pytest.mark.asyncio
    async def test_manage_vm_start(self):
        """Test azure_manage_vm with start action."""
        with patch.object(server.cloud, "manage_vm", new_callable=AsyncMock) as mock_manage:
            mock_manage.return_value = "VM 'my-vm' started successfully."
            result = await server.azure_manage_vm("my-rg", "my-vm", "start")

            assert "Error" not in result
            mock_manage.assert_called_once_with("my-rg", "my-vm", "start")

    @pytest.mark.asyncio
    async def test_manage_vm_with_empty_resource_group(self):
        """Test azure_manage_vm with empty resource_group returns error."""
        result = await server.azure_manage_vm("", "my-vm", "start")
        assert "Error" in result
        assert "resource_group" in result.lower()

    @pytest.mark.asyncio
    async def test_manage_vm_with_empty_vm_name(self):
        """Test azure_manage_vm with empty vm_name returns error."""
        result = await server.azure_manage_vm("my-rg", "", "start")
        assert "Error" in result
        assert "vm_name" in result.lower()

    @pytest.mark.asyncio
    async def test_manage_vm_with_empty_action(self):
        """Test azure_manage_vm with empty action returns error."""
        result = await server.azure_manage_vm("my-rg", "my-vm", "")
        assert "Error" in result
        assert "action" in result.lower()


class TestAzureScaleVMSS:
    """Tests for the azure_scale_vmss tool."""

    @pytest.mark.asyncio
    async def test_scale_vmss_with_valid_inputs(self):
        """Test azure_scale_vmss with valid inputs."""
        with patch.object(server.cloud, "scale_vmss", new_callable=AsyncMock) as mock_scale:
            mock_scale.return_value = "VMSS Scaling Complete:\nName: my-vmss\nNew Capacity: 5"
            result = await server.azure_scale_vmss("my-rg", "my-vmss", 5)

            assert "Error" not in result
            mock_scale.assert_called_once_with("my-rg", "my-vmss", 5)

    @pytest.mark.asyncio
    async def test_scale_vmss_with_negative_capacity(self):
        """Test azure_scale_vmss with negative capacity returns error."""
        result = await server.azure_scale_vmss("my-rg", "my-vmss", -1)
        assert "Error" in result
        assert "non-negative" in result.lower()

    @pytest.mark.asyncio
    async def test_scale_vmss_with_zero_capacity(self):
        """Test azure_scale_vmss with zero capacity is allowed."""
        with patch.object(server.cloud, "scale_vmss", new_callable=AsyncMock) as mock_scale:
            mock_scale.return_value = "VMSS Scaling Complete:\nName: my-vmss\nNew Capacity: 0"
            result = await server.azure_scale_vmss("my-rg", "my-vmss", 0)

            assert "Error" not in result
            mock_scale.assert_called_once_with("my-rg", "my-vmss", 0)

    @pytest.mark.asyncio
    async def test_scale_vmss_with_empty_resource_group(self):
        """Test azure_scale_vmss with empty resource_group returns error."""
        result = await server.azure_scale_vmss("", "my-vmss", 5)
        assert "Error" in result
        assert "resource_group" in result.lower()

    @pytest.mark.asyncio
    async def test_scale_vmss_with_empty_vmss_name(self):
        """Test azure_scale_vmss with empty vmss_name returns error."""
        result = await server.azure_scale_vmss("my-rg", "", 5)
        assert "Error" in result
        assert "vmss_name" in result.lower()


class TestListContainers:
    """Tests for the list_containers tool."""

    @pytest.mark.asyncio
    async def test_list_containers_success(self):
        """Test list_containers returns container list."""
        with patch.object(server.containers, "list_containers", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Running Containers:\n..."
            result = await server.list_containers()

            assert "Error" not in result
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_containers_handles_exception(self):
        """Test list_containers handles exceptions gracefully."""
        with patch.object(server.containers, "list_containers", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Docker not available")
            result = await server.list_containers()

            assert "Error" in result
            assert "Docker not available" in result


class TestGetContainerLogs:
    """Tests for the get_container_logs tool."""

    @pytest.mark.asyncio
    async def test_get_container_logs_with_valid_inputs(self):
        """Test get_container_logs with valid inputs."""
        with patch.object(server.containers, "get_container_logs", new_callable=AsyncMock) as mock_logs:
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
        with patch.object(server.containers, "restart_container", new_callable=AsyncMock) as mock_restart:
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


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_check_rate_limit_allows_request(self):
        """Test that rate limiting allows requests within limit."""
        # Reset rate limit storage
        server.rate_limit_storage.clear()

        result = await server.check_rate_limit("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_blocks_when_exceeded(self):
        """Test that rate limiting blocks requests when limit exceeded."""
        # Reset rate limit storage
        server.rate_limit_storage.clear()

        # Temporarily lower the limit for testing
        original_limit = server.config.rate_limit_requests_per_minute
        server.config.rate_limit_requests_per_minute = 5

        try:
            # Make requests up to the limit
            for _ in range(5):
                await server.check_rate_limit("test_key_2")

            # Next request should be blocked
            result = await server.check_rate_limit("test_key_2")
            assert result is False
        finally:
            # Restore original limit
            server.config.rate_limit_requests_per_minute = original_limit

    @pytest.mark.asyncio
    async def test_check_rate_limit_disabled(self):
        """Test that rate limiting can be disabled."""
        # Temporarily disable rate limiting
        original_enabled = server.config.rate_limit_enabled
        server.config.rate_limit_enabled = False

        try:
            # Should always return True when disabled
            for _ in range(100):
                result = await server.check_rate_limit("test_key_3")
                assert result is True
        finally:
            # Restore original setting
            server.config.rate_limit_enabled = original_enabled
