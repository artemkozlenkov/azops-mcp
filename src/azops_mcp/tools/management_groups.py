"""Management group operations tools."""

import logging
from typing import Any, Optional

from ..utils.helpers import format_error_message
from ._clients import _get_management_group_client

logger = logging.getLogger(__name__)


async def list_management_groups() -> str:
    """List all management groups.

    Returns:
        Formatted list showing display_name, name/ID, type.
    """
    try:
        client = _get_management_group_client()
        groups = client.management_groups.list()

        formatted = []
        for group in groups:
            formatted.append(f"Display Name: {group.display_name or 'N/A'}\nName/ID: {group.name}\nType: {group.type}")

        if not formatted:
            return "No management groups found."

        return f"Management Groups ({len(formatted)} found):\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list management groups")
        logger.error(error_msg)
        return error_msg


async def get_management_group(group_id: str) -> str:
    """Get management group details with children.

    Args:
        group_id: Management group ID.

    Returns:
        Management group details including children (subscription vs management group).
    """
    try:
        client = _get_management_group_client()
        group = client.management_groups.get(group_id, expand="children")

        output = (
            f"Management Group:\n"
            f"{'=' * 50}\n"
            f"Display Name: {group.display_name or 'N/A'}\n"
            f"Name/ID: {group.name}\n"
            f"Type: {group.type}\n"
            f"Tenant ID: {group.tenant_id or 'N/A'}\n"
        )

        if group.children:
            output += f"\nChildren ({len(group.children)}):\n"
            for child in group.children:
                child_type = "Subscription" if child.type and "/subscriptions/" in child.type else "Management Group"
                output += f"  - {child.display_name or child.name} ({child_type})\n"
        else:
            output += "\nChildren: None\n"

        return output

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to get management group '{group_id}'")
        logger.error(error_msg)
        return error_msg


async def create_management_group(
    group_id: str,
    display_name: str,
    parent_id: Optional[str] = None,
) -> str:
    """Create a management group.

    Args:
        group_id: Unique ID for the management group.
        display_name: Display name for the management group.
        parent_id: Optional parent management group ID. If provided, set parent path.

    Returns:
        Result of the create operation.
    """
    try:
        client = _get_management_group_client()

        create_request: dict[str, Any] = {"display_name": display_name}
        if parent_id:
            create_request["parent_id"] = f"/providers/Microsoft.Management/managementGroups/{parent_id}"

        poller = client.management_groups.begin_create_or_update(group_id, create_request)
        result = poller.result()

        return (
            f"Management group created successfully!\n"
            f"{'=' * 50}\n"
            f"Display Name: {result.display_name or display_name}\n"
            f"ID: {result.name or group_id}\n"
            f"Type: {result.type}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to create management group '{group_id}'")
        logger.error(error_msg)
        return error_msg


async def delete_management_group(group_id: str) -> str:
    """Delete a management group.

    Note: Management group must be empty (no children) to be deleted.

    Args:
        group_id: Management group ID to delete.

    Returns:
        Confirmation message.
    """
    try:
        client = _get_management_group_client()
        poller = client.management_groups.begin_delete(group_id)
        poller.result()

        return f"Management group '{group_id}' deleted successfully."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to delete management group '{group_id}'")
        logger.error(error_msg)
        return error_msg
