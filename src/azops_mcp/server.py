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
from .tools import acr, cloud

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
            ("azure-mgmt-appconfiguration", "azure.mgmt.appconfiguration"),
            ("azure-appconfiguration", "azure.appconfiguration"),
            ("azure-mgmt-web", "azure.mgmt.web"),
            ("azure-mgmt-network", "azure.mgmt.network"),
            ("azure-mgmt-containerregistry", "azure.mgmt.containerregistry"),
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


# -- 14. Azure Container Registry (ACR) --------------------------------------


@mcp.tool()
async def acr_list_registries(resource_group: str = "") -> str:
    """List container registries in a resource group or subscription.

    Args:
        resource_group: Optional resource group name to filter by
    """
    logger.info("acr_list_registries: %s", resource_group or "subscription")
    try:
        return await acr.acr_list_registries(resource_group)
    except Exception as e:
        logger.error("acr_list_registries failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_show_registry(resource_group: str, registry_name: str) -> str:
    """Get details of a container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
    """
    logger.info("acr_show_registry: %s/%s", resource_group, registry_name)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_show_registry(resource_group, registry_name)
    except Exception as e:
        logger.error("acr_show_registry failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_create_registry(
    resource_group: str,
    registry_name: str,
    location: str = "eastus",
    sku: str = "Basic",
    admin_enabled: bool = False,
) -> str:
    """Create a new container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry (must be unique across Azure)
        location: Azure region (default: eastus)
        sku: Sku tier - Basic, Standard, Premium (default: Basic)
        admin_enabled: Enable admin user (default: False)
    """
    logger.info("acr_create_registry: %s/%s sku=%s admin=%s", resource_group, registry_name, sku, admin_enabled)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_create_registry(resource_group, registry_name, location, sku, admin_enabled)
    except Exception as e:
        logger.error("acr_create_registry failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_delete_registry(resource_group: str, registry_name: str) -> str:
    """Delete a container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
    """
    logger.info("acr_delete_registry: %s/%s", resource_group, registry_name)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_delete_registry(resource_group, registry_name)
    except Exception as e:
        logger.error("acr_delete_registry failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_update_registry(
    resource_group: str,
    registry_name: str,
    admin_enabled: bool = None,
) -> str:
    """Update a container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        admin_enabled: Enable or disable admin user (optional)
    """
    logger.info("acr_update_registry: %s/%s admin=%s", resource_group, registry_name, admin_enabled)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_update_registry(resource_group, registry_name, admin_enabled, None)
    except Exception as e:
        logger.error("acr_update_registry failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_get_credentials(resource_group: str, registry_name: str) -> str:
    """Get login credentials for a container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
    """
    logger.info("acr_get_credentials: %s/%s", resource_group, registry_name)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_get_credentials(resource_group, registry_name)
    except Exception as e:
        logger.error("acr_get_credentials failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_get_login_server(resource_group: str, registry_name: str) -> str:
    """Get the login server URL for a container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
    """
    logger.info("acr_get_login_server: %s/%s", resource_group, registry_name)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_get_login_server(resource_group, registry_name)
    except Exception as e:
        logger.error("acr_get_login_server failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_list_repositories(resource_group: str, registry_name: str) -> str:
    """List repositories in a container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
    """
    logger.info("acr_list_repositories: %s/%s", resource_group, registry_name)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_list_repositories(resource_group, registry_name)
    except Exception as e:
        logger.error("acr_list_repositories failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_list_tags(resource_group: str, registry_name: str, repository: str) -> str:
    """List tags in a container registry repository.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        repository: Repository name
    """
    logger.info("acr_list_tags: %s/%s/%s", resource_group, registry_name, repository)
    if not registry_name or not resource_group or not repository:
        return "Error: registry_name, resource_group, and repository are required"
    try:
        return await acr.acr_list_tags(resource_group, registry_name, repository)
    except Exception as e:
        logger.error("acr_list_tags failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_show_task(resource_group: str, registry_name: str, task_name: str) -> str:
    """Get details of a container registry task.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        task_name: Name of the task
    """
    logger.info("acr_show_task: %s/%s/%s", resource_group, registry_name, task_name)
    if not registry_name or not resource_group or not task_name:
        return "Error: registry_name, resource_group, and task_name are required"
    try:
        return await acr.acr_show_task(resource_group, registry_name, task_name)
    except Exception as e:
        logger.error("acr_show_task failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_list_tasks(resource_group: str, registry_name: str) -> str:
    """List tasks in a container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
    """
    logger.info("acr_list_tasks: %s/%s", resource_group, registry_name)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_list_tasks(resource_group, registry_name)
    except Exception as e:
        logger.error("acr_list_tasks failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_create_task(
    resource_group: str,
    registry_name: str,
    task_name: str,
    platform_os: str = "Linux",
    platform_architecture: str = "amd64",
    platform_variant: str = "",
) -> str:
    """Create a container registry task.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        task_name: Name of the task
        platform_os: Platform OS - Linux or Windows (default: Linux)
        platform_architecture: Platform architecture (default: amd64)
        platform_variant: Platform variant (optional)
    """
    logger.info("acr_create_task: %s/%s/%s os=%s arch=%s", resource_group, registry_name, task_name, platform_os, platform_architecture)
    if not registry_name or not resource_group or not task_name:
        return "Error: registry_name, resource_group, and task_name are required"
    try:
        return await acr.acr_create_task(resource_group, registry_name, task_name, platform_os, platform_architecture, platform_variant)
    except Exception as e:
        logger.error("acr_create_task failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_delete_task(resource_group: str, registry_name: str, task_name: str) -> str:
    """Delete a container registry task.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        task_name: Name of the task
    """
    logger.info("acr_delete_task: %s/%s/%s", resource_group, registry_name, task_name)
    if not registry_name or not resource_group or not task_name:
        return "Error: registry_name, resource_group, and task_name are required"
    try:
        return await acr.acr_delete_task(resource_group, registry_name, task_name)
    except Exception as e:
        logger.error("acr_delete_task failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_run_task(resource_group: str, registry_name: str, task_name: str) -> str:
    """Run a container registry task.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        task_name: Name of the task
    """
    logger.info("acr_run_task: %s/%s/%s", resource_group, registry_name, task_name)
    if not registry_name or not resource_group or not task_name:
        return "Error: registry_name, resource_group, and task_name are required"
    try:
        return await acr.acr_run_task(resource_group, registry_name, task_name)
    except Exception as e:
        logger.error("acr_run_task failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_list_builds(resource_group: str = "", registry_name: str = "") -> str:
    """List build tasks in a subscription or specific registry.

    Args:
        resource_group: Resource group containing build runners (optional)
        registry_name: Name of the container registry (optional)
    """
    logger.info("acr_list_builds: %s", registry_name or "subscription")
    try:
        return await acr.acr_list_builds(resource_group, registry_name)
    except Exception as e:
        logger.error("acr_list_builds failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_show_quotas(resource_group: str, registry_name: str) -> str:
    """Show quota information for a container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
    """
    logger.info("acr_show_quotas: %s/%s", resource_group, registry_name)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_show_quotas(resource_group, registry_name)
    except Exception as e:
        logger.error("acr_show_quotas failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_show_usage(resource_group: str, registry_name: str) -> str:
    """Show usage information for a container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
    """
    logger.info("acr_show_usage: %s/%s", resource_group, registry_name)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_show_usage(resource_group, registry_name)
    except Exception as e:
        logger.error("acr_show_usage failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_list_network_rules(resource_group: str, registry_name: str) -> str:
    """List network rules for a container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
    """
    logger.info("acr_list_network_rules: %s/%s", resource_group, registry_name)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_list_network_rules(resource_group, registry_name)
    except Exception as e:
        logger.error("acr_list_network_rules failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_update_network_rules(
    resource_group: str,
    registry_name: str,
    default_action: str = "Allow",
) -> str:
    """Update network rules for a container registry.

    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        default_action: Default action - Allow or Deny (default: Allow)
    """
    logger.info("acr_update_network_rules: %s/%s action=%s", resource_group, registry_name, default_action)
    if not registry_name or not resource_group:
        return "Error: registry_name and resource_group are required"
    try:
        return await acr.acr_update_network_rules(resource_group, registry_name, default_action)
    except Exception as e:
        logger.error("acr_update_network_rules failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def acr_reset_client() -> str:
    """Reset cached ACR client and force re-authentication."""
    logger.info("acr_reset_client called")
    try:
        acr.reset_acr_client()
        return "ACR client cache cleared"
    except Exception as e:
        logger.error("acr_reset_client failed: %s", e)
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



# -- 11. App Configuration ----------------------------------------------------


@mcp.tool()
async def appconfig_list(resource_group: str = "") -> str:
    """List App Configuration stores in the subscription or resource group.

    Args:
        resource_group: Optional resource group to filter by
    """
    logger.info("appconfig_list: %s", resource_group or "subscription")
    try:
        return await cloud.appconfig_list(resource_group)
    except Exception as e:
        logger.error("appconfig_list failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def appconfig_show(store_name: str, resource_group: str) -> str:
    """Show details of an App Configuration store.

    Args:
        store_name: Name of the App Configuration store
        resource_group: Resource group containing the store
    """
    logger.info("appconfig_show: %s/%s", resource_group, store_name)
    if not store_name or not resource_group:
        return "Error: store_name and resource_group are required"
    try:
        return await cloud.appconfig_show(store_name, resource_group)
    except Exception as e:
        logger.error("appconfig_show failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def appconfig_kv_list(store_name: str, resource_group: str = "", key_filter: str = "*", label_filter: str = "") -> str:
    """List key-values in an App Configuration store.

    Args:
        store_name: Name of the App Configuration store
        resource_group: Optional resource group (speeds up lookup)
        key_filter: Key pattern filter (default '*' for all, supports '*' wildcard)
        label_filter: Optional label filter
    """
    logger.info("appconfig_kv_list: store=%s, key=%s", store_name, key_filter)
    if not store_name:
        return "Error: store_name is required"
    try:
        return await cloud.appconfig_kv_list(store_name, resource_group, key_filter, label_filter)
    except Exception as e:
        logger.error("appconfig_kv_list failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def appconfig_kv_show(store_name: str, key: str, resource_group: str = "", label: str = "") -> str:
    """Show a specific key-value from an App Configuration store.

    Args:
        store_name: Name of the App Configuration store
        key: The configuration key to retrieve
        resource_group: Optional resource group
        label: Optional label (default: no label)
    """
    logger.info("appconfig_kv_show: store=%s, key=%s", store_name, key)
    if not store_name or not key:
        return "Error: store_name and key are required"
    try:
        return await cloud.appconfig_kv_show(store_name, key, resource_group, label)
    except Exception as e:
        logger.error("appconfig_kv_show failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def appconfig_kv_set(store_name: str, key: str, value: str, resource_group: str = "", label: str = "", content_type: str = "") -> str:
    """Set a key-value in an App Configuration store.

    Args:
        store_name: Name of the App Configuration store
        key: The configuration key
        value: The value to set
        resource_group: Optional resource group
        label: Optional label
        content_type: Optional content type (e.g. 'application/json')
    """
    logger.info("appconfig_kv_set: store=%s, key=%s", store_name, key)
    if not store_name or not key:
        return "Error: store_name and key are required"
    try:
        return await cloud.appconfig_kv_set(store_name, key, value, resource_group, label, content_type)
    except Exception as e:
        logger.error("appconfig_kv_set failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def appconfig_kv_delete(store_name: str, key: str, resource_group: str = "", label: str = "") -> str:
    """Delete a key-value from an App Configuration store.

    Args:
        store_name: Name of the App Configuration store
        key: The configuration key to delete
        resource_group: Optional resource group
        label: Optional label
    """
    logger.info("appconfig_kv_delete: store=%s, key=%s", store_name, key)
    if not store_name or not key:
        return "Error: store_name and key are required"
    try:
        return await cloud.appconfig_kv_delete(store_name, key, resource_group, label)
    except Exception as e:
        logger.error("appconfig_kv_delete failed: %s", e)
        return f"Error: {e}"


# -- 12. App Service -----------------------------------------------------------


@mcp.tool()
async def appservice_plan_list(resource_group: str = "") -> str:
    """List App Service plans in the subscription or resource group.

    Args:
        resource_group: Optional resource group to filter by
    """
    logger.info("appservice_plan_list: %s", resource_group or "subscription")
    try:
        return await cloud.appservice_plan_list(resource_group)
    except Exception as e:
        logger.error("appservice_plan_list failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def appservice_plan_show(name: str, resource_group: str) -> str:
    """Show details of an App Service plan.

    Args:
        name: App Service plan name
        resource_group: Resource group containing the plan
    """
    logger.info("appservice_plan_show: %s/%s", resource_group, name)
    if not name or not resource_group:
        return "Error: name and resource_group are required"
    try:
        return await cloud.appservice_plan_show(name, resource_group)
    except Exception as e:
        logger.error("appservice_plan_show failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def webapp_list(resource_group: str = "") -> str:
    """List web apps in the subscription or resource group.

    Args:
        resource_group: Optional resource group to filter by
    """
    logger.info("webapp_list: %s", resource_group or "subscription")
    try:
        return await cloud.webapp_list(resource_group)
    except Exception as e:
        logger.error("webapp_list failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def webapp_show(name: str, resource_group: str) -> str:
    """Show details of a web app.

    Args:
        name: Web app name
        resource_group: Resource group containing the web app
    """
    logger.info("webapp_show: %s/%s", resource_group, name)
    if not name or not resource_group:
        return "Error: name and resource_group are required"
    try:
        return await cloud.webapp_show(name, resource_group)
    except Exception as e:
        logger.error("webapp_show failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def webapp_start(name: str, resource_group: str) -> str:
    """Start a web app.

    Args:
        name: Web app name
        resource_group: Resource group containing the web app
    """
    logger.info("webapp_start: %s/%s", resource_group, name)
    if not name or not resource_group:
        return "Error: name and resource_group are required"
    try:
        return await cloud.webapp_start(name, resource_group)
    except Exception as e:
        logger.error("webapp_start failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def webapp_stop(name: str, resource_group: str) -> str:
    """Stop a web app.

    Args:
        name: Web app name
        resource_group: Resource group containing the web app
    """
    logger.info("webapp_stop: %s/%s", resource_group, name)
    if not name or not resource_group:
        return "Error: name and resource_group are required"
    try:
        return await cloud.webapp_stop(name, resource_group)
    except Exception as e:
        logger.error("webapp_stop failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def webapp_restart(name: str, resource_group: str) -> str:
    """Restart a web app.

    Args:
        name: Web app name
        resource_group: Resource group containing the web app
    """
    logger.info("webapp_restart: %s/%s", resource_group, name)
    if not name or not resource_group:
        return "Error: name and resource_group are required"
    try:
        return await cloud.webapp_restart(name, resource_group)
    except Exception as e:
        logger.error("webapp_restart failed: %s", e)
        return f"Error: {e}"


# -- 13. Virtual Networks ------------------------------------------------------


@mcp.tool()
async def vnet_list(resource_group: str = "") -> str:
    """List virtual networks in the subscription or resource group.

    Args:
        resource_group: Optional resource group to filter by
    """
    logger.info("vnet_list: %s", resource_group or "subscription")
    try:
        return await cloud.vnet_list(resource_group)
    except Exception as e:
        logger.error("vnet_list failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def vnet_show(name: str, resource_group: str) -> str:
    """Show details of a virtual network including subnets and peerings.

    Args:
        name: Virtual network name
        resource_group: Resource group containing the VNet
    """
    logger.info("vnet_show: %s/%s", resource_group, name)
    if not name or not resource_group:
        return "Error: name and resource_group are required"
    try:
        return await cloud.vnet_show(name, resource_group)
    except Exception as e:
        logger.error("vnet_show failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def vnet_create(name: str, resource_group: str, address_prefix: str = "10.0.0.0/16", location: str = "") -> str:
    """Create a virtual network with a default subnet.

    Args:
        name: Virtual network name
        resource_group: Resource group to create the VNet in
        address_prefix: Address space CIDR (default 10.0.0.0/16)
        location: Azure region (defaults to resource group location)
    """
    logger.info("vnet_create: %s/%s prefix=%s", resource_group, name, address_prefix)
    if not name or not resource_group:
        return "Error: name and resource_group are required"
    try:
        return await cloud.vnet_create(name, resource_group, address_prefix, location)
    except Exception as e:
        logger.error("vnet_create failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def vnet_delete(name: str, resource_group: str) -> str:
    """Delete a virtual network. WARNING: removes all subnets and peerings.

    Args:
        name: Virtual network name
        resource_group: Resource group containing the VNet
    """
    logger.info("vnet_delete: %s/%s", resource_group, name)
    if not name or not resource_group:
        return "Error: name and resource_group are required"
    try:
        return await cloud.vnet_delete(name, resource_group)
    except Exception as e:
        logger.error("vnet_delete failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def vnet_subnet_list(vnet_name: str, resource_group: str) -> str:
    """List subnets in a virtual network.

    Args:
        vnet_name: Virtual network name
        resource_group: Resource group containing the VNet
    """
    logger.info("vnet_subnet_list: %s/%s", resource_group, vnet_name)
    if not vnet_name or not resource_group:
        return "Error: vnet_name and resource_group are required"
    try:
        return await cloud.vnet_subnet_list(vnet_name, resource_group)
    except Exception as e:
        logger.error("vnet_subnet_list failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def vnet_subnet_show(vnet_name: str, subnet_name: str, resource_group: str) -> str:
    """Show details of a subnet including NSG, route table, and delegations.

    Args:
        vnet_name: Virtual network name
        subnet_name: Subnet name
        resource_group: Resource group containing the VNet
    """
    logger.info("vnet_subnet_show: %s/%s/%s", resource_group, vnet_name, subnet_name)
    if not vnet_name or not subnet_name or not resource_group:
        return "Error: vnet_name, subnet_name, and resource_group are required"
    try:
        return await cloud.vnet_subnet_show(vnet_name, subnet_name, resource_group)
    except Exception as e:
        logger.error("vnet_subnet_show failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def vnet_subnet_create(vnet_name: str, subnet_name: str, resource_group: str, address_prefix: str) -> str:
    """Create a subnet in a virtual network.

    Args:
        vnet_name: Virtual network name
        subnet_name: Name for the new subnet
        resource_group: Resource group containing the VNet
        address_prefix: Subnet CIDR (e.g. 10.0.1.0/24)
    """
    logger.info("vnet_subnet_create: %s/%s/%s prefix=%s", resource_group, vnet_name, subnet_name, address_prefix)
    if not vnet_name or not subnet_name or not resource_group or not address_prefix:
        return "Error: vnet_name, subnet_name, resource_group, and address_prefix are required"
    try:
        return await cloud.vnet_subnet_create(vnet_name, subnet_name, resource_group, address_prefix)
    except Exception as e:
        logger.error("vnet_subnet_create failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def vnet_subnet_delete(vnet_name: str, subnet_name: str, resource_group: str) -> str:
    """Delete a subnet from a virtual network.

    Args:
        vnet_name: Virtual network name
        subnet_name: Subnet name to delete
        resource_group: Resource group containing the VNet
    """
    logger.info("vnet_subnet_delete: %s/%s/%s", resource_group, vnet_name, subnet_name)
    if not vnet_name or not subnet_name or not resource_group:
        return "Error: vnet_name, subnet_name, and resource_group are required"
    try:
        return await cloud.vnet_subnet_delete(vnet_name, subnet_name, resource_group)
    except Exception as e:
        logger.error("vnet_subnet_delete failed: %s", e)
        return f"Error: {e}"


@mcp.tool()
async def vnet_peering_list(vnet_name: str, resource_group: str) -> str:
    """List peerings for a virtual network.

    Args:
        vnet_name: Virtual network name
        resource_group: Resource group containing the VNet
    """
    logger.info("vnet_peering_list: %s/%s", resource_group, vnet_name)
    if not vnet_name or not resource_group:
        return "Error: vnet_name and resource_group are required"
    try:
        return await cloud.vnet_peering_list(vnet_name, resource_group)
    except Exception as e:
        logger.error("vnet_peering_list failed: %s", e)
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
