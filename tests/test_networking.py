"""Tests for networking tools (VNets, subnets, peerings)."""

from unittest.mock import AsyncMock, patch

import pytest

from azops_mcp import server


class TestVnetList:
    """Tests for the vnet_list tool."""

    @pytest.mark.asyncio
    async def test_vnet_list_success(self):
        """Test vnet_list returns VNets."""
        with patch.object(server.networking, "vnet_list", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Virtual Networks:\n- my-vnet (10.0.0.0/16)"
            result = await server.vnet_list("my-rg")

            assert "Error" not in result
            mock_list.assert_called_once_with("my-rg")

    @pytest.mark.asyncio
    async def test_vnet_list_handles_exception(self):
        """Test vnet_list handles exceptions gracefully."""
        with patch.object(server.networking, "vnet_list", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Network SDK not available")
            result = await server.vnet_list("")

            assert "Error" in result


class TestVnetShow:
    """Tests for the vnet_show tool."""

    @pytest.mark.asyncio
    async def test_vnet_show_success(self):
        """Test vnet_show returns VNet details."""
        with patch.object(server.networking, "vnet_show", new_callable=AsyncMock) as mock_show:
            mock_show.return_value = "VNet: my-vnet\nAddress Space: 10.0.0.0/16"
            result = await server.vnet_show("my-vnet", "my-rg")

            assert "Error" not in result
            mock_show.assert_called_once_with("my-vnet", "my-rg")

    @pytest.mark.asyncio
    async def test_vnet_show_missing_params(self):
        """Test vnet_show with missing params returns error."""
        result = await server.vnet_show("", "my-rg")
        assert "Error" in result


class TestVnetCreate:
    """Tests for the vnet_create tool."""

    @pytest.mark.asyncio
    async def test_vnet_create_success(self):
        """Test vnet_create creates a VNet."""
        with patch.object(server.networking, "vnet_create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "VNet 'my-vnet' created in 'eastus'"
            result = await server.vnet_create("my-vnet", "my-rg", "10.0.0.0/16")

            assert "Error" not in result
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_vnet_create_missing_params(self):
        """Test vnet_create with missing params returns error."""
        result = await server.vnet_create("", "my-rg")
        assert "Error" in result


class TestVnetSubnetList:
    """Tests for the vnet_subnet_list tool."""

    @pytest.mark.asyncio
    async def test_subnet_list_success(self):
        """Test vnet_subnet_list returns subnets."""
        with patch.object(server.networking, "vnet_subnet_list", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Subnets:\n- default (10.0.0.0/24)"
            result = await server.vnet_subnet_list("my-vnet", "my-rg")

            assert "Error" not in result
            mock_list.assert_called_once_with("my-vnet", "my-rg")


class TestVnetSubnetCreate:
    """Tests for the vnet_subnet_create tool."""

    @pytest.mark.asyncio
    async def test_subnet_create_success(self):
        """Test vnet_subnet_create creates a subnet."""
        with patch.object(server.networking, "vnet_subnet_create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "Subnet 'web-tier' created"
            result = await server.vnet_subnet_create("my-vnet", "web-tier", "my-rg", "10.0.1.0/24")

            assert "Error" not in result
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_subnet_create_missing_params(self):
        """Test vnet_subnet_create with missing params returns error."""
        result = await server.vnet_subnet_create("", "web-tier", "my-rg", "10.0.1.0/24")
        assert "Error" in result


class TestVnetPeeringList:
    """Tests for the vnet_peering_list tool."""

    @pytest.mark.asyncio
    async def test_peering_list_success(self):
        """Test vnet_peering_list returns peerings."""
        with patch.object(server.networking, "vnet_peering_list", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "No peerings found."
            result = await server.vnet_peering_list("my-vnet", "my-rg")

            assert "Error" not in result
            mock_list.assert_called_once_with("my-vnet", "my-rg")
