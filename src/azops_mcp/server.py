#!/usr/bin/env python3
"""Azure Infrastructure MCP Server - Core platform tools for Azure management.

Tools are split into two tiers:

  FREE   — read-only / operational tools, always registered.
  PREMIUM — write / mutating tools, registered only when the license
            server grants the corresponding feature flag.

On startup the server validates AUTH_TOKEN against LICENSE_API_URL.
If validation fails (or no token is set), only free-tier tools appear
in the MCP ``tools/list`` response — premium tools are invisible.
"""

import logging
import signal
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

from .config import config
from .tools import cloud
from .utils.auth import get_licensed_features, validate_license

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

        license_info = validate_license()
        return {
            "status": "healthy",
            "dependencies": deps,
            "license_tier": license_info.get("tier", "free"),
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
# PREMIUM TIER — conditionally registered based on license features
# =============================================================================


def _register_premium_tools() -> None:
    """Register premium tools whose feature flags are present in the license.

    Called once at module-load time.  If the license server is unreachable
    or the token is invalid, no premium tools are registered and the MCP
    client never sees them.
    """
    features = get_licensed_features()

    if not features:
        logger.info("No premium features licensed — only free-tier tools available")
        return

    logger.info("Registering premium tools for features: %s", features)

    # -- Resource Groups (write) -----------------------------------------------

    if "rg_write" in features:

        @mcp.tool()
        async def create_resource_group(name: str, location: str) -> str:
            """Create a new Azure resource group.

            Args:
                name: Resource group name (e.g., my-app-rg)
                location: Azure region (e.g., eastus, westeurope)
            """
            logger.info("create_resource_group: %s in %s", name, location)
            if not name or not location:
                return "Error: name and location are required"
            try:
                return await cloud.create_resource_group(name, location)
            except Exception as e:
                logger.error("create_resource_group failed: %s", e)
                return f"Error: {e}"

        @mcp.tool()
        async def delete_resource_group(name: str) -> str:
            """Delete a resource group and ALL its resources. WARNING: Irreversible!

            Args:
                name: Resource group name to delete
            """
            logger.info("delete_resource_group: %s", name)
            if not name:
                return "Error: name is required"
            try:
                return await cloud.delete_resource_group(name)
            except Exception as e:
                logger.error("delete_resource_group failed: %s", e)
                return f"Error: {e}"

    # -- RBAC ------------------------------------------------------------------

    if "rbac" in features:

        @mcp.tool()
        async def list_role_assignments(resource_group: str = "") -> str:
            """List role assignments (RBAC) for subscription or resource group.

            Args:
                resource_group: Optional resource group to filter by
            """
            logger.info("list_role_assignments: %s", resource_group or "subscription")
            try:
                rg = resource_group if resource_group else None
                return await cloud.list_role_assignments(rg)
            except Exception as e:
                logger.error("list_role_assignments failed: %s", e)
                return f"Error: {e}"

    # -- Resource Locks (write) ------------------------------------------------

    if "locks_write" in features:

        @mcp.tool()
        async def create_resource_lock(resource_group: str, lock_name: str, lock_level: str = "CanNotDelete") -> str:
            """Create a lock on a resource group to prevent deletion or modification.

            Args:
                resource_group: Resource group to lock
                lock_name: Name for the lock
                lock_level: CanNotDelete (default) or ReadOnly
            """
            logger.info("create_resource_lock: %s/%s", resource_group, lock_name)
            if not resource_group or not lock_name:
                return "Error: resource_group and lock_name are required"
            try:
                return await cloud.create_resource_lock(resource_group, lock_name, lock_level)
            except Exception as e:
                logger.error("create_resource_lock failed: %s", e)
                return f"Error: {e}"

        @mcp.tool()
        async def delete_resource_lock(resource_group: str, lock_name: str) -> str:
            """Delete a resource lock from a resource group.

            Args:
                resource_group: Resource group containing the lock
                lock_name: Name of the lock to delete
            """
            logger.info("delete_resource_lock: %s/%s", resource_group, lock_name)
            if not resource_group or not lock_name:
                return "Error: resource_group and lock_name are required"
            try:
                return await cloud.delete_resource_lock(resource_group, lock_name)
            except Exception as e:
                logger.error("delete_resource_lock failed: %s", e)
                return f"Error: {e}"

    # -- Tags (write) ----------------------------------------------------------

    if "tags_write" in features:

        @mcp.tool()
        async def set_resource_group_tags(resource_group: str, tags: str) -> str:
            """Set tags on a resource group. Format: key1=value1,key2=value2

            Args:
                resource_group: Resource group to tag
                tags: Tags in format key1=value1,key2=value2
            """
            logger.info("set_resource_group_tags: %s", resource_group)
            if not resource_group or not tags:
                return "Error: resource_group and tags are required"
            try:
                tag_dict = {}
                for pair in tags.split(","):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        tag_dict[k.strip()] = v.strip()
                if not tag_dict:
                    return "Error: Invalid tags format. Use key1=value1,key2=value2"
                return await cloud.update_resource_group_tags(resource_group, tag_dict, merge=True)
            except Exception as e:
                logger.error("set_resource_group_tags failed: %s", e)
                return f"Error: {e}"

    # -- Management Groups (write) ---------------------------------------------

    if "mg_write" in features:

        @mcp.tool()
        async def create_management_group(group_id: str, display_name: str, parent_id: str = "") -> str:
            """Create a new management group.

            Args:
                group_id: Unique ID for the management group
                display_name: Display name
                parent_id: Optional parent management group ID
            """
            logger.info("create_management_group: %s", group_id)
            if not group_id or not display_name:
                return "Error: group_id and display_name are required"
            try:
                parent = parent_id if parent_id else None
                return await cloud.create_management_group(group_id, display_name, parent)
            except Exception as e:
                logger.error("create_management_group failed: %s", e)
                return f"Error: {e}"

        @mcp.tool()
        async def delete_management_group(group_id: str) -> str:
            """Delete a management group (must be empty).

            Args:
                group_id: Management group ID to delete
            """
            logger.info("delete_management_group: %s", group_id)
            if not group_id:
                return "Error: group_id is required"
            try:
                return await cloud.delete_management_group(group_id)
            except Exception as e:
                logger.error("delete_management_group failed: %s", e)
                return f"Error: {e}"


# Run conditional registration at import time
_register_premium_tools()


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
