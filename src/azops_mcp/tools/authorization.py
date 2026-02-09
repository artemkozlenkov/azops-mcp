"""RBAC (Role-Based Access Control) management tools."""

import logging
import uuid
from typing import Optional

from ..utils.helpers import format_error_message
from ._clients import _get_authorization_client, get_subscription_id

logger = logging.getLogger(__name__)


async def list_role_assignments(resource_group: Optional[str] = None) -> str:
    """List role assignments for the subscription or a resource group.

    Args:
        resource_group: Optional resource group to filter by. If provided, use list_for_scope.

    Returns:
        Formatted list of role assignments (limited to 20).
    """
    try:
        authorization_client = _get_authorization_client()
        subscription_id = get_subscription_id()

        if not subscription_id:
            return "Error: Subscription ID not configured. Use azure_set_subscription to set it."

        if resource_group:
            scope = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
            assignments = authorization_client.role_assignments.list_for_scope(scope)
        else:
            assignments = authorization_client.role_assignments.list_for_subscription()

        formatted = []
        for assignment in assignments:
            principal_id = assignment.principal_id or "N/A"
            principal_type = assignment.principal_type or "N/A"
            role_id = assignment.role_definition_id.split("/")[-1] if assignment.role_definition_id else "N/A"
            formatted.append(
                f"Principal: {principal_id} ({principal_type})\n"
                f"Role Definition ID: {role_id}\n"
                f"Scope: {assignment.scope}\n"
                f"Assignment ID: {assignment.id}"
            )

        if not formatted:
            return "No role assignments found."

        limited = formatted[:20]
        suffix = f" (showing first 20 of {len(formatted)})" if len(formatted) > 20 else ""
        return f"Role Assignments{suffix}:\n\n" + "\n---\n".join(limited)

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list role assignments")
        logger.error(error_msg)
        return error_msg


async def list_role_definitions() -> str:
    """List built-in role definitions.

    Returns:
        Formatted list of built-in roles (first 15).
    """
    try:
        authorization_client = _get_authorization_client()
        subscription_id = get_subscription_id()

        if not subscription_id:
            return "Error: Subscription ID not configured."

        scope = f"/subscriptions/{subscription_id}"
        roles = authorization_client.role_definitions.list(scope)

        formatted = []
        for role in roles:
            if role.role_type == "BuiltInRole":
                desc = (role.description[:100] + "...") if role.description else "N/A"
                formatted.append(f"Name: {role.role_name}\nID: {role.name}\nDescription: {desc}")

        if not formatted:
            return "No built-in role definitions found."

        limited = formatted[:15]
        suffix = f" (showing first 15 of {len(formatted)})" if len(formatted) > 15 else ""
        return f"Built-in Role Definitions{suffix}:\n\n" + "\n---\n".join(limited)

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list role definitions")
        logger.error(error_msg)
        return error_msg


async def create_role_assignment(
    principal_id: str,
    role_definition_name: str,
    resource_group: Optional[str] = None,
    scope: Optional[str] = None,
) -> str:
    """Create a role assignment.

    Args:
        principal_id: Object ID of the principal (user, group, or service principal).
        role_definition_name: Role name (e.g., 'Contributor', 'Reader', 'AcrPull').
        resource_group: Optional resource group scope. Uses subscription if not provided.
        scope: Full resource scope. Overrides resource_group if provided.

    Returns:
        Result of the role assignment creation.
    """
    try:
        from azure.mgmt.authorization.models import RoleAssignmentCreateParameters

        authorization_client = _get_authorization_client()
        subscription_id = get_subscription_id()

        if not subscription_id:
            return "Error: Subscription ID not configured."

        if scope:
            target_scope = scope
        elif resource_group:
            target_scope = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        else:
            target_scope = f"/subscriptions/{subscription_id}"

        roles = authorization_client.role_definitions.list(target_scope)
        role_def_id = None

        for role_def in roles:
            if role_def.role_name == role_definition_name:
                role_def_id = role_def.id
                break

        if not role_def_id:
            return (
                f"Error: Role '{role_definition_name}' not found at scope '{target_scope}'. "
                "Use list_role_definitions to see available roles."
            )

        assignment_name = str(uuid.uuid4())
        assignment_params = RoleAssignmentCreateParameters(
            role_definition_id=role_def_id,
            principal_id=principal_id,
            principal_type="ServicePrincipal",
        )

        authorization_client.role_assignments.create(target_scope, assignment_name, assignment_params)

        return (
            f"Role assignment created successfully!\n"
            f"{'=' * 60}\n"
            f"Principal ID: {principal_id}\n"
            f"Role: {role_definition_name}\n"
            f"Scope: {target_scope}\n"
            f"Assignment ID: {assignment_name}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to create role assignment for principal '{principal_id}'")
        logger.error(error_msg)
        return error_msg


async def delete_role_assignment(assignment_id: str) -> str:
    """Delete a role assignment by assignment ID.

    Args:
        assignment_id: Full role assignment ID (resource path).

    Returns:
        Confirmation message.
    """
    try:
        authorization_client = _get_authorization_client()

        parts = assignment_id.split("/")
        if len(parts) < 9:
            return "Error: Invalid assignment_id format. Expected full resource path."

        assignment_name = parts[-1]
        scope = "/".join(parts[:-1])

        authorization_client.role_assignments.delete(scope, assignment_name)

        return f"Role assignment '{assignment_id}' deleted successfully."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to delete role assignment '{assignment_id}'")
        logger.error(error_msg)
        return error_msg


async def list_role_assignments_for_principal(
    principal_id: str,
    resource_group: Optional[str] = None,
) -> str:
    """List role assignments for a specific principal.

    Args:
        principal_id: Object ID of the principal.
        resource_group: Optional resource group to filter by.

    Returns:
        Formatted list of role assignments for the principal.
    """
    try:
        authorization_client = _get_authorization_client()
        subscription_id = get_subscription_id()

        if not subscription_id:
            return "Error: Subscription ID not configured."

        if resource_group:
            scope = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
            assignments = authorization_client.role_assignments.list_for_scope(scope)
        else:
            assignments = authorization_client.role_assignments.list_for_subscription()

        filtered = [a for a in assignments if a.principal_id == principal_id]

        if not filtered:
            return f"No role assignments found for principal '{principal_id}'."

        formatted = []
        for assignment in filtered:
            role_id = assignment.role_definition_id.split("/")[-1] if assignment.role_definition_id else "N/A"
            formatted.append(
                f"Scope: {assignment.scope}\n"
                f"Role ID: {role_id}\n"
                f"Principal: {principal_id}\n"
                f"Assignment ID: {assignment.id}"
            )

        return f"Role Assignments for Principal '{principal_id}':\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to list role assignments for principal '{principal_id}'")
        logger.error(error_msg)
        return error_msg
