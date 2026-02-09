"""Azure cloud resource management tools."""

import logging
from typing import Any, Dict, List, Optional

from ..utils.helpers import format_error_message
from ..config import config

logger = logging.getLogger(__name__)

# Azure SDK imports (lazy loaded)
_azure_credential = None
_compute_client = None
_resource_client = None
_storage_client = None
_appconfig_mgmt_client = None
_appconfig_data_clients: Dict[str, Any] = {}  # keyed by store endpoint
_web_client = None
_network_client = None

# Runtime configuration (can be set via chat)
_runtime_config: Dict[str, Optional[str]] = {
    "subscription_id": None,  # Overrides config.azure_subscription_id when set
}


def set_subscription_id(subscription_id: str) -> None:
    """Set the active subscription ID at runtime."""
    global _runtime_config, _compute_client, _resource_client, _storage_client, _subscription_client
    global _appconfig_mgmt_client, _appconfig_data_clients, _web_client, _network_client
    _runtime_config["subscription_id"] = subscription_id
    # Clear cached clients so they use the new subscription
    _compute_client = None
    _resource_client = None
    _storage_client = None
    _subscription_client = None
    _appconfig_mgmt_client = None
    _appconfig_data_clients = {}
    _web_client = None
    _network_client = None
    logger.info(f"Subscription ID set to: {subscription_id}")


def get_subscription_id() -> Optional[str]:
    """Get the active subscription ID (runtime override or config)."""
    return _runtime_config.get("subscription_id") or config.azure_subscription_id


def clear_subscription_id() -> None:
    """Clear the runtime subscription ID override."""
    global _runtime_config
    _runtime_config["subscription_id"] = None
    logger.info("Runtime subscription ID cleared, using config value")


def _get_azure_credential():
    """Get Azure credential (lazy initialization).
    
    Authentication priority:
    1. Azure CLI credentials (after 'az login') - recommended for local development
    2. Service Principal (if AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID are set)
    3. DefaultAzureCredential (tries multiple methods including managed identity, VS Code, etc.)
    """
    global _azure_credential
    if _azure_credential is None:
        try:
            from azure.identity import (
                AzureCliCredential,
                ClientSecretCredential,
                ChainedTokenCredential,
                ManagedIdentityCredential,
            )
            
            # If service principal is fully configured, use it
            if config.azure_client_id and config.azure_client_secret and config.azure_tenant_id:
                logger.info("Using Service Principal authentication")
                _azure_credential = ClientSecretCredential(
                    tenant_id=config.azure_tenant_id,
                    client_id=config.azure_client_id,
                    client_secret=config.azure_client_secret,
                )
            else:
                # Prioritize Azure CLI credentials for local development
                # Falls back to Managed Identity for Azure-hosted environments
                logger.info("Using Azure CLI / Managed Identity authentication")
                _azure_credential = ChainedTokenCredential(
                    AzureCliCredential(),
                    ManagedIdentityCredential(),
                )
        except ImportError:
            raise ImportError("Azure SDK not installed. Run: pip install azure-identity azure-mgmt-compute azure-mgmt-resource azure-mgmt-storage")
    return _azure_credential


def reset_azure_credentials():
    """Reset cached Azure credentials (useful after re-authentication)."""
    global _azure_credential, _compute_client, _resource_client, _storage_client, _subscription_client
    global _appconfig_mgmt_client, _appconfig_data_clients, _web_client, _network_client
    _azure_credential = None
    _compute_client = None
    _resource_client = None
    _storage_client = None
    _subscription_client = None
    _appconfig_mgmt_client = None
    _appconfig_data_clients = {}
    _web_client = None
    _network_client = None
    logger.info("Azure credentials cache cleared")


def _get_compute_client():
    """Get Azure Compute Management client."""
    global _compute_client
    if _compute_client is None:
        try:
            from azure.mgmt.compute import ComputeManagementClient
            
            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError("Subscription ID not configured. Use azure_set_subscription to set it, or configure AZURE_SUBSCRIPTION_ID in .env")
            
            _compute_client = ComputeManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError:
            raise ImportError("Azure Compute SDK not installed. Run: pip install azure-mgmt-compute")
    return _compute_client


def _get_resource_client():
    """Get Azure Resource Management client."""
    global _resource_client
    if _resource_client is None:
        try:
            from azure.mgmt.resource import ResourceManagementClient
            
            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError("Subscription ID not configured. Use azure_set_subscription to set it, or configure AZURE_SUBSCRIPTION_ID in .env")
            
            _resource_client = ResourceManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError:
            raise ImportError("Azure Resource SDK not installed. Run: pip install azure-mgmt-resource")
    return _resource_client


def _get_storage_client():
    """Get Azure Storage Management client."""
    global _storage_client
    if _storage_client is None:
        try:
            from azure.mgmt.storage import StorageManagementClient
            
            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError("Subscription ID not configured. Use azure_set_subscription to set it, or configure AZURE_SUBSCRIPTION_ID in .env")
            
            _storage_client = StorageManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError:
            raise ImportError("Azure Storage SDK not installed. Run: pip install azure-mgmt-storage")
    return _storage_client


async def list_resources(resource_group: str, resource_type: str = "all") -> str:
    """List Azure resources in a resource group.
    
    Args:
        resource_group: Azure resource group name
        resource_type: Type of resources to list (all, vm, storage, webapp, sql)
        
    Returns:
        Formatted list of resources
    """
    resource_type = resource_type.lower()
    valid_types = ["all", "vm", "storage", "webapp", "sql"]
    
    if resource_type not in valid_types:
        return f"Invalid resource_type: {resource_type}. Valid types: {', '.join(valid_types)}"
    
    try:
        resources: List[Dict[str, Any]] = []
        
        if resource_type in ["all", "vm"]:
            # List Virtual Machines
            try:
                compute_client = _get_compute_client()
                vms = compute_client.virtual_machines.list(resource_group)
                for vm in vms:
                    # Get instance view for power state
                    instance_view = compute_client.virtual_machines.instance_view(
                        resource_group, vm.name
                    )
                    power_state = "unknown"
                    for status in instance_view.statuses:
                        if status.code.startswith("PowerState/"):
                            power_state = status.code.replace("PowerState/", "")
                            break
                    
                    resources.append({
                        "type": "Virtual Machine",
                        "name": vm.name,
                        "id": vm.id,
                        "location": vm.location,
                        "status": power_state,
                        "vm_size": vm.hardware_profile.vm_size if vm.hardware_profile else "N/A",
                    })
            except Exception as e:
                logger.warning(f"Failed to list VMs: {e}")
        
        if resource_type in ["all", "storage"]:
            # List Storage Accounts
            try:
                storage_client = _get_storage_client()
                # Filter by resource group
                accounts = storage_client.storage_accounts.list_by_resource_group(resource_group)
                for account in accounts:
                    resources.append({
                        "type": "Storage Account",
                        "name": account.name,
                        "id": account.id,
                        "location": account.location,
                        "status": account.provisioning_state,
                        "kind": account.kind,
                    })
            except Exception as e:
                logger.warning(f"Failed to list storage accounts: {e}")
        
        if resource_type == "all":
            # List all resources in the resource group
            try:
                resource_client = _get_resource_client()
                all_resources = resource_client.resources.list_by_resource_group(resource_group)
                existing_ids = {r["id"] for r in resources}
                
                for resource in all_resources:
                    if resource.id not in existing_ids:
                        resources.append({
                            "type": resource.type.split("/")[-1] if resource.type else "Unknown",
                            "name": resource.name,
                            "id": resource.id,
                            "location": resource.location,
                            "status": "available",
                        })
            except Exception as e:
                logger.warning(f"Failed to list all resources: {e}")
        
        if not resources:
            return f"No resources found in resource group '{resource_group}'"
        
        formatted_resources = []
        for resource in resources:
            details = [f"Type: {resource['type']}", f"Name: {resource['name']}"]
            if resource.get("location"):
                details.append(f"Location: {resource['location']}")
            if resource.get("status"):
                details.append(f"Status: {resource['status']}")
            if resource.get("vm_size"):
                details.append(f"Size: {resource['vm_size']}")
            if resource.get("kind"):
                details.append(f"Kind: {resource['kind']}")
            formatted_resources.append("\n".join(details))
        
        return f"Azure Resources in '{resource_group}':\n\n" + "\n---\n".join(formatted_resources)
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to list resources in {resource_group}")
        logger.error(error_msg)
        return error_msg


async def get_resource_status(resource_group: str, resource_name: str, resource_type: str = "vm") -> str:
    """Get status of a specific Azure resource.
    
    Args:
        resource_group: Azure resource group name
        resource_name: Name of the resource
        resource_type: Type of resource (vm, storage, webapp)
        
    Returns:
        Resource status information
    """
    resource_type = resource_type.lower()
    
    try:
        if resource_type == "vm":
            compute_client = _get_compute_client()
            
            # Get VM details
            vm = compute_client.virtual_machines.get(resource_group, resource_name)
            instance_view = compute_client.virtual_machines.instance_view(resource_group, resource_name)
            
            # Extract power state and provisioning state
            power_state = "unknown"
            provisioning_state = "unknown"
            for status in instance_view.statuses:
                if status.code.startswith("PowerState/"):
                    power_state = status.code.replace("PowerState/", "")
                elif status.code.startswith("ProvisioningState/"):
                    provisioning_state = status.code.replace("ProvisioningState/", "")
            
            return (
                f"Azure VM Status:\n"
                f"Name: {vm.name}\n"
                f"Resource Group: {resource_group}\n"
                f"Location: {vm.location}\n"
                f"VM Size: {vm.hardware_profile.vm_size if vm.hardware_profile else 'N/A'}\n"
                f"Power State: {power_state}\n"
                f"Provisioning State: {provisioning_state}\n"
                f"OS Type: {vm.storage_profile.os_disk.os_type if vm.storage_profile and vm.storage_profile.os_disk else 'N/A'}"
            )
            
        elif resource_type == "storage":
            storage_client = _get_storage_client()
            account = storage_client.storage_accounts.get_properties(resource_group, resource_name)
            
            return (
                f"Azure Storage Account Status:\n"
                f"Name: {account.name}\n"
                f"Resource Group: {resource_group}\n"
                f"Location: {account.location}\n"
                f"Kind: {account.kind}\n"
                f"SKU: {account.sku.name if account.sku else 'N/A'}\n"
                f"Provisioning State: {account.provisioning_state}\n"
                f"Primary Endpoints: {account.primary_endpoints.blob if account.primary_endpoints else 'N/A'}"
            )
            
        else:
            return f"Unsupported resource type: {resource_type}. Supported types: vm, storage"
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to get status for {resource_name}")
        logger.error(error_msg)
        return error_msg


async def manage_vm(resource_group: str, vm_name: str, action: str) -> str:
    """Manage an Azure Virtual Machine (start, stop, restart, deallocate).
    
    Args:
        resource_group: Azure resource group name
        vm_name: Name of the virtual machine
        action: Action to perform (start, stop, restart, deallocate)
        
    Returns:
        Operation result
    """
    action = action.lower()
    valid_actions = ["start", "stop", "restart", "deallocate"]
    
    if action not in valid_actions:
        return f"Invalid action: {action}. Valid actions: {', '.join(valid_actions)}"
    
    try:
        compute_client = _get_compute_client()
        
        if action == "start":
            poller = compute_client.virtual_machines.begin_start(resource_group, vm_name)
            poller.result()  # Wait for completion
            return f"VM '{vm_name}' started successfully."
            
        elif action == "stop":
            poller = compute_client.virtual_machines.begin_power_off(resource_group, vm_name)
            poller.result()
            return f"VM '{vm_name}' stopped successfully."
            
        elif action == "restart":
            poller = compute_client.virtual_machines.begin_restart(resource_group, vm_name)
            poller.result()
            return f"VM '{vm_name}' restarted successfully."
            
        elif action == "deallocate":
            poller = compute_client.virtual_machines.begin_deallocate(resource_group, vm_name)
            poller.result()
            return f"VM '{vm_name}' deallocated successfully."
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to {action} VM {vm_name}")
        logger.error(error_msg)
        return error_msg


async def scale_vmss(resource_group: str, vmss_name: str, capacity: int) -> str:
    """Scale an Azure Virtual Machine Scale Set.
    
    Args:
        resource_group: Azure resource group name
        vmss_name: Name of the VM Scale Set
        capacity: Target instance count (must be non-negative)
        
    Returns:
        Scaling operation result
    """
    if capacity < 0:
        return "Capacity must be non-negative"
    
    try:
        compute_client = _get_compute_client()
        
        # Get current VMSS
        vmss = compute_client.virtual_machine_scale_sets.get(resource_group, vmss_name)
        current_capacity = vmss.sku.capacity if vmss.sku else 0
        
        # Update capacity
        vmss.sku.capacity = capacity
        poller = compute_client.virtual_machine_scale_sets.begin_create_or_update(
            resource_group, vmss_name, vmss
        )
        poller.result()  # Wait for completion
        
        return (
            f"VMSS Scaling Complete:\n"
            f"Name: {vmss_name}\n"
            f"Resource Group: {resource_group}\n"
            f"Previous Capacity: {current_capacity}\n"
            f"New Capacity: {capacity}"
        )
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to scale VMSS {vmss_name}")
        logger.error(error_msg)
        return error_msg


async def list_resource_groups() -> str:
    """List all Azure resource groups in the subscription.
    
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
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list resource groups")
        logger.error(error_msg)
        return error_msg


async def create_resource_group(name: str, location: str, tags: Optional[Dict[str, str]] = None) -> str:
    """Create a new Azure resource group.
    
    Args:
        name: Name of the resource group to create
        location: Azure region (e.g., eastus, westeurope, southeastasia)
        tags: Optional dictionary of tags to apply to the resource group
        
    Returns:
        Result of the create operation
    """
    try:
        resource_client = _get_resource_client()
        
        # Prepare resource group parameters
        rg_params = {
            "location": location,
        }
        if tags:
            rg_params["tags"] = tags
        
        # Create the resource group
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
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to create resource group '{name}'")
        logger.error(error_msg)
        return error_msg


async def delete_resource_group(name: str) -> str:
    """Delete an Azure resource group and all its resources.
    
    WARNING: This will delete ALL resources within the resource group!
    
    Args:
        name: Name of the resource group to delete
        
    Returns:
        Result of the delete operation
    """
    try:
        resource_client = _get_resource_client()
        
        # Start the delete operation (this is async on Azure side)
        poller = resource_client.resource_groups.begin_delete(name)
        
        # Wait for completion
        poller.result()
        
        return f"Resource group '{name}' deleted successfully."
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to delete resource group '{name}'")
        logger.error(error_msg)
        return error_msg


# Subscription client (lazy loaded)
_subscription_client = None


def _get_subscription_client():
    """Get Azure Subscription Management client."""
    global _subscription_client
    if _subscription_client is None:
        try:
            from azure.mgmt.subscription import SubscriptionClient
            
            _subscription_client = SubscriptionClient(
                credential=_get_azure_credential(),
            )
        except ImportError:
            raise ImportError("Azure Subscription SDK not installed. Run: pip install azure-mgmt-subscription")
    return _subscription_client


async def configure_subscription(subscription_id: str) -> str:
    """Set the active Azure subscription ID for this session.
    
    Args:
        subscription_id: The Azure subscription ID to use
        
    Returns:
        Confirmation message
    """
    try:
        # Validate the subscription ID format (basic validation)
        import re
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', subscription_id.lower()):
            return f"Error: Invalid subscription ID format. Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        
        set_subscription_id(subscription_id)
        
        # Try to validate by fetching subscription details
        try:
            subscription_client = _get_subscription_client()
            subscription = subscription_client.subscriptions.get(subscription_id)
            
            return (
                f"Subscription configured successfully!\n"
                f"{'='*50}\n"
                f"Subscription ID: {subscription.subscription_id}\n"
                f"Name: {subscription.display_name}\n"
                f"State: {subscription.state}\n"
                f"\nYou can now use Azure resource tools with this subscription."
            )
        except Exception as e:
            # Still set it, but warn that validation failed
            return (
                f"Subscription ID set to: {subscription_id}\n"
                f"Warning: Could not validate subscription. Error: {str(e)}\n"
                f"Make sure you're authenticated (run 'az login' or configure service principal)."
            )
            
    except Exception as e:
        error_msg = format_error_message(e, "Failed to configure subscription")
        logger.error(error_msg)
        return error_msg


async def get_auth_status() -> str:
    """Get current Azure authentication status and method being used.
    
    Returns:
        Information about the current authentication method and its validity
    """
    try:
        from azure.identity import AzureCliCredential, ClientSecretCredential
        from azure.core.exceptions import ClientAuthenticationError
        
        auth_info = {
            "method": "Unknown",
            "status": "Unknown",
            "details": [],
        }
        
        # Check which authentication method is configured
        if config.azure_client_id and config.azure_client_secret and config.azure_tenant_id:
            auth_info["method"] = "Service Principal"
            auth_info["details"].append(f"Client ID: {config.azure_client_id[:8]}...{config.azure_client_id[-4:]}")
            auth_info["details"].append(f"Tenant ID: {config.azure_tenant_id}")
        else:
            auth_info["method"] = "Azure CLI (az login)"
            auth_info["details"].append("Using local Azure CLI credentials")
            auth_info["details"].append("Run 'az login' if not authenticated")
        
        # Test the credentials by attempting to get a token
        try:
            credential = _get_azure_credential()
            # Try to get a token for Azure Resource Manager
            token = credential.get_token("https://management.azure.com/.default")
            if token:
                auth_info["status"] = "Authenticated"
                # Token expiry
                from datetime import datetime
                expiry = datetime.fromtimestamp(token.expires_on)
                auth_info["details"].append(f"Token expires: {expiry.isoformat()}")
        except ClientAuthenticationError as e:
            auth_info["status"] = "Not Authenticated"
            auth_info["details"].append(f"Error: {str(e)}")
        except Exception as e:
            auth_info["status"] = "Error"
            auth_info["details"].append(f"Error checking credentials: {str(e)}")
        
        # Check subscription configuration
        subscription_id = get_subscription_id()
        runtime_sub = _runtime_config.get("subscription_id")
        
        if subscription_id:
            if runtime_sub:
                auth_info["details"].append(f"Subscription ID: {subscription_id} (set via chat)")
            else:
                auth_info["details"].append(f"Subscription ID: {subscription_id} (from .env)")
        else:
            auth_info["details"].append("Warning: No subscription ID configured")
            auth_info["details"].append("Use azure_set_subscription to set one, or add AZURE_SUBSCRIPTION_ID to .env")
        
        # Format output
        output = (
            f"Azure Authentication Status:\n"
            f"{'='*50}\n"
            f"Method: {auth_info['method']}\n"
            f"Status: {auth_info['status']}\n"
            f"\nDetails:\n"
        )
        for detail in auth_info["details"]:
            output += f"  - {detail}\n"
        
        return output
        
    except ImportError as e:
        return f"Azure SDK not installed: {str(e)}"
    except Exception as e:
        error_msg = format_error_message(e, "Failed to check authentication status")
        logger.error(error_msg)
        return error_msg


async def get_account_info() -> str:
    """Get current Azure account/subscription information (similar to 'az account show').
    
    Returns:
        Formatted account information including subscription details
    """
    try:
        subscription_id = get_subscription_id()
        if not subscription_id:
            return "Error: No subscription ID configured. Use azure_set_subscription to set one."
        
        subscription_client = _get_subscription_client()
        
        # Get subscription details
        subscription = subscription_client.subscriptions.get(subscription_id)
        
        # Get tenant information
        tenant_id = config.azure_tenant_id or "Not configured (using DefaultAzureCredential)"
        
        # Format output similar to 'az account show'
        output = (
            f"Azure Account Information:\n"
            f"{'='*50}\n"
            f"Subscription ID: {subscription.subscription_id}\n"
            f"Subscription Name: {subscription.display_name}\n"
            f"State: {subscription.state}\n"
            f"Tenant ID: {tenant_id}\n"
            f"Environment: AzureCloud\n"
            f"Home Tenant ID: {subscription.tenant_id}\n"
        )
        
        # Add subscription policies if available
        if subscription.subscription_policies:
            policies = subscription.subscription_policies
            output += (
                f"\nSubscription Policies:\n"
                f"  Location Placement ID: {policies.location_placement_id or 'N/A'}\n"
                f"  Quota ID: {policies.quota_id or 'N/A'}\n"
                f"  Spending Limit: {policies.spending_limit or 'N/A'}"
            )
        
        return output
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to get account information")
        logger.error(error_msg)
        return error_msg


async def list_subscriptions() -> str:
    """List all Azure subscriptions accessible to the current credentials (similar to 'az account list').
    
    Returns:
        Formatted list of subscriptions
    """
    try:
        subscription_client = _get_subscription_client()
        subscriptions = subscription_client.subscriptions.list()
        
        formatted_subs = []
        current_sub_id = get_subscription_id()
        
        for sub in subscriptions:
            is_current = " (current)" if sub.subscription_id == current_sub_id else ""
            formatted_subs.append(
                f"Name: {sub.display_name}{is_current}\n"
                f"Subscription ID: {sub.subscription_id}\n"
                f"State: {sub.state}"
            )
        
        if not formatted_subs:
            return "No subscriptions found for the current credentials."
        
        return f"Azure Subscriptions ({len(formatted_subs)} found):\n\n" + "\n---\n".join(formatted_subs)
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list subscriptions")
        logger.error(error_msg)
        return error_msg


async def list_locations() -> str:
    """List all Azure locations/regions available for the subscription (similar to 'az account list-locations').
    
    Returns:
        Formatted list of Azure regions
    """
    try:
        subscription_id = get_subscription_id()
        if not subscription_id:
            return "Error: No subscription ID configured. Use azure_set_subscription to set one."
        
        subscription_client = _get_subscription_client()
        locations = subscription_client.subscriptions.list_locations(subscription_id)
        
        formatted_locations = []
        for loc in locations:
            formatted_locations.append(
                f"Name: {loc.name}\n"
                f"Display Name: {loc.display_name}\n"
                f"Regional Display Name: {loc.regional_display_name or 'N/A'}\n"
                f"Type: {loc.type or 'N/A'}"
            )
        
        if not formatted_locations:
            return "No locations found for the subscription."
        
        return f"Azure Locations ({len(formatted_locations)} available):\n\n" + "\n---\n".join(formatted_locations)
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list locations")
        logger.error(error_msg)
        return error_msg


# Management Group client (lazy loaded)
_management_group_client = None


def _get_management_group_client():
    """Get Azure Management Group client."""
    global _management_group_client
    if _management_group_client is None:
        try:
            from azure.mgmt.managementgroups import ManagementGroupsAPI
            
            _management_group_client = ManagementGroupsAPI(
                credential=_get_azure_credential(),
            )
        except ImportError:
            raise ImportError("Azure Management Groups SDK not installed. Run: pip install azure-mgmt-managementgroups")
    return _management_group_client


async def list_management_groups() -> str:
    """List all Azure management groups.
    
    Returns:
        Formatted list of management groups
    """
    try:
        client = _get_management_group_client()
        groups = client.management_groups.list()
        
        formatted_groups = []
        for group in groups:
            formatted_groups.append(
                f"Name: {group.display_name or group.name}\n"
                f"ID: {group.name}\n"
                f"Type: {group.type}"
            )
        
        if not formatted_groups:
            return "No management groups found."
        
        return f"Azure Management Groups ({len(formatted_groups)} found):\n\n" + "\n---\n".join(formatted_groups)
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list management groups")
        logger.error(error_msg)
        return error_msg


async def get_management_group(group_id: str) -> str:
    """Get details of a specific management group.
    
    Args:
        group_id: Management group ID or name
        
    Returns:
        Management group details
    """
    try:
        client = _get_management_group_client()
        group = client.management_groups.get(group_id, expand="children")
        
        output = (
            f"Management Group Details:\n"
            f"{'='*50}\n"
            f"Display Name: {group.display_name or 'N/A'}\n"
            f"ID: {group.name}\n"
            f"Type: {group.type}\n"
            f"Tenant ID: {group.tenant_id or 'N/A'}\n"
        )
        
        # List children (subscriptions and child management groups)
        if group.children:
            output += f"\nChildren ({len(group.children)}):\n"
            for child in group.children:
                child_type = "Subscription" if "/subscriptions/" in (child.type or "") else "Management Group"
                output += f"  - {child.display_name or child.name} ({child_type})\n"
        
        return output
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to get management group '{group_id}'")
        logger.error(error_msg)
        return error_msg


async def create_management_group(group_id: str, display_name: str, parent_id: Optional[str] = None) -> str:
    """Create a new management group.
    
    Args:
        group_id: Unique ID for the management group
        display_name: Display name for the management group
        parent_id: Optional parent management group ID
        
    Returns:
        Result of the create operation
    """
    try:
        client = _get_management_group_client()
        
        # Prepare create request
        create_request = {
            "display_name": display_name,
        }
        if parent_id:
            create_request["parent_id"] = f"/providers/Microsoft.Management/managementGroups/{parent_id}"
        
        # Create management group (this is a long-running operation)
        poller = client.management_groups.begin_create_or_update(group_id, create_request)
        result = poller.result()
        
        return (
            f"Management group created successfully!\n"
            f"{'='*50}\n"
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
        group_id: Management group ID to delete
        
    Returns:
        Result of the delete operation
    """
    try:
        client = _get_management_group_client()
        
        # Delete management group
        poller = client.management_groups.begin_delete(group_id)
        poller.result()
        
        return f"Management group '{group_id}' deleted successfully."
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to delete management group '{group_id}'")
        logger.error(error_msg)
        return error_msg


# Authorization client (lazy loaded) - for RBAC
_authorization_client = None


def _get_authorization_client():
    """Get Azure Authorization client for RBAC."""
    global _authorization_client
    if _authorization_client is None:
        try:
            from azure.mgmt.authorization import AuthorizationManagementClient
            
            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError("Subscription ID not configured")
            
            _authorization_client = AuthorizationManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError:
            raise ImportError("Azure Authorization SDK not installed. Run: pip install azure-mgmt-authorization")
    return _authorization_client


async def list_role_assignments(resource_group: Optional[str] = None) -> str:
    """List role assignments (RBAC) for the subscription or a resource group.
    
    Args:
        resource_group: Optional resource group to filter by
        
    Returns:
        Formatted list of role assignments
    """
    try:
        client = _get_authorization_client()
        
        if resource_group:
            scope = f"/subscriptions/{get_subscription_id()}/resourceGroups/{resource_group}"
            assignments = client.role_assignments.list_for_scope(scope)
        else:
            assignments = client.role_assignments.list_for_subscription()
        
        formatted = []
        for assignment in assignments:
            # Extract principal info
            principal_id = assignment.principal_id or "N/A"
            principal_type = assignment.principal_type or "N/A"
            role_id = assignment.role_definition_id.split("/")[-1] if assignment.role_definition_id else "N/A"
            
            formatted.append(
                f"Principal: {principal_id} ({principal_type})\n"
                f"Role Definition ID: {role_id}\n"
                f"Scope: {assignment.scope}"
            )
        
        if not formatted:
            return "No role assignments found."
        
        return f"Role Assignments ({len(formatted)} found):\n\n" + "\n---\n".join(formatted[:20])  # Limit to 20
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list role assignments")
        logger.error(error_msg)
        return error_msg


async def list_role_definitions() -> str:
    """List available role definitions (built-in and custom roles).
    
    Returns:
        Formatted list of common role definitions
    """
    try:
        client = _get_authorization_client()
        scope = f"/subscriptions/{get_subscription_id()}"
        roles = client.role_definitions.list(scope)
        
        formatted = []
        for role in roles:
            if role.role_type == "BuiltInRole":  # Focus on built-in roles
                formatted.append(
                    f"Name: {role.role_name}\n"
                    f"ID: {role.name}\n"
                    f"Description: {role.description[:100] if role.description else 'N/A'}..."
                )
        
        if not formatted:
            return "No role definitions found."
        
        # Return first 15 common roles
        return f"Built-in Role Definitions ({len(formatted)} found, showing first 15):\n\n" + "\n---\n".join(formatted[:15])
        
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
    """Create a new role assignment (RBAC).
    
    Args:
        principal_id: Object ID of the principal (user, group, or service principal)
        role_definition_name: Role name (e.g., 'Contributor', 'Reader', 'AcrPull')
        resource_group: Resource group scope (optional, uses subscription if not provided)
        scope: Full resource scope (optional, overrides resource_group)
        
    Returns:
        Result of the role assignment creation
    """
    try:
        authorization_client = _get_authorization_client()
        subscription_id = get_subscription_id()
        
        # Determine scope
        if scope:
            scope = scope
        elif resource_group:
            scope = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        else:
            scope = f"/subscriptions/{subscription_id}"
        
        # Get role definition ID by role name
        roles = authorization_client.role_definitions.list(scope)
        role_def_id = None
        
        for role_def in roles:
            if role_def.role_name == role_definition_name:
                role_def_id = role_def.id
                break
        
        if not role_def_id:
            return f"Error: Role '{role_definition_name}' not found at scope '{scope}'. Available roles can be listed with list_role_definitions."
        
        # Generate unique assignment name
        import uuid
        assignment_name = str(uuid.uuid4())
        
        # Create role assignment
        from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
        
        assignment_params = RoleAssignmentCreateParameters(
            role_definition_id=role_def_id,
            principal_id=principal_id,
            principal_type="ServicePrincipal",
        )
        
        authorization_client.role_assignments.create(
            scope, assignment_name, assignment_params
        )
        
        return (
            f"Role assignment created successfully!\n"
            f"{'='*60}\n"
            f"Principal ID: {principal_id}\n"
            f"Role: {role_definition_name}\n"
            f"Scope: {scope}\n"
            f"Assignment ID: {assignment_name}"
        )
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to create role assignment for principal '{principal_id}'")
        logger.error(error_msg)
        return error_msg


async def delete_role_assignment(assignment_id: str) -> str:
    """Delete a role assignment.
    
    Args:
        assignment_id: Role assignment ID to delete
        
    Returns:
        Result of the deletion
    """
    try:
        authorization_client = _get_authorization_client()
        
        # Parse assignment ID to get scope and assignment name
        parts = assignment_id.split("/")
        if len(parts) < 9:
            return "Error: Invalid assignment_id format"
        
        # Get the last part as assignment name
        assignment_name = parts[-1]
        
        # Remove assignment name from parts to get scope
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
        principal_id: Object ID of the principal
        resource_group: Resource group to filter by (optional)
        
    Returns:
        Formatted list of role assignments
    """
    try:
        authorization_client = _get_authorization_client()
        subscription_id = get_subscription_id()
        
        if resource_group:
            scope = f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
            assignments = authorization_client.role_assignments.list_for_scope(scope)
        else:
            assignments = authorization_client.role_assignments.list_for_subscription()
        
        # Filter by principal ID
        filtered = [a for a in assignments if a.principal_id == principal_id]
        
        if not filtered:
            return f"No role assignments found for principal '{principal_id}'."
        
        formatted = []
        for assignment in filtered:
            # Get role definition name
            role_id = assignment.role_definition_id.split("/")[-1] if assignment.role_definition_id else "N/A"
            formatted.append(
                f"Scope: {assignment.scope}\n"
                f"Role ID: {role_id}\n"
                f"Principal: {principal_id}\n"
                f"Assignment ID: {assignment.name}"
            )
        
        return f"Role Assignments for Principal '{principal_id}':\n\n" + "\n---\n".join(formatted)
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to list role assignments for principal '{principal_id}'")
        logger.error(error_msg)
        return error_msg


async def list_resource_locks(resource_group: Optional[str] = None) -> str:
    """List resource locks in the subscription or a resource group.
    
    Args:
        resource_group: Optional resource group to filter by
        
    Returns:
        Formatted list of resource locks
    """
    try:
        resource_client = _get_resource_client()
        
        if resource_group:
            locks = resource_client.management_locks.list_at_resource_group_level(resource_group)
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
        
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list resource locks")
        logger.error(error_msg)
        return error_msg


async def create_resource_lock(resource_group: str, lock_name: str, lock_level: str = "CanNotDelete", notes: str = "") -> str:
    """Create a resource lock on a resource group.
    
    Args:
        resource_group: Resource group to lock
        lock_name: Name for the lock
        lock_level: Lock level - CanNotDelete or ReadOnly
        notes: Optional notes about the lock
        
    Returns:
        Result of the create operation
    """
    try:
        if lock_level not in ["CanNotDelete", "ReadOnly"]:
            return "Error: lock_level must be 'CanNotDelete' or 'ReadOnly'"
        
        resource_client = _get_resource_client()
        
        lock_params = {
            "level": lock_level,
            "notes": notes or f"Lock created via azops-mcp"
        }
        
        result = resource_client.management_locks.create_or_update_at_resource_group_level(
            resource_group, lock_name, lock_params
        )
        
        return (
            f"Resource lock created successfully!\n"
            f"Name: {result.name}\n"
            f"Level: {result.level}\n"
            f"Resource Group: {resource_group}"
        )
        
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to create lock '{lock_name}'")
        logger.error(error_msg)
        return error_msg


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
        resource_client.management_locks.delete_at_resource_group_level(resource_group, lock_name)
        
        return f"Resource lock '{lock_name}' deleted from '{resource_group}'."
        
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to delete lock '{lock_name}'")
        logger.error(error_msg)
        return error_msg


async def list_tags(resource_group: Optional[str] = None) -> str:
    """List tags used in the subscription or on a resource group.
    
    Args:
        resource_group: Optional resource group to get tags from
        
    Returns:
        Formatted list of tags
    """
    try:
        resource_client = _get_resource_client()
        
        if resource_group:
            # Get tags from the resource group itself
            rg = resource_client.resource_groups.get(resource_group)
            tags = rg.tags or {}
            
            if not tags:
                return f"No tags found on resource group '{resource_group}'."
            
            formatted = [f"{k}: {v}" for k, v in tags.items()]
            return f"Tags on '{resource_group}':\n" + "\n".join(formatted)
        else:
            # List all tag names in subscription
            tags_list = resource_client.tags.list()
            
            formatted = []
            for tag in tags_list:
                values = [v.tag_value for v in (tag.values or [])][:5]  # First 5 values
                formatted.append(f"{tag.tag_name}: {', '.join(values) if values else '(no values)'}")
            
            if not formatted:
                return "No tags found in subscription."
            
            return f"Tags in Subscription ({len(formatted)} found):\n" + "\n".join(formatted[:20])
        
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list tags")
        logger.error(error_msg)
        return error_msg


async def update_resource_group_tags(resource_group: str, tags: Dict[str, str], merge: bool = True) -> str:
    """Update tags on a resource group.
    
    Args:
        resource_group: Resource group to update
        tags: Dictionary of tags to set
        merge: If True, merge with existing tags. If False, replace all tags.
        
    Returns:
        Result of the update operation
    """
    try:
        resource_client = _get_resource_client()
        
        # Get current resource group
        rg = resource_client.resource_groups.get(resource_group)
        
        if merge:
            # Merge with existing tags
            existing_tags = rg.tags or {}
            existing_tags.update(tags)
            new_tags = existing_tags
        else:
            new_tags = tags
        
        # Update resource group
        rg.tags = new_tags
        result = resource_client.resource_groups.create_or_update(resource_group, rg)
        
        tag_list = [f"  {k}: {v}" for k, v in (result.tags or {}).items()]
        return (
            f"Tags updated on '{resource_group}':\n" + "\n".join(tag_list)
        )
        
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to update tags on '{resource_group}'")
        logger.error(error_msg)
        return error_msg


async def get_activity_log(resource_group: Optional[str] = None, days: int = 1) -> str:
    """Get recent activity log entries (audit log).
    
    Args:
        resource_group: Optional resource group to filter by
        days: Number of days to look back (1-7)
        
    Returns:
        Recent activity log entries
    """
    try:
        from azure.mgmt.monitor import MonitorManagementClient
        from datetime import datetime, timedelta
        
        subscription_id = get_subscription_id()
        if not subscription_id:
            return "Error: Subscription ID not configured"
        
        monitor_client = MonitorManagementClient(
            credential=_get_azure_credential(),
            subscription_id=subscription_id,
        )
        
        # Build filter
        days = min(max(days, 1), 7)  # Clamp to 1-7 days
        start_time = datetime.utcnow() - timedelta(days=days)
        
        filter_str = f"eventTimestamp ge '{start_time.isoformat()}Z'"
        if resource_group:
            filter_str += f" and resourceGroupName eq '{resource_group}'"
        
        # Get activity logs
        logs = monitor_client.activity_logs.list(filter=filter_str)
        
        formatted = []
        for log in logs:
            if len(formatted) >= 20:  # Limit to 20 entries
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
        
        return f"Activity Log (last {days} day(s), showing {len(formatted)} entries):\n\n" + "\n---\n".join(formatted)
        
    except ImportError:
        return "Azure Monitor SDK not installed. Run: pip install azure-mgmt-monitor"
    except Exception as e:
        error_msg = format_error_message(e, "Failed to get activity log")
        logger.error(error_msg)
        return error_msg


async def clear_account() -> str:
    """Clear cached Azure credentials and subscription override (similar to 'az account clear').

    Resets the runtime subscription ID override and clears all cached Azure SDK
    clients and credentials so the next call re-authenticates from scratch.

    Returns:
        Confirmation message
    """
    try:
        clear_subscription_id()
        reset_azure_credentials()
        return (
            "Azure account cache cleared successfully.\n"
            "  - Runtime subscription override removed\n"
            "  - Cached credentials cleared\n"
            "  - Cached SDK clients cleared\n"
            "\nNext Azure operation will re-authenticate."
        )
    except Exception as e:
        error_msg = format_error_message(e, "Failed to clear account cache")
        logger.error(error_msg)
        return error_msg


async def get_access_token(resource: str = "https://management.azure.com/.default") -> str:
    """Get an Azure access token for the current credentials (similar to 'az account get-access-token').

    Args:
        resource: The resource/scope to obtain a token for.
                  Default: https://management.azure.com/.default (Azure Resource Manager).

    Returns:
        Token information including the access token, expiry, subscription, and tenant.
    """
    try:
        from datetime import datetime

        credential = _get_azure_credential()
        token = credential.get_token(resource)

        subscription_id = get_subscription_id() or "Not configured"
        tenant_id = config.azure_tenant_id or "N/A (using CLI/Managed Identity)"

        expiry = datetime.fromtimestamp(token.expires_on)

        # Mask the token for security — show first 8 and last 4 chars
        token_value = token.token
        if len(token_value) > 16:
            masked_token = f"{token_value[:8]}...{token_value[-4:]}"
        else:
            masked_token = "****"

        return (
            f"Azure Access Token:\n"
            f"{'='*50}\n"
            f"Token (masked): {masked_token}\n"
            f"Token Length: {len(token_value)} chars\n"
            f"Expires On: {expiry.isoformat()}\n"
            f"Subscription: {subscription_id}\n"
            f"Tenant: {tenant_id}\n"
            f"Resource: {resource}\n"
            f"Token Type: Bearer\n"
            f"\nNote: Full token is not shown for security. "
            f"Use this tool programmatically if you need the raw token."
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to get access token")
        logger.error(error_msg)
        return error_msg


# =============================================================================
# App Configuration — management + data plane
# =============================================================================


def _get_appconfig_mgmt_client():
    """Get Azure App Configuration Management client."""
    global _appconfig_mgmt_client
    if _appconfig_mgmt_client is None:
        try:
            from azure.mgmt.appconfiguration import AppConfigurationManagementClient

            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError("Subscription ID not configured")

            _appconfig_mgmt_client = AppConfigurationManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError:
            raise ImportError("Azure App Configuration SDK not installed. Run: pip install azure-mgmt-appconfiguration")
    return _appconfig_mgmt_client


def _get_appconfig_data_client(endpoint: str):
    """Get Azure App Configuration data-plane client for a specific store."""
    global _appconfig_data_clients
    if endpoint not in _appconfig_data_clients:
        try:
            from azure.appconfiguration import AzureAppConfigurationClient

            _appconfig_data_clients[endpoint] = AzureAppConfigurationClient(
                base_url=endpoint,
                credential=_get_azure_credential(),
            )
        except ImportError:
            raise ImportError("Azure App Configuration data SDK not installed. Run: pip install azure-appconfiguration")
    return _appconfig_data_clients[endpoint]


async def _resolve_appconfig_endpoint(store_name: str, resource_group: str = "") -> str:
    """Resolve the endpoint URL for an App Configuration store.

    If resource_group is given, fetches directly. Otherwise searches across
    all stores in the subscription.
    """
    client = _get_appconfig_mgmt_client()

    if resource_group:
        store = client.configuration_stores.get(resource_group, store_name)
        return store.endpoint
    else:
        # Search across all stores
        stores = client.configuration_stores.list()
        for store in stores:
            if store.name == store_name:
                return store.endpoint
        raise ValueError(f"App Configuration store '{store_name}' not found in subscription")


async def appconfig_list(resource_group: str = "") -> str:
    """List App Configuration stores (similar to 'az appconfig list').

    Args:
        resource_group: Optional resource group to filter by

    Returns:
        Formatted list of App Configuration stores
    """
    try:
        client = _get_appconfig_mgmt_client()

        if resource_group:
            stores = client.configuration_stores.list_by_resource_group(resource_group)
        else:
            stores = client.configuration_stores.list()

        formatted = []
        for store in stores:
            sku = store.sku.name if store.sku else "N/A"
            formatted.append(
                f"Name: {store.name}\n"
                f"Location: {store.location}\n"
                f"Resource Group: {store.id.split('/')[4] if store.id else 'N/A'}\n"
                f"Endpoint: {store.endpoint}\n"
                f"SKU: {sku}\n"
                f"Provisioning State: {store.provisioning_state}"
            )

        if not formatted:
            scope = f"resource group '{resource_group}'" if resource_group else "subscription"
            return f"No App Configuration stores found in {scope}."

        return f"App Configuration Stores ({len(formatted)} found):\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list App Configuration stores")
        logger.error(error_msg)
        return error_msg


async def appconfig_show(store_name: str, resource_group: str) -> str:
    """Show details of an App Configuration store (similar to 'az appconfig show').

    Args:
        store_name: Name of the App Configuration store
        resource_group: Resource group containing the store

    Returns:
        Store details
    """
    try:
        client = _get_appconfig_mgmt_client()
        store = client.configuration_stores.get(resource_group, store_name)

        sku = store.sku.name if store.sku else "N/A"
        tags = ", ".join(f"{k}={v}" for k, v in (store.tags or {}).items()) or "None"

        output = (
            f"App Configuration Store:\n"
            f"{'='*50}\n"
            f"Name: {store.name}\n"
            f"Location: {store.location}\n"
            f"Resource Group: {resource_group}\n"
            f"Endpoint: {store.endpoint}\n"
            f"SKU: {sku}\n"
            f"Provisioning State: {store.provisioning_state}\n"
            f"Creation Date: {store.creation_date.isoformat() if store.creation_date else 'N/A'}\n"
            f"Soft Delete Retention (days): {store.soft_delete_retention_in_days or 'N/A'}\n"
            f"Public Network Access: {store.public_network_access or 'N/A'}\n"
            f"Disable Local Auth: {store.disable_local_auth or False}\n"
            f"Tags: {tags}\n"
            f"ID: {store.id}"
        )
        return output

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to show App Configuration store '{store_name}'")
        logger.error(error_msg)
        return error_msg


async def appconfig_kv_list(store_name: str, resource_group: str = "", key_filter: str = "*", label_filter: str = "") -> str:
    """List key-values in an App Configuration store (similar to 'az appconfig kv list').

    Args:
        store_name: Name of the App Configuration store
        resource_group: Optional resource group (speeds up endpoint lookup)
        key_filter: Key filter pattern (default '*' for all). Supports '*' wildcard.
        label_filter: Optional label filter

    Returns:
        Formatted list of key-value pairs
    """
    try:
        endpoint = await _resolve_appconfig_endpoint(store_name, resource_group)
        client = _get_appconfig_data_client(endpoint)

        kwargs = {"key_filter": key_filter}
        if label_filter:
            kwargs["label_filter"] = label_filter

        settings = client.list_configuration_settings(**kwargs)

        formatted = []
        count = 0
        for setting in settings:
            if count >= 50:
                formatted.append("... (truncated, more key-values exist)")
                break
            value_preview = (setting.value or "")[:100]
            if setting.value and len(setting.value) > 100:
                value_preview += "..."
            formatted.append(
                f"Key: {setting.key}\n"
                f"Value: {value_preview}\n"
                f"Label: {setting.label or '(no label)'}\n"
                f"Content Type: {setting.content_type or 'N/A'}\n"
                f"Last Modified: {setting.last_modified.isoformat() if setting.last_modified else 'N/A'}"
            )
            count += 1

        if not formatted:
            return f"No key-values found in store '{store_name}' matching key='{key_filter}'."

        return f"Key-Values in '{store_name}' ({count} shown):\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to list key-values in '{store_name}'")
        logger.error(error_msg)
        return error_msg


async def appconfig_kv_show(store_name: str, key: str, resource_group: str = "", label: str = "") -> str:
    """Show a specific key-value in an App Configuration store (similar to 'az appconfig kv show').

    Args:
        store_name: Name of the App Configuration store
        key: The configuration key to retrieve
        resource_group: Optional resource group
        label: Optional label (default: no label)

    Returns:
        Key-value details
    """
    try:
        endpoint = await _resolve_appconfig_endpoint(store_name, resource_group)
        client = _get_appconfig_data_client(endpoint)

        setting = client.get_configuration_setting(key=key, label=label or None)

        return (
            f"App Configuration Key-Value:\n"
            f"{'='*50}\n"
            f"Key: {setting.key}\n"
            f"Value: {setting.value}\n"
            f"Label: {setting.label or '(no label)'}\n"
            f"Content Type: {setting.content_type or 'N/A'}\n"
            f"Last Modified: {setting.last_modified.isoformat() if setting.last_modified else 'N/A'}\n"
            f"Read Only: {setting.read_only}\n"
            f"ETag: {setting.etag or 'N/A'}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to get key '{key}' from '{store_name}'")
        logger.error(error_msg)
        return error_msg


async def appconfig_kv_set(store_name: str, key: str, value: str, resource_group: str = "", label: str = "", content_type: str = "") -> str:
    """Set a key-value in an App Configuration store (similar to 'az appconfig kv set').

    Args:
        store_name: Name of the App Configuration store
        key: The configuration key
        value: The value to set
        resource_group: Optional resource group
        label: Optional label
        content_type: Optional content type (e.g. 'application/json')

    Returns:
        Confirmation with the set key-value
    """
    try:
        endpoint = await _resolve_appconfig_endpoint(store_name, resource_group)
        client = _get_appconfig_data_client(endpoint)

        from azure.appconfiguration import ConfigurationSetting

        setting = ConfigurationSetting(
            key=key,
            value=value,
            label=label or None,
            content_type=content_type or None,
        )

        result = client.set_configuration_setting(setting)

        return (
            f"Key-value set successfully in '{store_name}':\n"
            f"{'='*50}\n"
            f"Key: {result.key}\n"
            f"Value: {result.value}\n"
            f"Label: {result.label or '(no label)'}\n"
            f"Last Modified: {result.last_modified.isoformat() if result.last_modified else 'N/A'}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to set key '{key}' in '{store_name}'")
        logger.error(error_msg)
        return error_msg


async def appconfig_kv_delete(store_name: str, key: str, resource_group: str = "", label: str = "") -> str:
    """Delete a key-value from an App Configuration store (similar to 'az appconfig kv delete').

    Args:
        store_name: Name of the App Configuration store
        key: The configuration key to delete
        resource_group: Optional resource group
        label: Optional label

    Returns:
        Confirmation message
    """
    try:
        endpoint = await _resolve_appconfig_endpoint(store_name, resource_group)
        client = _get_appconfig_data_client(endpoint)

        client.delete_configuration_setting(key=key, label=label or None)

        label_info = f" (label='{label}')" if label else ""
        return f"Key-value '{key}'{label_info} deleted from '{store_name}'."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to delete key '{key}' from '{store_name}'")
        logger.error(error_msg)
        return error_msg


# =============================================================================
# App Service — plans & web apps
# =============================================================================


def _get_web_client():
    """Get Azure Web Site Management client."""
    global _web_client
    if _web_client is None:
        try:
            from azure.mgmt.web import WebSiteManagementClient

            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError("Subscription ID not configured")

            _web_client = WebSiteManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError:
            raise ImportError("Azure Web SDK not installed. Run: pip install azure-mgmt-web")
    return _web_client


async def appservice_plan_list(resource_group: str = "") -> str:
    """List App Service plans (similar to 'az appservice plan list').

    Args:
        resource_group: Optional resource group to filter by

    Returns:
        Formatted list of App Service plans
    """
    try:
        client = _get_web_client()

        if resource_group:
            plans = client.app_service_plans.list_by_resource_group(resource_group)
        else:
            plans = client.app_service_plans.list()

        formatted = []
        for plan in plans:
            sku = f"{plan.sku.name} ({plan.sku.tier})" if plan.sku else "N/A"
            formatted.append(
                f"Name: {plan.name}\n"
                f"Resource Group: {plan.resource_group}\n"
                f"Location: {plan.location}\n"
                f"SKU: {sku}\n"
                f"Status: {plan.status or 'N/A'}\n"
                f"Kind: {plan.kind or 'N/A'}\n"
                f"Workers: {plan.number_of_workers or 0}"
            )

        if not formatted:
            scope = f"resource group '{resource_group}'" if resource_group else "subscription"
            return f"No App Service plans found in {scope}."

        return f"App Service Plans ({len(formatted)} found):\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list App Service plans")
        logger.error(error_msg)
        return error_msg


async def appservice_plan_show(name: str, resource_group: str) -> str:
    """Show details of an App Service plan (similar to 'az appservice plan show').

    Args:
        name: App Service plan name
        resource_group: Resource group containing the plan

    Returns:
        Plan details
    """
    try:
        client = _get_web_client()
        plan = client.app_service_plans.get(resource_group, name)

        sku = f"{plan.sku.name} ({plan.sku.tier})" if plan.sku else "N/A"
        sku_capacity = str(plan.sku.capacity) if plan.sku else "N/A"

        output = (
            f"App Service Plan:\n"
            f"{'='*50}\n"
            f"Name: {plan.name}\n"
            f"Resource Group: {resource_group}\n"
            f"Location: {plan.location}\n"
            f"SKU: {sku}\n"
            f"SKU Capacity: {sku_capacity}\n"
            f"Status: {plan.status or 'N/A'}\n"
            f"Kind: {plan.kind or 'N/A'}\n"
            f"Reserved (Linux): {plan.reserved or False}\n"
            f"Workers: {plan.number_of_workers or 0}\n"
            f"Max Workers: {plan.maximum_number_of_workers or 'N/A'}\n"
            f"Number of Sites: {plan.number_of_sites or 0}\n"
            f"Provisioning State: {plan.provisioning_state or 'N/A'}\n"
            f"ID: {plan.id}"
        )
        return output

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to show App Service plan '{name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_list(resource_group: str = "") -> str:
    """List web apps (similar to 'az webapp list').

    Args:
        resource_group: Optional resource group to filter by

    Returns:
        Formatted list of web apps
    """
    try:
        client = _get_web_client()

        if resource_group:
            apps = client.web_apps.list_by_resource_group(resource_group)
        else:
            apps = client.web_apps.list()

        formatted = []
        for app in apps:
            formatted.append(
                f"Name: {app.name}\n"
                f"Resource Group: {app.resource_group}\n"
                f"Location: {app.location}\n"
                f"State: {app.state or 'N/A'}\n"
                f"Default Hostname: {app.default_host_name or 'N/A'}\n"
                f"Kind: {app.kind or 'N/A'}\n"
                f"HTTPS Only: {app.https_only or False}"
            )

        if not formatted:
            scope = f"resource group '{resource_group}'" if resource_group else "subscription"
            return f"No web apps found in {scope}."

        return f"Web Apps ({len(formatted)} found):\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list web apps")
        logger.error(error_msg)
        return error_msg


async def webapp_show(name: str, resource_group: str) -> str:
    """Show details of a web app (similar to 'az webapp show').

    Args:
        name: Web app name
        resource_group: Resource group containing the web app

    Returns:
        Web app details
    """
    try:
        client = _get_web_client()
        app = client.web_apps.get(resource_group, name)

        plan_name = app.server_farm_id.split("/")[-1] if app.server_farm_id else "N/A"
        outbound_ips = app.outbound_ip_addresses or "N/A"
        tags = ", ".join(f"{k}={v}" for k, v in (app.tags or {}).items()) or "None"

        output = (
            f"Web App:\n"
            f"{'='*50}\n"
            f"Name: {app.name}\n"
            f"Resource Group: {resource_group}\n"
            f"Location: {app.location}\n"
            f"State: {app.state or 'N/A'}\n"
            f"Default Hostname: {app.default_host_name or 'N/A'}\n"
            f"Kind: {app.kind or 'N/A'}\n"
            f"App Service Plan: {plan_name}\n"
            f"HTTPS Only: {app.https_only or False}\n"
            f"Client Cert Enabled: {app.client_cert_enabled or False}\n"
            f"Availability: {app.availability_state or 'N/A'}\n"
            f"Outbound IPs: {outbound_ips}\n"
            f"Last Modified: {app.last_modified_time_utc.isoformat() if app.last_modified_time_utc else 'N/A'}\n"
            f"Tags: {tags}\n"
            f"ID: {app.id}"
        )
        return output

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to show web app '{name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_start(name: str, resource_group: str) -> str:
    """Start a web app (similar to 'az webapp start').

    Args:
        name: Web app name
        resource_group: Resource group containing the web app

    Returns:
        Confirmation message
    """
    try:
        client = _get_web_client()
        client.web_apps.start(resource_group, name)
        return f"Web app '{name}' started successfully."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to start web app '{name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_stop(name: str, resource_group: str) -> str:
    """Stop a web app (similar to 'az webapp stop').

    Args:
        name: Web app name
        resource_group: Resource group containing the web app

    Returns:
        Confirmation message
    """
    try:
        client = _get_web_client()
        client.web_apps.stop(resource_group, name)
        return f"Web app '{name}' stopped successfully."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to stop web app '{name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_restart(name: str, resource_group: str) -> str:
    """Restart a web app (similar to 'az webapp restart').

    Args:
        name: Web app name
        resource_group: Resource group containing the web app

    Returns:
        Confirmation message
    """
    try:
        client = _get_web_client()
        client.web_apps.restart(resource_group, name)
        return f"Web app '{name}' restarted successfully."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to restart web app '{name}'")
        logger.error(error_msg)
        return error_msg


# =============================================================================
# Virtual Networks — vnet, subnet, peering
# =============================================================================


def _get_network_client():
    """Get Azure Network Management client."""
    global _network_client
    if _network_client is None:
        try:
            from azure.mgmt.network import NetworkManagementClient

            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError("Subscription ID not configured")

            _network_client = NetworkManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError:
            raise ImportError("Azure Network SDK not installed. Run: pip install azure-mgmt-network")
    return _network_client


async def vnet_list(resource_group: str = "") -> str:
    """List virtual networks (similar to 'az network vnet list').

    Args:
        resource_group: Optional resource group to filter by

    Returns:
        Formatted list of virtual networks
    """
    try:
        client = _get_network_client()

        if resource_group:
            vnets = client.virtual_networks.list(resource_group)
        else:
            vnets = client.virtual_networks.list_all()

        formatted = []
        for vnet in vnets:
            rg = vnet.id.split("/")[4] if vnet.id else "N/A"
            address_space = ", ".join(vnet.address_space.address_prefixes) if vnet.address_space and vnet.address_space.address_prefixes else "N/A"
            subnet_count = len(vnet.subnets) if vnet.subnets else 0
            formatted.append(
                f"Name: {vnet.name}\n"
                f"Resource Group: {rg}\n"
                f"Location: {vnet.location}\n"
                f"Address Space: {address_space}\n"
                f"Subnets: {subnet_count}\n"
                f"Provisioning State: {vnet.provisioning_state or 'N/A'}"
            )

        if not formatted:
            scope = f"resource group '{resource_group}'" if resource_group else "subscription"
            return f"No virtual networks found in {scope}."

        return f"Virtual Networks ({len(formatted)} found):\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list virtual networks")
        logger.error(error_msg)
        return error_msg


async def vnet_show(name: str, resource_group: str) -> str:
    """Show details of a virtual network (similar to 'az network vnet show').

    Args:
        name: Virtual network name
        resource_group: Resource group containing the VNet

    Returns:
        VNet details
    """
    try:
        client = _get_network_client()
        vnet = client.virtual_networks.get(resource_group, name)

        address_space = ", ".join(vnet.address_space.address_prefixes) if vnet.address_space and vnet.address_space.address_prefixes else "N/A"
        dns_servers = ", ".join(vnet.dhcp_options.dns_servers) if vnet.dhcp_options and vnet.dhcp_options.dns_servers else "Azure default"
        tags = ", ".join(f"{k}={v}" for k, v in (vnet.tags or {}).items()) or "None"

        output = (
            f"Virtual Network:\n"
            f"{'='*50}\n"
            f"Name: {vnet.name}\n"
            f"Resource Group: {resource_group}\n"
            f"Location: {vnet.location}\n"
            f"Address Space: {address_space}\n"
            f"DNS Servers: {dns_servers}\n"
            f"Provisioning State: {vnet.provisioning_state or 'N/A'}\n"
            f"Enable DDoS Protection: {vnet.enable_ddos_protection or False}\n"
            f"Tags: {tags}\n"
            f"ID: {vnet.id}\n"
        )

        # List subnets
        if vnet.subnets:
            output += f"\nSubnets ({len(vnet.subnets)}):\n"
            for subnet in vnet.subnets:
                prefix = subnet.address_prefix or (", ".join(subnet.address_prefixes) if subnet.address_prefixes else "N/A")
                nsg_name = subnet.network_security_group.id.split("/")[-1] if subnet.network_security_group else "None"
                output += f"  - {subnet.name}: {prefix} (NSG: {nsg_name})\n"

        # List peerings
        if vnet.virtual_network_peerings:
            output += f"\nPeerings ({len(vnet.virtual_network_peerings)}):\n"
            for peering in vnet.virtual_network_peerings:
                remote = peering.remote_virtual_network.id.split("/")[-1] if peering.remote_virtual_network else "N/A"
                output += f"  - {peering.name}: -> {remote} (State: {peering.peering_state or 'N/A'})\n"

        return output

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to show virtual network '{name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_create(name: str, resource_group: str, address_prefix: str = "10.0.0.0/16", location: str = "") -> str:
    """Create a virtual network (similar to 'az network vnet create').

    Args:
        name: Virtual network name
        resource_group: Resource group to create the VNet in
        address_prefix: Address space CIDR (default 10.0.0.0/16)
        location: Azure region (defaults to resource group location)

    Returns:
        Created VNet details
    """
    try:
        client = _get_network_client()

        # Resolve location from resource group if not specified
        if not location:
            resource_client = _get_resource_client()
            rg = resource_client.resource_groups.get(resource_group)
            location = rg.location

        vnet_params = {
            "location": location,
            "address_space": {"address_prefixes": [address_prefix]},
            "subnets": [
                {"name": "default", "address_prefix": address_prefix.rsplit(".", 1)[0] + ".0/24"}
            ],
        }

        poller = client.virtual_networks.begin_create_or_update(resource_group, name, vnet_params)
        result = poller.result()

        address_space = ", ".join(result.address_space.address_prefixes) if result.address_space else "N/A"
        return (
            f"Virtual network created successfully!\n"
            f"{'='*50}\n"
            f"Name: {result.name}\n"
            f"Resource Group: {resource_group}\n"
            f"Location: {result.location}\n"
            f"Address Space: {address_space}\n"
            f"Default Subnet: {result.subnets[0].name} ({result.subnets[0].address_prefix})\n"
            f"ID: {result.id}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to create virtual network '{name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_delete(name: str, resource_group: str) -> str:
    """Delete a virtual network (similar to 'az network vnet delete').

    Args:
        name: Virtual network name
        resource_group: Resource group containing the VNet

    Returns:
        Confirmation message
    """
    try:
        client = _get_network_client()
        poller = client.virtual_networks.begin_delete(resource_group, name)
        poller.result()
        return f"Virtual network '{name}' deleted from '{resource_group}'."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to delete virtual network '{name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_subnet_list(vnet_name: str, resource_group: str) -> str:
    """List subnets in a virtual network (similar to 'az network vnet subnet list').

    Args:
        vnet_name: Virtual network name
        resource_group: Resource group containing the VNet

    Returns:
        Formatted list of subnets
    """
    try:
        client = _get_network_client()
        subnets = client.subnets.list(resource_group, vnet_name)

        formatted = []
        for subnet in subnets:
            prefix = subnet.address_prefix or (", ".join(subnet.address_prefixes) if subnet.address_prefixes else "N/A")
            nsg_name = subnet.network_security_group.id.split("/")[-1] if subnet.network_security_group else "None"
            delegations = ", ".join(d.service_name for d in (subnet.delegations or [])) or "None"
            formatted.append(
                f"Name: {subnet.name}\n"
                f"Address Prefix: {prefix}\n"
                f"NSG: {nsg_name}\n"
                f"Delegations: {delegations}\n"
                f"Provisioning State: {subnet.provisioning_state or 'N/A'}"
            )

        if not formatted:
            return f"No subnets found in virtual network '{vnet_name}'."

        return f"Subnets in '{vnet_name}' ({len(formatted)} found):\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to list subnets in '{vnet_name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_subnet_show(vnet_name: str, subnet_name: str, resource_group: str) -> str:
    """Show details of a subnet (similar to 'az network vnet subnet show').

    Args:
        vnet_name: Virtual network name
        subnet_name: Subnet name
        resource_group: Resource group containing the VNet

    Returns:
        Subnet details
    """
    try:
        client = _get_network_client()
        subnet = client.subnets.get(resource_group, vnet_name, subnet_name)

        prefix = subnet.address_prefix or (", ".join(subnet.address_prefixes) if subnet.address_prefixes else "N/A")
        nsg_name = subnet.network_security_group.id.split("/")[-1] if subnet.network_security_group else "None"
        route_table = subnet.route_table.id.split("/")[-1] if subnet.route_table else "None"
        delegations = ", ".join(d.service_name for d in (subnet.delegations or [])) or "None"
        service_endpoints = ", ".join(ep.service for ep in (subnet.service_endpoints or [])) or "None"
        ip_configs = len(subnet.ip_configurations) if subnet.ip_configurations else 0
        private_endpoint_policy = subnet.private_endpoint_network_policies or "N/A"

        return (
            f"Subnet:\n"
            f"{'='*50}\n"
            f"Name: {subnet.name}\n"
            f"VNet: {vnet_name}\n"
            f"Resource Group: {resource_group}\n"
            f"Address Prefix: {prefix}\n"
            f"NSG: {nsg_name}\n"
            f"Route Table: {route_table}\n"
            f"Delegations: {delegations}\n"
            f"Service Endpoints: {service_endpoints}\n"
            f"Private Endpoint Policy: {private_endpoint_policy}\n"
            f"Connected Devices: {ip_configs}\n"
            f"Provisioning State: {subnet.provisioning_state or 'N/A'}\n"
            f"ID: {subnet.id}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to show subnet '{subnet_name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_subnet_create(vnet_name: str, subnet_name: str, resource_group: str, address_prefix: str) -> str:
    """Create a subnet in a virtual network (similar to 'az network vnet subnet create').

    Args:
        vnet_name: Virtual network name
        subnet_name: Name for the new subnet
        resource_group: Resource group containing the VNet
        address_prefix: Subnet address prefix in CIDR notation (e.g. 10.0.1.0/24)

    Returns:
        Created subnet details
    """
    try:
        client = _get_network_client()

        subnet_params = {"address_prefix": address_prefix}
        poller = client.subnets.begin_create_or_update(resource_group, vnet_name, subnet_name, subnet_params)
        result = poller.result()

        return (
            f"Subnet created successfully!\n"
            f"{'='*50}\n"
            f"Name: {result.name}\n"
            f"VNet: {vnet_name}\n"
            f"Address Prefix: {result.address_prefix}\n"
            f"Provisioning State: {result.provisioning_state or 'N/A'}\n"
            f"ID: {result.id}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to create subnet '{subnet_name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_subnet_delete(vnet_name: str, subnet_name: str, resource_group: str) -> str:
    """Delete a subnet from a virtual network (similar to 'az network vnet subnet delete').

    Args:
        vnet_name: Virtual network name
        subnet_name: Subnet name to delete
        resource_group: Resource group containing the VNet

    Returns:
        Confirmation message
    """
    try:
        client = _get_network_client()
        poller = client.subnets.begin_delete(resource_group, vnet_name, subnet_name)
        poller.result()
        return f"Subnet '{subnet_name}' deleted from VNet '{vnet_name}'."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to delete subnet '{subnet_name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_peering_list(vnet_name: str, resource_group: str) -> str:
    """List peerings for a virtual network (similar to 'az network vnet peering list').

    Args:
        vnet_name: Virtual network name
        resource_group: Resource group containing the VNet

    Returns:
        Formatted list of peerings
    """
    try:
        client = _get_network_client()
        peerings = client.virtual_network_peerings.list(resource_group, vnet_name)

        formatted = []
        for p in peerings:
            remote = p.remote_virtual_network.id.split("/")[-1] if p.remote_virtual_network else "N/A"
            remote_rg = p.remote_virtual_network.id.split("/")[4] if p.remote_virtual_network and p.remote_virtual_network.id else "N/A"
            formatted.append(
                f"Name: {p.name}\n"
                f"Peering State: {p.peering_state or 'N/A'}\n"
                f"Remote VNet: {remote} (RG: {remote_rg})\n"
                f"Allow VNet Access: {p.allow_virtual_network_access}\n"
                f"Allow Forwarded Traffic: {p.allow_forwarded_traffic}\n"
                f"Allow Gateway Transit: {p.allow_gateway_transit}\n"
                f"Use Remote Gateways: {p.use_remote_gateways}\n"
                f"Provisioning State: {p.provisioning_state or 'N/A'}"
            )

        if not formatted:
            return f"No peerings found for virtual network '{vnet_name}'."

        return f"VNet Peerings for '{vnet_name}' ({len(formatted)} found):\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to list peerings for '{vnet_name}'")
        logger.error(error_msg)
        return error_msg


async def get_tenant_info() -> str:
    """Get Azure tenant information (similar to 'az account tenant list').
    
    Returns:
        Formatted tenant information
    """
    try:
        subscription_client = _get_subscription_client()
        tenants = subscription_client.tenants.list()
        
        formatted_tenants = []
        current_tenant_id = config.azure_tenant_id
        
        for tenant in tenants:
            is_current = " (current)" if tenant.tenant_id == current_tenant_id else ""
            
            details = [f"Tenant ID: {tenant.tenant_id}{is_current}"]
            
            if hasattr(tenant, 'display_name') and tenant.display_name:
                details.append(f"Display Name: {tenant.display_name}")
            if hasattr(tenant, 'default_domain') and tenant.default_domain:
                details.append(f"Default Domain: {tenant.default_domain}")
            if hasattr(tenant, 'tenant_type') and tenant.tenant_type:
                details.append(f"Tenant Type: {tenant.tenant_type}")
            if hasattr(tenant, 'country') and tenant.country:
                details.append(f"Country: {tenant.country}")
            
            formatted_tenants.append("\n".join(details))
        
        if not formatted_tenants:
            return "No tenants found for the current credentials."
        
        return f"Azure Tenants ({len(formatted_tenants)} found):\n\n" + "\n---\n".join(formatted_tenants)
        
    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to get tenant information")
        logger.error(error_msg)
        return error_msg
