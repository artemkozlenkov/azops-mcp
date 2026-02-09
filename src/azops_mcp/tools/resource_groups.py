"""Resource group management, tags, locks, and activity log tools."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ..utils.helpers import format_error_message
from ._clients import (
    _get_azure_credential,
    _get_resource_client,
    get_subscription_id,
)

logger = logging.getLogger(__name__)


async def list_resource_groups() -> str:
    """List all resource groups in the subscription.

    Returns:
        Formatted list of resource groups
    """
    try:
        resource_client = _get_resource_client()
        groups = resource_client.resource_groups.list()

        formatted_groups = []
        for group in groups:
            formatted_groups.append(
                f"Name: {group.name}\n"
                f"Location: {group.location}\n"
                f"Provisioning State: {group.properties.provisioning_state if group.properties else 'N/A'}"
            )

        if not formatted_groups:
            return "No resource groups found in the subscription."

        return "Azure Resource Groups:\n\n" + "\n---\n".join(formatted_groups)

    except ImportError as e:
        return format_error_message(e, "Failed to list resource groups")
    except Exception as e:
        logger.error("list_resource_groups failed: %s", e)
        return format_error_message(e, "Failed to list resource groups")


async def create_resource_group(
    name: str, location: str, tags: Optional[Dict[str, str]] = None
) -> str:
    """Create or update a resource group.

    Args:
        name: Name of the resource group
        location: Azure region (e.g., eastus, westeurope)
        tags: Optional dictionary of tags to apply

    Returns:
        Result of the create/update operation
    """
    try:
        resource_client = _get_resource_client()

        rg_params: Dict[str, Any] = {"location": location}
        if tags:
            rg_params["tags"] = tags

        result = resource_client.resource_groups.create_or_update(name, rg_params)

        return (
            f"Resource group created successfully!\n"
            f"{'='*50}\n"
            f"Name: {result.name}\n"
            f"Location: {result.location}\n"
            f"Provisioning State: {result.properties.provisioning_state if result.properties else 'N/A'}\n"
            f"ID: {result.id}"
        )

    except ImportError as e:
        return format_error_message(e, f"Failed to create resource group '{name}'")
    except Exception as e:
        logger.error("create_resource_group failed: %s", e)
        return format_error_message(e, f"Failed to create resource group '{name}'")


async def delete_resource_group(name: str) -> str:
    """Delete a resource group and all its resources.

    Args:
        name: Name of the resource group to delete

    Returns:
        Result of the delete operation
    """
    try:
        resource_client = _get_resource_client()
        poller = resource_client.resource_groups.begin_delete(name)
        poller.result()
        return f"Resource group '{name}' deleted successfully."

    except ImportError as e:
        return format_error_message(e, f"Failed to delete resource group '{name}'")
    except Exception as e:
        logger.error("delete_resource_group failed: %s", e)
        return format_error_message(e, f"Failed to delete resource group '{name}'")


async def list_tags(resource_group: Optional[str] = None) -> str:
    """List tags. If resource_group given, get tags from that RG. Otherwise list all tag names in subscription.

    Args:
        resource_group: Optional resource group to get tags from

    Returns:
        Formatted list of tags
    """
    try:
        resource_client = _get_resource_client()

        if resource_group:
            rg = resource_client.resource_groups.get(resource_group)
            tags = rg.tags or {}
            if not tags:
                return f"No tags found on resource group '{resource_group}'."
            formatted = [f"{k}: {v}" for k, v in tags.items()]
            return f"Tags on '{resource_group}':\n" + "\n".join(formatted)
        else:
            tags_list = resource_client.tags.list()
            formatted = []
            for tag in tags_list:
                values = [v.tag_value for v in (tag.values or [])][:5]
                formatted.append(
                    f"{tag.tag_name}: {', '.join(values) if values else '(no values)'}"
                )
            if not formatted:
                return "No tags found in subscription."
            return f"Tags in Subscription ({len(formatted)} found):\n" + "\n".join(formatted[:20])

    except ImportError as e:
        return format_error_message(e, "Failed to list tags")
    except Exception as e:
        logger.error("list_tags failed: %s", e)
        return format_error_message(e, "Failed to list tags")


async def update_resource_group_tags(
    resource_group: str, tags: Dict[str, str], merge: bool = True
) -> str:
    """Merge or replace tags on a resource group.

    Args:
        resource_group: Resource group to update
        tags: Dictionary of tags to set
        merge: If True, merge with existing. If False, replace all tags.

    Returns:
        Result of the update operation
    """
    try:
        resource_client = _get_resource_client()
        rg = resource_client.resource_groups.get(resource_group)

        if merge:
            existing_tags = rg.tags or {}
            existing_tags.update(tags)
            new_tags = existing_tags
        else:
            new_tags = tags

        rg.tags = new_tags
        result = resource_client.resource_groups.create_or_update(resource_group, rg)
        tag_list = [f"  {k}: {v}" for k, v in (result.tags or {}).items()]
        return f"Tags updated on '{resource_group}':\n" + "\n".join(tag_list)

    except ImportError as e:
        return format_error_message(e, f"Failed to update tags on '{resource_group}'")
    except Exception as e:
        logger.error("update_resource_group_tags failed: %s", e)
        return format_error_message(e, f"Failed to update tags on '{resource_group}'")


async def list_resource_locks(resource_group: Optional[str] = None) -> str:
    """List resource locks at RG level or subscription level.

    Args:
        resource_group: Optional resource group to filter by

    Returns:
        Formatted list of locks
    """
    try:
        resource_client = _get_resource_client()

        if resource_group:
            locks = resource_client.management_locks.list_at_resource_group_level(
                resource_group
            )
        else:
            locks = resource_client.management_locks.list_at_subscription_level()

        formatted = []
        for lock in locks:
            formatted.append(
                f"Name: {lock.name}\n"
                f"Level: {lock.level}\n"
                f"Notes: {lock.notes or 'N/A'}"
            )

        if not formatted:
            return "No resource locks found."
        return f"Resource Locks ({len(formatted)} found):\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return format_error_message(e, "Failed to list resource locks")
    except Exception as e:
        logger.error("list_resource_locks failed: %s", e)
        return format_error_message(e, "Failed to list resource locks")


async def create_resource_lock(
    resource_group: str,
    lock_name: str,
    lock_level: str = "CanNotDelete",
    notes: str = "",
) -> str:
    """Create a resource lock on a resource group.

    Args:
        resource_group: Resource group to lock
        lock_name: Name for the lock
        lock_level: CanNotDelete or ReadOnly
        notes: Optional notes about the lock

    Returns:
        Result of the create operation
    """
    try:
        if lock_level not in ["CanNotDelete", "ReadOnly"]:
            return "Error: lock_level must be 'CanNotDelete' or 'ReadOnly'"

        resource_client = _get_resource_client()
        lock_params = {"level": lock_level, "notes": notes or "Lock created via azops-mcp"}

        result = resource_client.management_locks.create_or_update_at_resource_group_level(
            resource_group, lock_name, lock_params
        )
        return (
            f"Resource lock created successfully!\n"
            f"Name: {result.name}\n"
            f"Level: {result.level}\n"
            f"Resource Group: {resource_group}"
        )

    except ImportError as e:
        return format_error_message(e, f"Failed to create lock '{lock_name}'")
    except Exception as e:
        logger.error("create_resource_lock failed: %s", e)
        return format_error_message(e, f"Failed to create lock '{lock_name}'")


async def delete_resource_lock(resource_group: str, lock_name: str) -> str:
    """Delete a resource lock from a resource group.

    Args:
        resource_group: Resource group containing the lock
        lock_name: Name of the lock to delete

    Returns:
        Result of the delete operation
    """
    try:
        resource_client = _get_resource_client()
        resource_client.management_locks.delete_at_resource_group_level(
            resource_group, lock_name
        )
        return f"Resource lock '{lock_name}' deleted from '{resource_group}'."

    except ImportError as e:
        return format_error_message(e, f"Failed to delete lock '{lock_name}'")
    except Exception as e:
        logger.error("delete_resource_lock failed: %s", e)
        return format_error_message(e, f"Failed to delete lock '{lock_name}'")


async def get_activity_log(resource_group: Optional[str] = None, days: int = 1) -> str:
    """Get recent Azure activity log (audit log).

    Args:
        resource_group: Optional resource group to filter by
        days: Days to look back (1-7, clamped)

    Returns:
        Recent activity log entries (limited to 20)
    """
    try:
        from azure.mgmt.monitor import MonitorManagementClient
    except ImportError:
        return format_error_message(
            ImportError("azure-mgmt-monitor not installed"),
            "Azure Monitor SDK not installed. Run: pip install azure-mgmt-monitor",
        )

    try:
        subscription_id = get_subscription_id()
        if not subscription_id:
            return "Error: Subscription ID not configured"

        monitor_client = MonitorManagementClient(
            credential=_get_azure_credential(),
            subscription_id=subscription_id,
        )

        days = min(max(days, 1), 7)
        start_time = datetime.utcnow() - timedelta(days=days)
        filter_str = f"eventTimestamp ge '{start_time.isoformat()}Z'"
        if resource_group:
            filter_str += f" and resourceGroupName eq '{resource_group}'"

        logs = monitor_client.activity_logs.list(filter=filter_str)
        formatted = []
        for log in logs:
            if len(formatted) >= 20:
                break
            timestamp = log.event_timestamp.isoformat() if log.event_timestamp else "N/A"
            formatted.append(
                f"Time: {timestamp}\n"
                f"Operation: {log.operation_name.localized_value if log.operation_name else 'N/A'}\n"
                f"Status: {log.status.localized_value if log.status else 'N/A'}\n"
                f"Caller: {log.caller or 'N/A'}"
            )

        if not formatted:
            return f"No activity log entries found in the last {days} day(s)."
        return (
            f"Activity Log (last {days} day(s), showing {len(formatted)} entries):\n\n"
            + "\n---\n".join(formatted)
        )

    except Exception as e:
        logger.error("get_activity_log failed: %s", e)
        return format_error_message(e, "Failed to get activity log")
