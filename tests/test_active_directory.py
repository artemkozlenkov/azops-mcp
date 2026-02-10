"""Tests for Azure AD (Entra ID) tools."""

from unittest.mock import AsyncMock, patch

import pytest

from azops_mcp import server


class TestAadListUsers:
    """Tests for the aad_list_users tool."""

    @pytest.mark.asyncio
    async def test_list_users_success(self):
        """Test aad_list_users returns users."""
        with patch.object(server.active_directory, "list_users", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure AD Users (2 found):\n..."
            result = await server.aad_list_users("", 50)

            assert "Error" not in result
            mock_list.assert_called_once_with("", 50)

    @pytest.mark.asyncio
    async def test_list_users_with_filter(self):
        """Test aad_list_users with OData filter."""
        with patch.object(server.active_directory, "list_users", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure AD Users (1 found):\n..."
            result = await server.aad_list_users("displayName eq 'John'", 10)

            assert "Error" not in result
            mock_list.assert_called_once_with("displayName eq 'John'", 10)

    @pytest.mark.asyncio
    async def test_list_users_handles_exception(self):
        """Test aad_list_users handles exceptions gracefully."""
        with patch.object(server.active_directory, "list_users", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Graph API error")
            result = await server.aad_list_users()

            assert "Error" in result


class TestAadShowUser:
    """Tests for the aad_show_user tool."""

    @pytest.mark.asyncio
    async def test_show_user_by_id(self):
        """Test aad_show_user with user ID."""
        with patch.object(server.active_directory, "show_user", new_callable=AsyncMock) as mock_show:
            mock_show.return_value = "Azure AD User:\nDisplay Name: John Doe"
            result = await server.aad_show_user("user-object-id")

            assert "Error" not in result
            mock_show.assert_called_once_with("user-object-id", "")

    @pytest.mark.asyncio
    async def test_show_user_missing_params(self):
        """Test aad_show_user with missing params returns error."""
        result = await server.aad_show_user("", "")
        assert "Error" in result


class TestAadCreateUser:
    """Tests for the aad_create_user tool."""

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test aad_create_user creates a user."""
        with patch.object(server.active_directory, "create_user", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "User created successfully!"
            result = await server.aad_create_user("John Doe", "john@contoso.com", "P@ssw0rd!")

            assert "Error" not in result
            mock_create.assert_called_once()


class TestAadDeleteUser:
    """Tests for the aad_delete_user tool."""

    @pytest.mark.asyncio
    async def test_delete_user_success(self):
        """Test aad_delete_user deletes a user."""
        with patch.object(server.active_directory, "delete_user", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = "User 'user-id' deleted successfully."
            result = await server.aad_delete_user("user-id")

            assert "Error" not in result
            mock_delete.assert_called_once_with("user-id", "")


class TestAadListApplications:
    """Tests for the aad_list_applications tool."""

    @pytest.mark.asyncio
    async def test_list_applications_success(self):
        """Test aad_list_applications returns apps."""
        with patch.object(server.active_directory, "list_applications", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure AD Applications (3 found):\n..."
            result = await server.aad_list_applications()

            assert "Error" not in result
            mock_list.assert_called_once()


class TestAadListGroups:
    """Tests for the aad_list_groups tool."""

    @pytest.mark.asyncio
    async def test_list_groups_success(self):
        """Test aad_list_groups returns groups."""
        with patch.object(server.active_directory, "list_groups", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Azure AD Groups (2 found):\n..."
            result = await server.aad_list_groups()

            assert "Error" not in result
            mock_list.assert_called_once()


class TestAadVerifyTenant:
    """Tests for the aad_verify_tenant tool."""

    @pytest.mark.asyncio
    async def test_verify_tenant_success(self):
        """Test aad_verify_tenant returns tenant info."""
        with patch.object(server.active_directory, "verify_tenant", new_callable=AsyncMock) as mock_verify:
            mock_verify.return_value = "Azure AD Tenant Information:\nTenant ID: abc-123"
            result = await server.aad_verify_tenant()

            assert "Error" not in result
            mock_verify.assert_called_once()


class TestAadResetClient:
    """Tests for the aad_reset_client tool."""

    @pytest.mark.asyncio
    async def test_reset_client_success(self):
        """Test aad_reset_client clears client cache."""
        with patch.object(server.active_directory, "reset_aad_client") as mock_reset:
            result = await server.aad_reset_client()

            assert "Error" not in result
            assert "cleared" in result.lower()
            mock_reset.assert_called_once()
