"""Tests for compute tools (VMs, VMSS, resources)."""

import pytest
from unittest.mock import AsyncMock, patch

from azops_mcp import server


class TestListResources:
    """Tests for the list_resources tool."""

    @pytest.mark.asyncio
    async def test_list_resources_with_valid_resource_group(self):
        """Test list_resources with valid resource group."""
        with patch.object(server.compute, "list_resources", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure Resources in 'my-rg':\n..."
            result = await server.list_resources("my-rg", "all")

            assert "Error" not in result
            mock_list.assert_called_once_with("my-rg", "all")

    @pytest.mark.asyncio
    async def test_list_resources_with_empty_resource_group(self):
        """Test list_resources with empty resource_group returns error."""
        result = await server.list_resources("", "all")
        assert "Error" in result
        assert "resource_group" in result.lower()

    @pytest.mark.asyncio
    async def test_list_resources_handles_exception(self):
        """Test list_resources handles exceptions gracefully."""
        with patch.object(server.compute, "list_resources", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Connection failed")
            result = await server.list_resources("my-rg", "all")

            assert "Error" in result
            assert "Connection failed" in result


class TestGetVmStatus:
    """Tests for the get_vm_status tool."""

    @pytest.mark.asyncio
    async def test_get_vm_status_with_valid_inputs(self):
        """Test get_vm_status with valid inputs."""
        with patch.object(server.compute, "get_resource_status", new_callable=AsyncMock) as mock_status:
            mock_status.return_value = "Azure VM Status:\nName: my-vm\nStatus: running"
            result = await server.get_vm_status("my-rg", "my-vm")

            assert "Error" not in result
            mock_status.assert_called_once_with("my-rg", "my-vm", "vm")

    @pytest.mark.asyncio
    async def test_get_vm_status_with_empty_resource_group(self):
        """Test get_vm_status with empty resource_group returns error."""
        result = await server.get_vm_status("", "my-vm")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_get_vm_status_with_empty_vm_name(self):
        """Test get_vm_status with empty vm_name returns error."""
        result = await server.get_vm_status("my-rg", "")
        assert "Error" in result


class TestStartVm:
    """Tests for the start_vm tool."""

    @pytest.mark.asyncio
    async def test_start_vm_success(self):
        """Test start_vm with valid inputs."""
        with patch.object(server.compute, "manage_vm", new_callable=AsyncMock) as mock_manage:
            mock_manage.return_value = "VM 'my-vm' started successfully."
            result = await server.start_vm("my-rg", "my-vm")

            assert "Error" not in result
            mock_manage.assert_called_once_with("my-rg", "my-vm", "start")

    @pytest.mark.asyncio
    async def test_start_vm_with_empty_resource_group(self):
        """Test start_vm with empty resource_group returns error."""
        result = await server.start_vm("", "my-vm")
        assert "Error" in result

    @pytest.mark.asyncio
    async def test_start_vm_with_empty_vm_name(self):
        """Test start_vm with empty vm_name returns error."""
        result = await server.start_vm("my-rg", "")
        assert "Error" in result


class TestStopVm:
    """Tests for the stop_vm tool."""

    @pytest.mark.asyncio
    async def test_stop_vm_success(self):
        """Test stop_vm with valid inputs."""
        with patch.object(server.compute, "manage_vm", new_callable=AsyncMock) as mock_manage:
            mock_manage.return_value = "VM 'my-vm' stopped."
            result = await server.stop_vm("my-rg", "my-vm")

            assert "Error" not in result
            mock_manage.assert_called_once_with("my-rg", "my-vm", "stop")


class TestDeallocateVm:
    """Tests for the deallocate_vm tool."""

    @pytest.mark.asyncio
    async def test_deallocate_vm_success(self):
        """Test deallocate_vm with valid inputs."""
        with patch.object(server.compute, "manage_vm", new_callable=AsyncMock) as mock_manage:
            mock_manage.return_value = "VM 'my-vm' deallocated."
            result = await server.deallocate_vm("my-rg", "my-vm")

            assert "Error" not in result
            mock_manage.assert_called_once_with("my-rg", "my-vm", "deallocate")


class TestScaleVmss:
    """Tests for the scale_vmss tool."""

    @pytest.mark.asyncio
    async def test_scale_vmss_with_valid_inputs(self):
        """Test scale_vmss with valid inputs."""
        with patch.object(server.compute, "scale_vmss", new_callable=AsyncMock) as mock_scale:
            mock_scale.return_value = "VMSS Scaling Complete:\nName: my-vmss\nNew Capacity: 5"
            result = await server.scale_vmss("my-rg", "my-vmss", 5)

            assert "Error" not in result
            mock_scale.assert_called_once_with("my-rg", "my-vmss", 5)

    @pytest.mark.asyncio
    async def test_scale_vmss_with_negative_capacity(self):
        """Test scale_vmss with negative capacity returns error."""
        result = await server.scale_vmss("my-rg", "my-vmss", -1)
        assert "Error" in result
        assert "non-negative" in result.lower()

    @pytest.mark.asyncio
    async def test_scale_vmss_with_zero_capacity(self):
        """Test scale_vmss with zero capacity is allowed."""
        with patch.object(server.compute, "scale_vmss", new_callable=AsyncMock) as mock_scale:
            mock_scale.return_value = "VMSS Scaling Complete:\nName: my-vmss\nNew Capacity: 0"
            result = await server.scale_vmss("my-rg", "my-vmss", 0)

            assert "Error" not in result
            mock_scale.assert_called_once_with("my-rg", "my-vmss", 0)

    @pytest.mark.asyncio
    async def test_scale_vmss_with_empty_resource_group(self):
        """Test scale_vmss with empty resource_group returns error."""
        result = await server.scale_vmss("", "my-vmss", 5)
        assert "Error" in result
        assert "resource_group" in result.lower()

    @pytest.mark.asyncio
    async def test_scale_vmss_with_empty_vmss_name(self):
        """Test scale_vmss with empty vmss_name returns error."""
        result = await server.scale_vmss("my-rg", "", 5)
        assert "Error" in result
        assert "vmss_name" in result.lower()


class TestListStorageAccounts:
    """Tests for the list_storage_accounts tool."""

    @pytest.mark.asyncio
    async def test_list_storage_accounts_success(self):
        """Test list_storage_accounts with valid resource group."""
        with patch.object(server.compute, "list_resources", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Storage Accounts:\n..."
            result = await server.list_storage_accounts("my-rg")

            assert "Error" not in result
            mock_list.assert_called_once_with("my-rg", "storage")

    @pytest.mark.asyncio
    async def test_list_storage_accounts_empty_rg(self):
        """Test list_storage_accounts with empty resource_group returns error."""
        result = await server.list_storage_accounts("")
        assert "Error" in result


class TestGetStorageStatus:
    """Tests for the get_storage_status tool."""

    @pytest.mark.asyncio
    async def test_get_storage_status_success(self):
        """Test get_storage_status with valid inputs."""
        with patch.object(server.compute, "get_resource_status", new_callable=AsyncMock) as mock_status:
            mock_status.return_value = "Storage Account Status:\n..."
            result = await server.get_storage_status("my-rg", "myaccount")

            assert "Error" not in result
            mock_status.assert_called_once_with("my-rg", "myaccount", "storage")

    @pytest.mark.asyncio
    async def test_get_storage_status_empty_inputs(self):
        """Test get_storage_status with empty inputs returns error."""
        result = await server.get_storage_status("", "myaccount")
        assert "Error" in result
