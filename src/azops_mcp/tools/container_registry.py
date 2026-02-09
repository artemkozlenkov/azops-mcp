"""Azure Container Registry (ACR) management tools."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Azure SDK imports (lazy loaded)
_acr_client = None


def _get_acr_client():
    """Get Azure Container Registry Management client.
    
    Returns:
        ContainerRegistryManagementClient instance
    """
    global _acr_client
    if _acr_client is None:
        try:
            from azure.identity import ChainedTokenCredential
            from azure.mgmt.containerregistry import ContainerRegistryManagementClient
            
            # Import shared clients for credential and subscription
            from ._clients import _get_azure_credential, get_subscription_id
            
            credential = _get_azure_credential()
            subscription_id = get_subscription_id()
            
            if not subscription_id:
                raise ValueError("Subscription ID not configured. Use set_subscription to set it.")
            
            _acr_client = ContainerRegistryManagementClient(
                credential=credential,
                subscription_id=subscription_id,
            )
        except ImportError:
            raise ImportError(
                "Azure Container Registry SDK not installed. "
                "Run: pip install azure-mgmt-containerregistry"
            )
    return _acr_client


def reset_acr_client() -> None:
    """Reset cached ACR client."""
    global _acr_client
    _acr_client = None
    logger.info("ACR client cache cleared")


# =============================================================================
# ACR Registry Management
# =============================================================================


async def acr_list_registries(resource_group: str = "") -> str:
    """List container registries in a resource group or subscription.
    
    Args:
        resource_group: Optional resource group name to filter by
        
    Returns:
        Formatted list of container registries
    """
    try:
        client = _get_acr_client()
        
        if resource_group:
            # List registries in specific resource group
            registries = client.registries.list_by_resource_group(resource_group)
        else:
            # List all registries in subscription
            registries = client.registries.list()
        
        registry_list = []
        for reg in registries:
            registry_list.append(
                f"Name: {reg.name}\n"
                f"Resource Group: {reg.id.split('/')[4] if '/' in reg.id else 'N/A'}\n"
                f"Location: {reg.location}\n"
                f"Sku: {reg.sku.name if reg.sku else 'N/A'}\n"
                f"ID: {reg.id}\n"
                f"Status: {reg.status if hasattr(reg, 'status') and reg.status else 'N/A'}\n"
                f"Admin User: {'Enabled' if hasattr(reg, 'admin_user_enabled') and reg.admin_user_enabled else 'Disabled'}"
            )
        
        if not registry_list:
            return f"No container registries found{' in resource group ' + resource_group if resource_group else ''}."
        
        return "Azure Container Registries:\n\n" + "\n---\n".join(registry_list)
        
    except Exception as e:
        error_msg = f"Failed to list container registries: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def acr_show_registry(resource_group: str, registry_name: str) -> str:
    """Get details of a container registry.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        
    Returns:
        Registry details
    """
    try:
        client = _get_acr_client()
        reg = client.registries.get_properties(resource_group, registry_name)
        
        details = [
            f"Azure Container Registry Details",
            f"{'='*50}",
            f"Name: {reg.name}",
            f"Resource Group: {resource_group}",
            f"Location: {reg.location}",
            f"Sku: {reg.sku.name if reg.sku else 'N/A'}",
            f"ID: {reg.id}",
        ]
        
        if hasattr(reg, 'admin_user_enabled') and reg.admin_user_enabled:
            details.append("Admin User: Enabled")
        else:
            details.append("Admin User: Disabled")
        
        if hasattr(reg, 'status') and reg.status:
            details.append(f"Status: {reg.status}")
        
        if hasattr(reg, 'creation_date') and reg.creation_date:
            details.append(f"Creation Date: {reg.creation_date}")
            
        if hasattr(reg, 'policies') and reg.policies:
            details.append(f"Soft Delete Policies: {reg.policies}")
        
        return "\n".join(details)
        
    except Exception as e:
        error_msg = f"Failed to get registry '{registry_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


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
        
    Returns:
        Result of the create operation
    """
    try:
        client = _get_acr_client()
        
        # Validate SKU
        valid_skus = ["Basic", "Standard", "Premium"]
        if sku not in valid_skus:
            return f"Invalid SKU. Valid SKUs: {', '.join(valid_skus)}"
        
        # Prepare registry parameters
        params = {
            "location": location,
            "sku": {"name": sku},
            "tags": {},
        }
        
        if admin_enabled:
            params["admin_user_enabled"] = True
        
        # Create the registry
        poller = client.registries.begin_create(
            resource_group_name=resource_group,
            registry_name=registry_name,
            registry=params,
        )
        result = poller.result()
        
        output = [
            f"Container Registry Created Successfully!",
            f"{'='*50}",
            f"Name: {result.name}",
            f"Resource Group: {resource_group}",
            f"Location: {location}",
            f"Sku: {sku}",
        ]
        
        if admin_enabled:
            # Get admin credentials
            try:
                creds = client.registries.list_credentials(resource_group, registry_name)
                output.append(f"Admin Username: {creds.username}")
                output.append(f"Admin Password: {creds.passwords[0].value if creds.passwords else 'N/A'}")
            except Exception as cred_err:
                output.append(f"Could not retrieve admin credentials: {str(cred_err)}")
        
        return "\n".join(output)
        
    except Exception as e:
        error_msg = f"Failed to create registry '{registry_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


async def acr_delete_registry(resource_group: str, registry_name: str) -> str:
    """Delete a container registry.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        
    Returns:
        Result of the delete operation
    """
    try:
        client = _get_acr_client()
        
        # Begin delete operation
        poller = client.registries.begin_delete(
            resource_group_name=resource_group,
            registry_name=registry_name,
        )
        poller.result()
        
        return f"Container Registry '{registry_name}' deleted successfully."
        
    except Exception as e:
        error_msg = f"Failed to delete registry '{registry_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


async def acr_update_registry(
    resource_group: str,
    registry_name: str,
    admin_enabled: Optional[bool] = None,
    tags: Optional[Dict[str, str]] = None,
) -> str:
    """Update a container registry.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        admin_enabled: Enable or disable admin user (optional)
        tags: Dictionary of tags to update (optional)
        
    Returns:
        Result of the update operation
    """
    try:
        client = _get_acr_client()
        
        # Get current registry
        reg = client.registries.get_properties(resource_group, registry_name)
        
        # Prepare update parameters
        params = {}
        
        if admin_enabled is not None:
            params["admin_user_enabled"] = admin_enabled
        
        if tags is not None:
            params["tags"] = tags
        
        # Update the registry
        result = client.registries.update(
            resource_group_name=resource_group,
            registry_name=registry_name,
            registry_update_parameters=params,
        )
        
        output = [
            f"Container Registry Updated Successfully!",
            f"{'='*50}",
            f"Name: {result.name}",
            f"Admin User: {'Enabled' if result.admin_user_enabled else 'Disabled'}",
        ]
        
        return "\n".join(output)
        
    except Exception as e:
        error_msg = f"Failed to update registry '{registry_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


async def acr_get_credentials(resource_group: str, registry_name: str) -> str:
    """Get login credentials for a container registry.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        
    Returns:
        Registry login credentials
    """
    try:
        client = _get_acr_client()
        
        creds = client.registries.list_credentials(resource_group, registry_name)
        
        output = [
            f"Container Registry Credentials",
            f"{'='*50}",
            f"Username: {creds.username}",
        ]
        
        if creds.passwords:
            for i, pwd in enumerate(creds.passwords):
                output.append(f"Password {i + 1}: {pwd.value}")
        
        return "\n".join(output)
        
    except Exception as e:
        error_msg = f"Failed to get credentials for '{registry_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


async def acr_get_login_server(resource_group: str, registry_name: str) -> str:
    """Get the login server URL for a container registry.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        
    Returns:
        Login server URL
    """
    try:
        client = _get_acr_client()
        
        reg = client.registries.get_properties(resource_group, registry_name)
        
        login_server = reg.login_server if hasattr(reg, 'login_server') and reg.login_server else f"{registry_name}.azurecr.io"
        
        return f"Login Server: {login_server}"
        
    except Exception as e:
        error_msg = f"Failed to get login server for '{registry_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


# =============================================================================
# ACR Repository Management
# =============================================================================


async def acr_list_repositories(resource_group: str, registry_name: str) -> str:
    """List repositories in a container registry.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        
    Returns:
        List of repositories
    """
    try:
        client = _get_acr_client()
        
        repos = client.repositories.list(resource_group, registry_name)
        
        repo_list = []
        for repo in repos:
            repo_list.append(
                f"Name: {repo.name}\n"
                f"Type: {repo.type if hasattr(repo, 'type') else 'N/A'}"
            )
        
        if not repo_list:
            return f"No repositories found in registry '{registry_name}'."
        
        return "Container Registry Repositories:\n\n" + "\n---\n".join(repo_list)
        
    except Exception as e:
        error_msg = f"Failed to list repositories for '{registry_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


async def acr_list_tags(resource_group: str, registry_name: str, repository: str) -> str:
    """List tags in a container registry repository.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        repository: Repository name
        
    Returns:
        List of tags in the repository
    """
    try:
        client = _get_acr_client()
        
        tags = client.repositories.list_tags(resource_group, registry_name, repository)
        
        if not hasattr(tags, '__iter__'):
            return f"No tags found in repository '{repository}'."
        
        tag_list = []
        for tag in tags:
            if hasattr(tag, 'name'):
                tag_list.append(f"Name: {tag.name}")
            elif isinstance(tag, str):
                tag_list.append(f"Name: {tag}")
        
        if not tag_list:
            return f"No tags found in repository '{repository}'."
        
        return f"Tags for repository '{repository}':\n\n" + "\n".join(tag_list)
        
    except Exception as e:
        error_msg = f"Failed to list tags for repository '{repository}': {str(e)}"
        logger.error(error_msg)
        return error_msg


# =============================================================================
# ACR Task Management
# =============================================================================


async def acr_show_task(resource_group: str, registry_name: str, task_name: str) -> str:
    """Get details of a container registry task.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        task_name: Name of the task
        
    Returns:
        Task details
    """
    try:
        client = _get_acr_client()
        
        task = client.tasks.get(resource_group, registry_name, task_name)
        
        output = [
            f"Container Registry Task Details",
            f"{'='*50}",
            f"Name: {task.name}",
            f"Resource Group: {resource_group}",
            f"Location: {task.location}",
            f"Status: {task.status if hasattr(task, 'status') else 'N/A'}",
            f"Platform OS: {task.platform.os if task.platform else 'N/A'}",
            f"Platform Architecture: {task.platform.architecture if task.platform else 'N/A'}",
            f"Platform Variant: {task.platform.variant if task.platform else 'N/A'}",
        ]
        
        return "\n".join(output)
        
    except Exception as e:
        error_msg = f"Failed to get task '{task_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


async def acr_list_tasks(resource_group: str, registry_name: str) -> str:
    """List tasks in a container registry.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        
    Returns:
        List of tasks
    """
    try:
        client = _get_acr_client()
        
        tasks = client.tasks.list(resource_group, registry_name)
        
        task_list = []
        for task in tasks:
            task_list.append(
                f"Name: {task.name}\n"
                f"Status: {task.status if hasattr(task, 'status') else 'N/A'}\n"
                f"Location: {task.location}"
            )
        
        if not task_list:
            return f"No tasks found in registry '{registry_name}'."
        
        return "Container Registry Tasks:\n\n" + "\n---\n".join(task_list)
        
    except Exception as e:
        error_msg = f"Failed to list tasks for '{registry_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


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
        
    Returns:
        Result of the create operation
    """
    try:
        client = _get_acr_client()
        
        # Build platform object
        platform_obj = {
            "os": platform_os,
            "architecture": platform_architecture,
        }
        
        if platform_variant:
            platform_obj["variant"] = platform_variant
        
        # Prepare task parameters
        params = {
            "location": "eastus",
            "platform": platform_obj,
        }
        
        # Create the task
        result = client.tasks.create(
            resource_group_name=resource_group,
            registry_name=registry_name,
            task_name=task_name,
            parameters=params,
        )
        
        output = [
            f"Container Registry Task Created Successfully!",
            f"{'='*50}",
            f"Name: {result.name}",
            f"Resource Group: {resource_group}",
        ]
        
        return "\n".join(output)
        
    except Exception as e:
        error_msg = f"Failed to create task '{task_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


async def acr_delete_task(resource_group: str, registry_name: str, task_name: str) -> str:
    """Delete a container registry task.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        task_name: Name of the task
        
    Returns:
        Result of the delete operation
    """
    try:
        client = _get_acr_client()
        
        client.tasks.delete(resource_group, registry_name, task_name)
        
        return f"Container Registry Task '{task_name}' deleted successfully."
        
    except Exception as e:
        error_msg = f"Failed to delete task '{task_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


async def acr_run_task(resource_group: str, registry_name: str, task_name: str) -> str:
    """Run a container registry task.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        task_name: Name of the task
        
    Returns:
        Result of the run operation
    """
    try:
        client = _get_acr_client()
        
        # Run the task
        result = client.tasks.run(
            resource_group_name=resource_group,
            registry_name=registry_name,
            task_name=task_name,
        )
        
        return f"Task '{task_name}' run initiated. Run ID: {result.run_id if hasattr(result, 'run_id') else 'N/A'}"
        
    except Exception as e:
        error_msg = f"Failed to run task '{task_name}': {str(e)}"
        logger.error(error_msg)
        return error_msg


# =============================================================================
# ACR Build Management
# =============================================================================


async def acr_list_builds(resource_group: str = "", registry_name: str = "") -> str:
    """List build tasks in a subscription or specific registry.
    
    Args:
        resource_group: Resource group containing build runners (optional)
        registry_name: Name of the container registry (optional)
        
    Returns:
        List of builds
    """
    try:
        client = _get_acr_client()
        
        builds = []
        
        if registry_name:
            # Try to list builds for a specific registry
            try:
                if hasattr(client, 'builds'):
                    for build in client.builds.list(registry_name=registry_name):
                        builds.append(build)
                elif hasattr(client, 'build_tasks'):
                    for build in client.build_tasks.list(registry_name=registry_name):
                        builds.append(build)
            except Exception as e:
                logger.warning(f"Could not list builds: {e}")
        
        if not builds:
            return "No builds found or build listing not available in current SDK version."
        
        build_list = []
        for build in builds:
            build_list.append(
                f"Build ID: {build.id if hasattr(build, 'id') else 'N/A'}\n"
                f"Status: {build.status if hasattr(build, 'status') else 'N/A'}\n"
                f"Start Time: {build.start_time if hasattr(build, 'start_time') else 'N/A'}"
            )
        
        return "Container Registry Builds:\n\n" + "\n---\n".join(build_list)
        
    except Exception as e:
        error_msg = f"Failed to list builds: {str(e)}"
        logger.error(error_msg)
        return error_msg


# =============================================================================
# ACR Quotas and Usage
# =============================================================================


async def acr_show_quotas(resource_group: str, registry_name: str) -> str:
    """Show quota information for a container registry.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        
    Returns:
        Quota information
    """
    try:
        client = _get_acr_client()
        
        # Get quota information
        quotas = client.quotas.get(resource_group, registry_name)
        
        output = [
            f"Container Registry Quotas",
            f"{'='*50}",
        ]
        
        if hasattr(quotas, 'storage_quota'):
            output.append(f"Storage Quota: {quotas.storage_quota} bytes")
        
        if hasattr(quotas, 'bandwidth_quota'):
            output.append(f"Bandwidth Quota: {quotas.bandwidth_quota}")
        
        return "\n".join(output)
        
    except Exception as e:
        # Quotas endpoint may not be available in all SDK versions
        return f"Quota information not available: {str(e)}"


async def acr_show_usage(resource_group: str, registry_name: str) -> str:
    """Show usage information for a container registry.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        
    Returns:
        Usage information
    """
    try:
        client = _get_acr_client()
        
        # Get usage information
        usages = client.usages.list(resource_group, registry_name)
        
        output = [
            f"Container Registry Usage",
            f"{'='*50}",
        ]
        
        for usage in usages:
            output.append(
                f"Name: {usage.name.value if hasattr(usage, 'name') and usage.name else 'N/A'}\n"
                f"Value: {usage.value if hasattr(usage, 'value') else 'N/A'}\n"
                f"Limit: {usage.limit if hasattr(usage, 'limit') else 'N/A'}"
            )
        
        return "\n".join(output)
        
    except Exception as e:
        return f"Usage information not available: {str(e)}"


# =============================================================================
# ACR Network Rules
# =============================================================================


async def acr_list_network_rules(resource_group: str, registry_name: str) -> str:
    """List network rules for a container registry.
    
    Args:
        resource_group: Resource group name
        registry_name: Name of the container registry
        
    Returns:
        List of network rules
    """
    try:
        client = _get_acr_client()
        
        # Get registry with expand network rule sets
        reg = client.registries.get_properties(resource_group, registry_name)
        
        output = [
            f"Container Registry Network Rules",
            f"{'='*50}",
        ]
        
        if hasattr(reg, 'network_rule_set') and reg.network_rule_set:
            output.append(f"Default Action: {reg.network_rule_set.default_action if hasattr(reg.network_rule_set, 'default_action') else 'N/A'}")
        else:
            output.append("Network rules not configured.")
        
        return "\n".join(output)
        
    except Exception as e:
        error_msg = f"Failed to get network rules: {str(e)}"
        logger.error(error_msg)
        return error_msg


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
        
    Returns:
        Result of the update operation
    """
    try:
        client = _get_acr_client()
        
        # Validate default action
        if default_action not in ["Allow", "Deny"]:
            return f"Invalid default action. Valid values: Allow, Deny"
        
        # Get current registry
        reg = client.registries.get_properties(resource_group, registry_name)
        
        # Prepare update
        params = {
            "network_rule_set": {
                "default_action": default_action,
            },
        }
        
        result = client.registries.update(
            resource_group_name=resource_group,
            registry_name=registry_name,
            registry_update_parameters=params,
        )
        
        return (
            f"Network rules updated successfully!\n"
            f"Default Action: {default_action}"
        )
        
    except Exception as e:
        error_msg = f"Failed to update network rules: {str(e)}"
        logger.error(error_msg)
        return error_msg
