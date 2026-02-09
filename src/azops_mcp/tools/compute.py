"""VM and VMSS management tools."""

import logging
from typing import Any, Dict, List

from ..utils.helpers import format_error_message
from ._clients import (
    _get_compute_client,
    _get_resource_client,
    _get_storage_client,
)

logger = logging.getLogger(__name__)


async def list_resources(
    resource_group: str, resource_type: str = "all"
) -> str:
    """List resources in a resource group.

    Args:
        resource_group: Resource group name
        resource_type: Filter by type - all, vm, storage, webapp, sql

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
            try:
                compute_client = _get_compute_client()
                vms = compute_client.virtual_machines.list(resource_group)
                for vm in vms:
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
                logger.warning("Failed to list VMs: %s", e)

        if resource_type in ["all", "storage"]:
            try:
                storage_client = _get_storage_client()
                accounts = storage_client.storage_accounts.list_by_resource_group(
                    resource_group
                )
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
                logger.warning("Failed to list storage accounts: %s", e)

        if resource_type in ["all", "webapp", "sql"]:
            try:
                resource_client = _get_resource_client()
                all_resources = resource_client.resources.list_by_resource_group(
                    resource_group
                )
                existing_ids = {r["id"] for r in resources}
                type_filters = {
                    "webapp": "Microsoft.Web",
                    "sql": "Microsoft.Sql",
                }
                filter_prefix = type_filters.get(resource_type) if resource_type != "all" else None

                for resource in all_resources:
                    if resource.id in existing_ids:
                        continue
                    if filter_prefix and (not resource.type or not resource.type.startswith(filter_prefix)):
                        continue
                    resources.append({
                        "type": resource.type.split("/")[-1] if resource.type else "Unknown",
                        "name": resource.name,
                        "id": resource.id,
                        "location": resource.location,
                        "status": "available",
                    })
            except Exception as e:
                logger.warning("Failed to list resources: %s", e)

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
        return format_error_message(e, f"Failed to list resources in {resource_group}")
    except Exception as e:
        logger.error("list_resources failed: %s", e)
        return format_error_message(e, f"Failed to list resources in {resource_group}")


async def get_resource_status(
    resource_group: str,
    resource_name: str,
    resource_type: str = "vm",
) -> str:
    """Get detailed status of a resource.

    Args:
        resource_group: Resource group name
        resource_name: Resource name
        resource_type: Type - vm or storage

    Returns:
        Formatted resource status
    """
    resource_type = resource_type.lower()

    try:
        if resource_type == "vm":
            compute_client = _get_compute_client()
            vm = compute_client.virtual_machines.get(resource_group, resource_name)
            instance_view = compute_client.virtual_machines.instance_view(
                resource_group, resource_name
            )
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
            account = storage_client.storage_accounts.get_properties(
                resource_group, resource_name
            )
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
            return f"Unsupported resource type: {resource_type}. Supported: vm, storage"

    except ImportError as e:
        return format_error_message(e, f"Failed to get status for {resource_name}")
    except Exception as e:
        logger.error("get_resource_status failed: %s", e)
        return format_error_message(e, f"Failed to get status for {resource_name}")


async def manage_vm(
    resource_group: str, vm_name: str, action: str
) -> str:
    """Start, stop, restart, or deallocate a VM.

    Args:
        resource_group: Resource group name
        vm_name: Virtual machine name
        action: start, stop, restart, or deallocate

    Returns:
        Result of the operation
    """
    action = action.lower()
    valid_actions = ["start", "stop", "restart", "deallocate"]

    if action not in valid_actions:
        return f"Invalid action: {action}. Valid actions: {', '.join(valid_actions)}"

    try:
        compute_client = _get_compute_client()

        if action == "start":
            poller = compute_client.virtual_machines.begin_start(
                resource_group, vm_name
            )
            poller.result()
            return f"VM '{vm_name}' started successfully."
        elif action == "stop":
            poller = compute_client.virtual_machines.begin_power_off(
                resource_group, vm_name
            )
            poller.result()
            return f"VM '{vm_name}' stopped successfully."
        elif action == "restart":
            poller = compute_client.virtual_machines.begin_restart(
                resource_group, vm_name
            )
            poller.result()
            return f"VM '{vm_name}' restarted successfully."
        elif action == "deallocate":
            poller = compute_client.virtual_machines.begin_deallocate(
                resource_group, vm_name
            )
            poller.result()
            return f"VM '{vm_name}' deallocated successfully."

    except ImportError as e:
        return format_error_message(e, f"Failed to {action} VM {vm_name}")
    except Exception as e:
        logger.error("manage_vm failed: %s", e)
        return format_error_message(e, f"Failed to {action} VM {vm_name}")


async def scale_vmss(
    resource_group: str, vmss_name: str, capacity: int
) -> str:
    """Scale a Virtual Machine Scale Set.

    Args:
        resource_group: Resource group name
        vmss_name: VM Scale Set name
        capacity: Target instance count (must be >= 0)

    Returns:
        Result of the scale operation
    """
    if capacity < 0:
        return "Error: capacity must be non-negative"

    try:
        compute_client = _get_compute_client()
        vmss = compute_client.virtual_machine_scale_sets.get(
            resource_group, vmss_name
        )
        current_capacity = vmss.sku.capacity if vmss.sku else 0

        vmss.sku.capacity = capacity
        poller = compute_client.virtual_machine_scale_sets.begin_create_or_update(
            resource_group, vmss_name, vmss
        )
        poller.result()

        return (
            f"VMSS Scaling Complete:\n"
            f"Name: {vmss_name}\n"
            f"Resource Group: {resource_group}\n"
            f"Previous Capacity: {current_capacity}\n"
            f"New Capacity: {capacity}"
        )

    except ImportError as e:
        return format_error_message(e, f"Failed to scale VMSS {vmss_name}")
    except Exception as e:
        logger.error("scale_vmss failed: %s", e)
        return format_error_message(e, f"Failed to scale VMSS {vmss_name}")
