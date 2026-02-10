"""Tests for RBAC authorization tools."""

from unittest.mock import AsyncMock, patch

import pytest

from azops_mcp import server


class TestListRoleDefinitions:
    """Tests for the list_role_definitions tool."""

    @pytest.mark.asyncio
    async def test_list_role_definitions_success(self):
        """Test list_role_definitions returns roles."""
        with patch.object(server.authorization, "list_role_definitions", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = "Built-in Roles:\n- Contributor\n- Reader"
            result = await server.list_role_definitions()

            assert "Error" not in result
            mock_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_role_definitions_handles_exception(self):
        """Test list_role_definitions handles exceptions gracefully."""
        with patch.object(server.authorization, "list_role_definitions", new_callable=AsyncMock) as mock_list:
            mock_list.side_effect = Exception("Authorization SDK not available")
            result = await server.list_role_definitions()

            assert "Error" in result


class TestCreateRoleAssignment:
    """Tests for the create_role_assignment tool."""

    @pytest.mark.asyncio
    async def test_create_role_assignment_success(self):
        """Test create_role_assignment creates an assignment."""
        with patch.object(server.authorization, "create_role_assignment", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "Role assignment created:\nRole: Contributor"
            result = await server.create_role_assignment("principal-id", "Contributor", "my-rg")

            assert "Error" not in result
            mock_create.assert_called_once_with("principal-id", "Contributor", "my-rg", "")

    @pytest.mark.asyncio
    async def test_create_role_assignment_missing_principal(self):
        """Test create_role_assignment with missing principal returns error."""
        result = await server.create_role_assignment("", "Contributor")
        assert "Error" in result


class TestDeleteRoleAssignment:
    """Tests for the delete_role_assignment tool."""

    @pytest.mark.asyncio
    async def test_delete_role_assignment_success(self):
        """Test delete_role_assignment deletes an assignment."""
        with patch.object(server.authorization, "delete_role_assignment", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = "Role assignment deleted."
            result = await server.delete_role_assignment("assignment-id")

            assert "Error" not in result
            mock_delete.assert_called_once_with("assignment-id")

    @pytest.mark.asyncio
    async def test_delete_role_assignment_missing_id(self):
        """Test delete_role_assignment with missing ID returns error."""
        result = await server.delete_role_assignment("")
        assert "Error" in result


class TestListRoleAssignmentsForPrincipal:
    """Tests for the list_role_assignments_for_principal tool."""

    @pytest.mark.asyncio
    async def test_list_assignments_success(self):
        """Test list_role_assignments_for_principal returns assignments."""
        with patch.object(
            server.authorization, "list_role_assignments_for_principal", new_callable=AsyncMock
        ) as mock_list:
            mock_list.return_value = "Role Assignments:\n- Contributor on my-rg"
            result = await server.list_role_assignments_for_principal("principal-id")

            assert "Error" not in result
            mock_list.assert_called_once_with("principal-id", "")

    @pytest.mark.asyncio
    async def test_list_assignments_missing_principal(self):
        """Test list_role_assignments_for_principal with missing principal returns error."""
        result = await server.list_role_assignments_for_principal("")
        assert "Error" in result
