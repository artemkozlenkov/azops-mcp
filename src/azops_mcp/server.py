#!/usr/bin/env python3
"""Azure Infrastructure MCP Server - Core platform tools for Azure management.
"""

import logging
import signal
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from .config import config
from .tools import cloud

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=config.get_log_level(),
    format=config.log_format,
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MCP instance
# ---------------------------------------------------------------------------

mcp = FastMCP("azops-mcp")


# =============================================================================
# FREE TIER — always registered
# =============================================================================


# -- 1. Health & Status -------------------------------------------------------


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


# -- 2. Subscription & Authentication -----------------------------------------


@mcp.tool()
async def list_subscriptions() -> str:
    """List all Azure subscriptions you have access to."""
    logger.info("list_subscriptions called")
    try:
        return await cloud.list_subscriptions()
    except Exception as e:
        logger.error("list_subscriptions failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def set_subscription(subscription_id: str) -> str:
    """Set the Azure subscription to use for this session.

    Args:
        subscription_id: Azure subscription ID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    """
    logger.info("set_subscription: %s", subscription_id)
    if not subscription_id:
        return "Error: subscription_id is required"
    try:
        return await cloud.configure_subscription(subscription_id)
    except Exception as e:
        logger.error("set_subscription failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def auth_status() -> str:
    """Check Azure authentication status and method (CLI or Service Principal)."""
    logger.info("auth_status called")
    try:
        return await cloud.get_auth_status()
    except Exception as e:
        logger.error("auth_status failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def account_show() -> str:
    """Get details of the current Azure subscription (similar to 'az account show')."""
    logger.info("account_show called")
    try:
        return await cloud.get_account_info()
    except Exception as e:
        logger.error("account_show failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def account_clear() -> str:
    """Clear cached Azure credentials and subscription override (similar to 'az account clear').

    Resets in-memory subscription override and cached SDK clients so the next
    operation re-authenticates from scratch.
    """
    logger.info("account_clear called")
    try:
        return await cloud.clear_account()
    except Exception as e:
        logger.error("account_clear failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def account_get_access_token(resource: str = "https://management.azure.com/.default") -> str:
    """Get an Azure access token for utilities to access Azure (similar to 'az account get-access-token').

    Args:
        resource: The resource/scope to obtain a token for (default: Azure Resource Manager)
    """
    logger.info("account_get_access_token: resource=%s", resource)
    try:
        return await cloud.get_access_token(resource)
    except Exception as e:
        logger.error("account_get_access_token failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def list_locations() -> str:
    """List all Azure regions available for the subscription."""
    logger.info("list_locations called")
    try:
        return await cloud.list_locations()
    except Exception as e:
        logger.error("list_locations failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def list_tenants() -> str:
    """List Azure AD tenants you have access to."""
    logger.info("list_tenants called")
    try:
        return await cloud.get_tenant_info()
    except Exception as e:
        logger.error("list_tenants failed: %s", e)
        return f"Error: {e}"


# -- 3. Management Groups (read) ----------------------------------------------


@mcp.tool()
async def list_management_groups() -> str:
    """List all Azure management groups."""
    logger.info("list_management_groups called")
    try:
        return await cloud.list_management_groups()
    except Exception as e:
        logger.error("list_management_groups failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def get_management_group(group_id: str) -> str:
    """Get details of a management group including its children.

    Args:
        group_id: Management group ID
    """
    logger.info("get_management_group: %s", group_id)
    if not group_id:
        return "Error: group_id is required"
    try:
        return await cloud.get_management_group(group_id)
    except Exception as e:
        logger.error("get_management_group failed: %s", e)
        return f"Error: {e}"


# -- 4. RBAC (read) -----------------------------------------------------------


@mcp.tool()
async def list_role_definitions() -> str:
    """List available Azure role definitions (built-in roles)."""
    logger.info("list_role_definitions called")
    try:
        return await cloud.list_role_definitions()
    except Exception as e:
        logger.error("list_role_definitions failed: %s", e)
        return f"Error: {e}"


# -- 5. Resource Locks (read) -------------------------------------------------


@mcp.tool()
async def list_resource_locks(resource_group: str = "") -> str:
    """List resource locks in subscription or resource group.

    Args:
        resource_group: Optional resource group to filter by
    """
    logger.info("list_resource_locks: %s", resource_group or "subscription")
    try:
        rg = resource_group if resource_group else None
        return await cloud.list_resource_locks(rg)
    except Exception as e:
        logger.error("list_resource_locks failed: %s", e)
        return f"Error: {e}"


# -- 6. Tags (read) -----------------------------------------------------------


@mcp.tool()
async def list_tags(resource_group: str = "") -> str:
    """List tags in subscription or on a resource group.

    Args:
        resource_group: Optional resource group to get tags from
    """
    logger.info("list_tags: %s", resource_group or "subscription")
    try:
        rg = resource_group if resource_group else None
        return await cloud.list_tags(rg)
    except Exception as e:
        logger.error("list_tags failed: %s", e)
        return f"Error: {e}"


# -- 7. Activity Log ----------------------------------------------------------


@mcp.tool()
async def get_activity_log(resource_group: str = "", days: int = 1) -> str:
    """Get recent Azure activity log (audit log).

    Args:
        resource_group: Optional resource group to filter by
        days: Days to look back (1-7, default 1)
    """
    logger.info("get_activity_log: %s, days=%d", resource_group or "subscription", days)
    try:
        rg = resource_group if resource_group else None
        return await cloud.get_activity_log(rg, days)
    except Exception as e:
        logger.error("get_activity_log failed: %s", e)
        return f"Error: {e}"


# -- 8. Resource Groups (read) ------------------------------------------------


@mcp.tool()
async def list_resource_groups() -> str:
    """List all resource groups in the subscription."""
    logger.info("list_resource_groups called")
    try:
        return await cloud.list_resource_groups()
    except Exception as e:
        logger.error("list_resource_groups failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def list_resources(resource_group: str, resource_type: str = "all") -> str:
    """List resources in a resource group.

    Args:
        resource_group: Resource group name
        resource_type: Filter by type (all, vm, storage)
    """
    logger.info("list_resources: %s, type=%s", resource_group, resource_type)
    if not resource_group:
        return "Error: resource_group is required"
    try:
        return await cloud.list_resources(resource_group, resource_type)
    except Exception as e:
        logger.error("list_resources failed: %s", e)
        return f"Error: {e}"


# -- 9. Virtual Machines -------------------------------------------------------


@mcp.tool()
async def list_vms(resource_group: str) -> str:
    """List virtual machines in a resource group.

    Args:
        resource_group: Resource group name
    """
    logger.info("list_vms: %s", resource_group)
    if not resource_group:
        return "Error: resource_group is required"
    try:
        return await cloud.list_resources(resource_group, "vm")
    except Exception as e:
        logger.error("list_vms failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def get_vm_status(resource_group: str, vm_name: str) -> str:
    """Get detailed status of a virtual machine.

    Args:
        resource_group: Resource group name
        vm_name: Virtual machine name
    """
    logger.info("get_vm_status: %s/%s", resource_group, vm_name)
    if not resource_group or not vm_name:
        return "Error: resource_group and vm_name are required"
    try:
        return await cloud.get_resource_status(resource_group, vm_name, "vm")
    except Exception as e:
        logger.error("get_vm_status failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def start_vm(resource_group: str, vm_name: str) -> str:
    """Start a virtual machine.

    Args:
        resource_group: Resource group name
        vm_name: Virtual machine name
    """
    logger.info("start_vm: %s/%s", resource_group, vm_name)
    if not resource_group or not vm_name:
        return "Error: resource_group and vm_name are required"
    try:
        return await cloud.manage_vm(resource_group, vm_name, "start")
    except Exception as e:
        logger.error("start_vm failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def stop_vm(resource_group: str, vm_name: str) -> str:
    """Stop a virtual machine (VM stays allocated, charges continue).

    Args:
        resource_group: Resource group name
        vm_name: Virtual machine name
    """
    logger.info("stop_vm: %s/%s", resource_group, vm_name)
    if not resource_group or not vm_name:
        return "Error: resource_group and vm_name are required"
    try:
        return await cloud.manage_vm(resource_group, vm_name, "stop")
    except Exception as e:
        logger.error("stop_vm failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def restart_vm(resource_group: str, vm_name: str) -> str:
    """Restart a virtual machine.

    Args:
        resource_group: Resource group name
        vm_name: Virtual machine name
    """
    logger.info("restart_vm: %s/%s", resource_group, vm_name)
    if not resource_group or not vm_name:
        return "Error: resource_group and vm_name are required"
    try:
        return await cloud.manage_vm(resource_group, vm_name, "restart")
    except Exception as e:
        logger.error("restart_vm failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def deallocate_vm(resource_group: str, vm_name: str) -> str:
    """Deallocate a VM (stops and releases compute, no charges).

    Args:
        resource_group: Resource group name
        vm_name: Virtual machine name
    """
    logger.info("deallocate_vm: %s/%s", resource_group, vm_name)
    if not resource_group or not vm_name:
        return "Error: resource_group and vm_name are required"
    try:
        return await cloud.manage_vm(resource_group, vm_name, "deallocate")
    except Exception as e:
        logger.error("deallocate_vm failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def scale_vmss(resource_group: str, vmss_name: str, capacity: int) -> str:
    """Scale a Virtual Machine Scale Set.

    Args:
        resource_group: Resource group name
        vmss_name: VM Scale Set name
        capacity: Target instance count (0+)
    """
    logger.info("scale_vmss: %s/%s to %d", resource_group, vmss_name, capacity)
    if not resource_group or not vmss_name:
        return "Error: resource_group and vmss_name are required"
    if not isinstance(capacity, int) or capacity < 0:
        return "Error: capacity must be a non-negative integer"
    try:
        return await cloud.scale_vmss(resource_group, vmss_name, capacity)
    except Exception as e:
        logger.error("scale_vmss failed: %s", e)
        return f"Error: {e}"


# -- 10. Storage Accounts -----------------------------------------------------


@mcp.tool()
async def list_storage_accounts(resource_group: str) -> str:
    """List storage accounts in a resource group.

    Args:
        resource_group: Resource group name
    """
    logger.info("list_storage_accounts: %s", resource_group)
    if not resource_group:
        return "Error: resource_group is required"
    try:
        return await cloud.list_resources(resource_group, "storage")
    except Exception as e:
        logger.error("list_storage_accounts failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def get_storage_status(resource_group: str, account_name: str) -> str:
    """Get status of a storage account.

    Args:
        resource_group: Resource group name
        account_name: Storage account name
    """
    logger.info("get_storage_status: %s/%s", resource_group, account_name)
    if not resource_group or not account_name:
        return "Error: resource_group and account_name are required"
    try:
        return await cloud.get_resource_status(resource_group, account_name, "storage")
    except Exception as e:
        logger.error("get_storage_status failed: %s", e)
        return f"Error: {e}"




# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """Start the Azure Infrastructure MCP Server."""
    logger.info("Starting Azure Infrastructure MCP Server...")

    def signal_handler(signum: int, frame: Optional[object]) -> None:
        logger.info("Shutting down (signal %d)...", signum)
        mcp.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error("Server error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
