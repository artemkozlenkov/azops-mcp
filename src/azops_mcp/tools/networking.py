"""Virtual network management tools."""

import logging
from typing import Any

from ..utils.helpers import format_error_message
from ._clients import _get_network_client, _get_resource_client

logger = logging.getLogger(__name__)


async def vnet_list(resource_group: str = "") -> str:
    """List virtual networks in a resource group or subscription.

    Args:
        resource_group: Resource group to filter by. If empty, list all in subscription.

    Returns:
        Formatted list of VNets with name, RG, location, address_space, subnet count, provisioning_state.
    """
    try:
        network_client = _get_network_client()

        if resource_group:
            vnets = network_client.virtual_networks.list(resource_group)
        else:
            vnets = network_client.virtual_networks.list_all()

        formatted = []
        for vnet in vnets:
            rg = vnet.id.split("/")[4] if vnet.id else "N/A"
            address_space = "N/A"
            if vnet.address_space and vnet.address_space.address_prefixes:
                address_space = ", ".join(vnet.address_space.address_prefixes)
            subnet_count = len(vnet.subnets) if vnet.subnets else 0
            formatted.append(
                f"Name: {vnet.name}\n"
                f"Resource Group: {rg}\n"
                f"Location: {vnet.location}\n"
                f"Address Space: {address_space}\n"
                f"Subnet Count: {subnet_count}\n"
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
    """Get virtual network details.

    Args:
        name: Virtual network name.
        resource_group: Resource group containing the VNet.

    Returns:
        VNet details including address space, DNS servers, DDoS protection, tags, subnets, peerings.
    """
    try:
        network_client = _get_network_client()
        vnet = network_client.virtual_networks.get(resource_group, name)

        address_space = "N/A"
        if vnet.address_space and vnet.address_space.address_prefixes:
            address_space = ", ".join(vnet.address_space.address_prefixes)

        dns_servers = "Azure default"
        if vnet.dhcp_options and vnet.dhcp_options.dns_servers:
            dns_servers = ", ".join(vnet.dhcp_options.dns_servers)

        ddos = vnet.enable_ddos_protection or False
        tags = ", ".join(f"{k}={v}" for k, v in (vnet.tags or {}).items()) or "None"

        output = (
            f"Virtual Network:\n"
            f"{'='*50}\n"
            f"Name: {vnet.name}\n"
            f"Resource Group: {resource_group}\n"
            f"Location: {vnet.location}\n"
            f"Address Space: {address_space}\n"
            f"DNS Servers: {dns_servers}\n"
            f"DDoS Protection: {ddos}\n"
            f"Tags: {tags}\n"
            f"Provisioning State: {vnet.provisioning_state or 'N/A'}\n"
            f"ID: {vnet.id}\n"
        )

        if vnet.subnets:
            output += f"\nSubnets ({len(vnet.subnets)}):\n"
            for subnet in vnet.subnets:
                prefix = subnet.address_prefix or (
                    ", ".join(subnet.address_prefixes) if subnet.address_prefixes else "N/A"
                )
                nsg_name = (
                    subnet.network_security_group.id.split("/")[-1]
                    if subnet.network_security_group
                    else "None"
                )
                output += f"  - {subnet.name}: {prefix} (NSG: {nsg_name})\n"

        if vnet.virtual_network_peerings:
            output += f"\nPeerings ({len(vnet.virtual_network_peerings)}):\n"
            for peering in vnet.virtual_network_peerings:
                remote = (
                    peering.remote_virtual_network.id.split("/")[-1]
                    if peering.remote_virtual_network
                    else "N/A"
                )
                output += f"  - {peering.name}: -> {remote} (State: {peering.peering_state or 'N/A'})\n"

        return output

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to show virtual network '{name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_create(
    name: str,
    resource_group: str,
    address_prefix: str = "10.0.0.0/16",
    location: str = "",
) -> str:
    """Create a virtual network.

    Args:
        name: Virtual network name.
        resource_group: Resource group to create the VNet in.
        address_prefix: Address space CIDR (default 10.0.0.0/16).
        location: Azure region. If empty, resolved from resource group.

    Returns:
        Created VNet details.
    """
    try:
        network_client = _get_network_client()
        resource_client = _get_resource_client()

        if not location:
            rg = resource_client.resource_groups.get(resource_group)
            location = rg.location

        default_subnet_prefix = address_prefix.rsplit(".", 1)[0] + ".0/24"
        vnet_params: dict[str, Any] = {
            "location": location,
            "address_space": {"address_prefixes": [address_prefix]},
            "subnets": [{"name": "default", "address_prefix": default_subnet_prefix}],
        }

        poller = network_client.virtual_networks.begin_create_or_update(
            resource_group, name, vnet_params
        )
        result = poller.result()

        address_space = "N/A"
        if result.address_space and result.address_space.address_prefixes:
            address_space = ", ".join(result.address_space.address_prefixes)

        default_subnet = ""
        if result.subnets:
            default_subnet = f"{result.subnets[0].name} ({result.subnets[0].address_prefix})"

        return (
            f"Virtual network created successfully!\n"
            f"{'='*50}\n"
            f"Name: {result.name}\n"
            f"Resource Group: {resource_group}\n"
            f"Location: {result.location}\n"
            f"Address Space: {address_space}\n"
            f"Default Subnet: {default_subnet}\n"
            f"ID: {result.id}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to create virtual network '{name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_delete(name: str, resource_group: str) -> str:
    """Delete a virtual network.

    Args:
        name: Virtual network name.
        resource_group: Resource group containing the VNet.

    Returns:
        Confirmation message.
    """
    try:
        network_client = _get_network_client()
        poller = network_client.virtual_networks.begin_delete(resource_group, name)
        poller.result()
        return f"Virtual network '{name}' deleted from '{resource_group}'."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to delete virtual network '{name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_subnet_list(vnet_name: str, resource_group: str) -> str:
    """List subnets in a virtual network.

    Args:
        vnet_name: Virtual network name.
        resource_group: Resource group containing the VNet.

    Returns:
        Formatted list of subnets (name, prefix, NSG, delegations, provisioning state).
    """
    try:
        network_client = _get_network_client()
        subnets = network_client.subnets.list(resource_group, vnet_name)

        formatted = []
        for subnet in subnets:
            prefix = subnet.address_prefix or (
                ", ".join(subnet.address_prefixes) if subnet.address_prefixes else "N/A"
            )
            nsg_name = (
                subnet.network_security_group.id.split("/")[-1]
                if subnet.network_security_group
                else "None"
            )
            delegations = (
                ", ".join(d.service_name for d in (subnet.delegations or [])) or "None"
            )
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


async def vnet_subnet_show(
    vnet_name: str, subnet_name: str, resource_group: str
) -> str:
    """Show subnet details.

    Args:
        vnet_name: Virtual network name.
        subnet_name: Subnet name.
        resource_group: Resource group containing the VNet.

    Returns:
        Subnet details including NSG, route table, delegations, service endpoints, IP configs count, private endpoint policy.
    """
    try:
        network_client = _get_network_client()
        subnet = network_client.subnets.get(resource_group, vnet_name, subnet_name)

        prefix = subnet.address_prefix or (
            ", ".join(subnet.address_prefixes) if subnet.address_prefixes else "N/A"
        )
        nsg_name = (
            subnet.network_security_group.id.split("/")[-1]
            if subnet.network_security_group
            else "None"
        )
        route_table = (
            subnet.route_table.id.split("/")[-1] if subnet.route_table else "None"
        )
        delegations = (
            ", ".join(d.service_name for d in (subnet.delegations or [])) or "None"
        )
        service_endpoints = (
            ", ".join(ep.service for ep in (subnet.service_endpoints or [])) or "None"
        )
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
            f"IP Configurations Count: {ip_configs}\n"
            f"Provisioning State: {subnet.provisioning_state or 'N/A'}\n"
            f"ID: {subnet.id}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to show subnet '{subnet_name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_subnet_create(
    vnet_name: str,
    subnet_name: str,
    resource_group: str,
    address_prefix: str,
) -> str:
    """Create a subnet in a virtual network.

    Args:
        vnet_name: Virtual network name.
        subnet_name: Name for the new subnet.
        resource_group: Resource group containing the VNet.
        address_prefix: Subnet address prefix in CIDR notation (e.g. 10.0.1.0/24).

    Returns:
        Created subnet details.
    """
    try:
        network_client = _get_network_client()
        subnet_params = {"address_prefix": address_prefix}

        poller = network_client.subnets.begin_create_or_update(
            resource_group, vnet_name, subnet_name, subnet_params
        )
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


async def vnet_subnet_delete(
    vnet_name: str, subnet_name: str, resource_group: str
) -> str:
    """Delete a subnet from a virtual network.

    Args:
        vnet_name: Virtual network name.
        subnet_name: Subnet name to delete.
        resource_group: Resource group containing the VNet.

    Returns:
        Confirmation message.
    """
    try:
        network_client = _get_network_client()
        poller = network_client.subnets.begin_delete(
            resource_group, vnet_name, subnet_name
        )
        poller.result()
        return f"Subnet '{subnet_name}' deleted from VNet '{vnet_name}'."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to delete subnet '{subnet_name}'")
        logger.error(error_msg)
        return error_msg


async def vnet_peering_list(vnet_name: str, resource_group: str) -> str:
    """List peerings for a virtual network.

    Args:
        vnet_name: Virtual network name.
        resource_group: Resource group containing the VNet.

    Returns:
        Formatted list of peerings (name, state, remote VNet, access/traffic/gateway settings).
    """
    try:
        network_client = _get_network_client()
        peerings = network_client.virtual_network_peerings.list(
            resource_group, vnet_name
        )

        formatted = []
        for p in peerings:
            remote = (
                p.remote_virtual_network.id.split("/")[-1]
                if p.remote_virtual_network
                else "N/A"
            )
            remote_rg = (
                p.remote_virtual_network.id.split("/")[4]
                if p.remote_virtual_network and p.remote_virtual_network.id
                else "N/A"
            )
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
