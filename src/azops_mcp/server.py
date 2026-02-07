#!/usr/bin/env python3
"""Azure Infrastructure MCP Server - Core platform tools for Azure management."""

import logging
import sys
import signal
from datetime import datetime
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from .tools import cloud
from .config import config

# Configure logging
logging.basicConfig(
    level=config.get_log_level(),
    format=config.log_format,
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)
mcp = FastMCP("azops-mcp")


# =============================================================================
# 1. HEALTH & STATUS
# =============================================================================

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Check MCP server health and Azure SDK availability."""
    try:
        deps = {}
        for pkg, path in [
            ("azure-identity", "azure.identity"),
            ("azure-mgmt-compute", "azure.mgmt.compute"),
            ("azure-mgmt-resource", "azure.mgmt.resource"),
            ("azure-mgmt-storage", "azure.mgmt.storage"),
            ("azure-mgmt-subscription", "azure.mgmt.subscription"),
            ("azure-mgmt-managementgroups", "azure.mgmt.managementgroups"),
        ]:
            try:
                __import__(path)
                deps[pkg] = "ok"
            except ImportError:
                deps[pkg] = "missing"

        return {
            "status": "healthy",
            "dependencies": deps,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# =============================================================================
# 2. SUBSCRIPTION & AUTHENTICATION (5 tools)
# =============================================================================

@mcp.tool()
async def list_subscriptions() -> str:
    """List all Azure subscriptions you have access to."""
    logger.info("list_subscriptions called")
    try:
        return await cloud.list_subscriptions()
    except Exception as e:
        logger.error(f"list_subscriptions failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def set_subscription(subscription_id: str) -> str:
    """Set the Azure subscription to use for this session.

    Args:
        subscription_id: Azure subscription ID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    """
    logger.info(f"set_subscription: {subscription_id}")
    if not subscription_id:
        return "Error: subscription_id is required"
    try:
        return await cloud.configure_subscription(subscription_id)
    except Exception as e:
        logger.error(f"set_subscription failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def auth_status() -> str:
    """Check Azure authentication status and method (CLI or Service Principal)."""
    logger.info("auth_status called")
    try:
        return await cloud.get_auth_status()
    except Exception as e:
        logger.error(f"auth_status failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def list_locations() -> str:
    """List all Azure regions available for the subscription."""
    logger.info("list_locations called")
    try:
        return await cloud.list_locations()
    except Exception as e:
        logger.error(f"list_locations failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def list_tenants() -> str:
    """List Azure AD tenants you have access to."""
    logger.info("list_tenants called")
    try:
        return await cloud.get_tenant_info()
    except Exception as e:
        logger.error(f"list_tenants failed: {e}")
        return f"Error: {str(e)}"


# =============================================================================
# 3. MANAGEMENT GROUPS (4 tools)
# =============================================================================

@mcp.tool()
async def list_management_groups() -> str:
    """List all Azure management groups."""
    logger.info("list_management_groups called")
    try:
        return await cloud.list_management_groups()
    except Exception as e:
        logger.error(f"list_management_groups failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def get_management_group(group_id: str) -> str:
    """Get details of a management group including its children.

    Args:
        group_id: Management group ID
    """
    logger.info(f"get_management_group: {group_id}")
    if not group_id:
        return "Error: group_id is required"
    try:
        return await cloud.get_management_group(group_id)
    except Exception as e:
        logger.error(f"get_management_group failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def create_management_group(group_id: str, display_name: str, parent_id: str = "") -> str:
    """Create a new management group.

    Args:
        group_id: Unique ID for the management group
        display_name: Display name
        parent_id: Optional parent management group ID
    """
    logger.info(f"create_management_group: {group_id}")
    if not group_id or not display_name:
        return "Error: group_id and display_name are required"
    try:
        parent = parent_id if parent_id else None
        return await cloud.create_management_group(group_id, display_name, parent)
    except Exception as e:
        logger.error(f"create_management_group failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def delete_management_group(group_id: str) -> str:
    """Delete a management group (must be empty).

    Args:
        group_id: Management group ID to delete
    """
    logger.info(f"delete_management_group: {group_id}")
    if not group_id:
        return "Error: group_id is required"
    try:
        return await cloud.delete_management_group(group_id)
    except Exception as e:
        logger.error(f"delete_management_group failed: {e}")
        return f"Error: {str(e)}"


# =============================================================================
# 4. RBAC - ROLE ASSIGNMENTS (2 tools)
# =============================================================================

@mcp.tool()
async def list_role_assignments(resource_group: str = "") -> str:
    """List role assignments (RBAC) for subscription or resource group.

    Args:
        resource_group: Optional resource group to filter by
    """
    logger.info(f"list_role_assignments: {resource_group or 'subscription'}")
    try:
        rg = resource_group if resource_group else None
        return await cloud.list_role_assignments(rg)
    except Exception as e:
        logger.error(f"list_role_assignments failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def list_role_definitions() -> str:
    """List available Azure role definitions (built-in roles)."""
    logger.info("list_role_definitions called")
    try:
        return await cloud.list_role_definitions()
    except Exception as e:
        logger.error(f"list_role_definitions failed: {e}")
        return f"Error: {str(e)}"


# =============================================================================
# 5. RESOURCE LOCKS (3 tools)
# =============================================================================

@mcp.tool()
async def list_resource_locks(resource_group: str = "") -> str:
    """List resource locks in subscription or resource group.

    Args:
        resource_group: Optional resource group to filter by
    """
    logger.info(f"list_resource_locks: {resource_group or 'subscription'}")
    try:
        rg = resource_group if resource_group else None
        return await cloud.list_resource_locks(rg)
    except Exception as e:
        logger.error(f"list_resource_locks failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def create_resource_lock(resource_group: str, lock_name: str, lock_level: str = "CanNotDelete") -> str:
    """Create a lock on a resource group to prevent deletion or modification.

    Args:
        resource_group: Resource group to lock
        lock_name: Name for the lock
        lock_level: CanNotDelete (default) or ReadOnly
    """
    logger.info(f"create_resource_lock: {resource_group}/{lock_name}")
    if not resource_group or not lock_name:
        return "Error: resource_group and lock_name are required"
    try:
        return await cloud.create_resource_lock(resource_group, lock_name, lock_level)
    except Exception as e:
        logger.error(f"create_resource_lock failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def delete_resource_lock(resource_group: str, lock_name: str) -> str:
    """Delete a resource lock from a resource group.

    Args:
        resource_group: Resource group containing the lock
        lock_name: Name of the lock to delete
    """
    logger.info(f"delete_resource_lock: {resource_group}/{lock_name}")
    if not resource_group or not lock_name:
        return "Error: resource_group and lock_name are required"
    try:
        return await cloud.delete_resource_lock(resource_group, lock_name)
    except Exception as e:
        logger.error(f"delete_resource_lock failed: {e}")
        return f"Error: {str(e)}"


# =============================================================================
# 6. TAGS (2 tools)
# =============================================================================

@mcp.tool()
async def list_tags(resource_group: str = "") -> str:
    """List tags in subscription or on a resource group.

    Args:
        resource_group: Optional resource group to get tags from
    """
    logger.info(f"list_tags: {resource_group or 'subscription'}")
    try:
        rg = resource_group if resource_group else None
        return await cloud.list_tags(rg)
    except Exception as e:
        logger.error(f"list_tags failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def set_resource_group_tags(resource_group: str, tags: str) -> str:
    """Set tags on a resource group. Format: key1=value1,key2=value2

    Args:
        resource_group: Resource group to tag
        tags: Tags in format key1=value1,key2=value2
    """
    logger.info(f"set_resource_group_tags: {resource_group}")
    if not resource_group or not tags:
        return "Error: resource_group and tags are required"
    try:
        # Parse tags string
        tag_dict = {}
        for pair in tags.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                tag_dict[k.strip()] = v.strip()
        
        if not tag_dict:
            return "Error: Invalid tags format. Use key1=value1,key2=value2"
        
        return await cloud.update_resource_group_tags(resource_group, tag_dict, merge=True)
    except Exception as e:
        logger.error(f"set_resource_group_tags failed: {e}")
        return f"Error: {str(e)}"


# =============================================================================
# 7. ACTIVITY LOG (1 tool)
# =============================================================================

@mcp.tool()
async def get_activity_log(resource_group: str = "", days: int = 1) -> str:
    """Get recent Azure activity log (audit log).

    Args:
        resource_group: Optional resource group to filter by
        days: Days to look back (1-7, default 1)
    """
    logger.info(f"get_activity_log: {resource_group or 'subscription'}, days={days}")
    try:
        rg = resource_group if resource_group else None
        return await cloud.get_activity_log(rg, days)
    except Exception as e:
        logger.error(f"get_activity_log failed: {e}")
        return f"Error: {str(e)}"


# =============================================================================
# 8. RESOURCE GROUPS (3 tools)
# =============================================================================

@mcp.tool()
async def list_resource_groups() -> str:
    """List all resource groups in the subscription."""
    logger.info("list_resource_groups called")
    try:
        return await cloud.list_resource_groups()
    except Exception as e:
        logger.error(f"list_resource_groups failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def create_resource_group(name: str, location: str) -> str:
    """Create a new Azure resource group.

    Args:
        name: Resource group name (e.g., my-app-rg)
        location: Azure region (e.g., eastus, westeurope)
    """
    logger.info(f"create_resource_group: {name} in {location}")
    if not name or not location:
        return "Error: name and location are required"
    try:
        return await cloud.create_resource_group(name, location)
    except Exception as e:
        logger.error(f"create_resource_group failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def delete_resource_group(name: str) -> str:
    """Delete a resource group and ALL its resources. WARNING: Irreversible!

    Args:
        name: Resource group name to delete
    """
    logger.info(f"delete_resource_group: {name}")
    if not name:
        return "Error: name is required"
    try:
        return await cloud.delete_resource_group(name)
    except Exception as e:
        logger.error(f"delete_resource_group failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def list_resources(resource_group: str, resource_type: str = "all") -> str:
    """List resources in a resource group.

    Args:
        resource_group: Resource group name
        resource_type: Filter by type (all, vm, storage)
    """
    logger.info(f"list_resources: {resource_group}, type={resource_type}")
    if not resource_group:
        return "Error: resource_group is required"
    try:
        return await cloud.list_resources(resource_group, resource_type)
    except Exception as e:
        logger.error(f"list_resources failed: {e}")
        return f"Error: {str(e)}"


# =============================================================================
# 9. VIRTUAL MACHINES (7 tools)
# =============================================================================

@mcp.tool()
async def list_vms(resource_group: str) -> str:
    """List virtual machines in a resource group.

    Args:
        resource_group: Resource group name
    """
    logger.info(f"list_vms: {resource_group}")
    if not resource_group:
        return "Error: resource_group is required"
    try:
        return await cloud.list_resources(resource_group, "vm")
    except Exception as e:
        logger.error(f"list_vms failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def get_vm_status(resource_group: str, vm_name: str) -> str:
    """Get detailed status of a virtual machine.

    Args:
        resource_group: Resource group name
        vm_name: Virtual machine name
    """
    logger.info(f"get_vm_status: {resource_group}/{vm_name}")
    if not resource_group or not vm_name:
        return "Error: resource_group and vm_name are required"
    try:
        return await cloud.get_resource_status(resource_group, vm_name, "vm")
    except Exception as e:
        logger.error(f"get_vm_status failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def start_vm(resource_group: str, vm_name: str) -> str:
    """Start a virtual machine.

    Args:
        resource_group: Resource group name
        vm_name: Virtual machine name
    """
    logger.info(f"start_vm: {resource_group}/{vm_name}")
    if not resource_group or not vm_name:
        return "Error: resource_group and vm_name are required"
    try:
        return await cloud.manage_vm(resource_group, vm_name, "start")
    except Exception as e:
        logger.error(f"start_vm failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def stop_vm(resource_group: str, vm_name: str) -> str:
    """Stop a virtual machine (VM stays allocated, charges continue).

    Args:
        resource_group: Resource group name
        vm_name: Virtual machine name
    """
    logger.info(f"stop_vm: {resource_group}/{vm_name}")
    if not resource_group or not vm_name:
        return "Error: resource_group and vm_name are required"
    try:
        return await cloud.manage_vm(resource_group, vm_name, "stop")
    except Exception as e:
        logger.error(f"stop_vm failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def restart_vm(resource_group: str, vm_name: str) -> str:
    """Restart a virtual machine.

    Args:
        resource_group: Resource group name
        vm_name: Virtual machine name
    """
    logger.info(f"restart_vm: {resource_group}/{vm_name}")
    if not resource_group or not vm_name:
        return "Error: resource_group and vm_name are required"
    try:
        return await cloud.manage_vm(resource_group, vm_name, "restart")
    except Exception as e:
        logger.error(f"restart_vm failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def deallocate_vm(resource_group: str, vm_name: str) -> str:
    """Deallocate a VM (stops and releases compute, no charges).

    Args:
        resource_group: Resource group name
        vm_name: Virtual machine name
    """
    logger.info(f"deallocate_vm: {resource_group}/{vm_name}")
    if not resource_group or not vm_name:
        return "Error: resource_group and vm_name are required"
    try:
        return await cloud.manage_vm(resource_group, vm_name, "deallocate")
    except Exception as e:
        logger.error(f"deallocate_vm failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def scale_vmss(resource_group: str, vmss_name: str, capacity: int) -> str:
    """Scale a Virtual Machine Scale Set.

    Args:
        resource_group: Resource group name
        vmss_name: VM Scale Set name
        capacity: Target instance count (0+)
    """
    logger.info(f"scale_vmss: {resource_group}/{vmss_name} to {capacity}")
    if not resource_group or not vmss_name:
        return "Error: resource_group and vmss_name are required"
    if not isinstance(capacity, int) or capacity < 0:
        return "Error: capacity must be a non-negative integer"
    try:
        return await cloud.scale_vmss(resource_group, vmss_name, capacity)
    except Exception as e:
        logger.error(f"scale_vmss failed: {e}")
        return f"Error: {str(e)}"


# =============================================================================
# 10. STORAGE ACCOUNTS (2 tools)
# =============================================================================

@mcp.tool()
async def list_storage_accounts(resource_group: str) -> str:
    """List storage accounts in a resource group.

    Args:
        resource_group: Resource group name
    """
    logger.info(f"list_storage_accounts: {resource_group}")
    if not resource_group:
        return "Error: resource_group is required"
    try:
        return await cloud.list_resources(resource_group, "storage")
    except Exception as e:
        logger.error(f"list_storage_accounts failed: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
async def get_storage_status(resource_group: str, account_name: str) -> str:
    """Get status of a storage account.

    Args:
        resource_group: Resource group name
        account_name: Storage account name
    """
    logger.info(f"get_storage_status: {resource_group}/{account_name}")
    if not resource_group or not account_name:
        return "Error: resource_group and account_name are required"
    try:
        return await cloud.get_resource_status(resource_group, account_name, "storage")
    except Exception as e:
        logger.error(f"get_storage_status failed: {e}")
        return f"Error: {str(e)}"


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    """Start the Azure Infrastructure MCP Server."""
    logger.info("Starting Azure Infrastructure MCP Server...")

    def signal_handler(signum: int, frame: Optional[object]) -> None:
        logger.info(f"Shutting down (signal {signum})...")
        mcp.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
