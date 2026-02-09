"""App Service plans and web app CRUD (list, show, start, stop, restart)."""

import logging

from ..utils.helpers import format_error_message
from ._clients import _get_web_client

logger = logging.getLogger(__name__)


async def appservice_plan_list(resource_group: str = "") -> str:
    """List plans. Show name, RG, location, SKU (name + tier), status, kind, workers."""
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
        return format_error_message(e, "Failed to list App Service plans")
    except Exception as e:
        logger.error("appservice_plan_list failed: %s", e)
        return format_error_message(e, "Failed to list App Service plans")


async def appservice_plan_show(name: str, resource_group: str) -> str:
    """Show plan details: name, RG, location, SKU, capacity, status, kind, reserved (linux), workers, max workers, number of sites, provisioning state, ID."""
    try:
        client = _get_web_client()
        plan = client.app_service_plans.get(resource_group, name)

        sku = f"{plan.sku.name} ({plan.sku.tier})" if plan.sku else "N/A"
        sku_capacity = str(plan.sku.capacity) if plan.sku else "N/A"

        return (
            f"App Service Plan:\n"
            f"{'=' * 50}\n"
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

    except ImportError as e:
        return format_error_message(e, f"Failed to show App Service plan '{name}'")
    except Exception as e:
        logger.error("appservice_plan_show failed: %s", e)
        return format_error_message(e, f"Failed to show App Service plan '{name}'")


async def webapp_list(resource_group: str = "") -> str:
    """List web apps. Show name, RG, location, state, hostname, kind, HTTPS only."""
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
                f"Hostname: {app.default_host_name or 'N/A'}\n"
                f"Kind: {app.kind or 'N/A'}\n"
                f"HTTPS Only: {app.https_only or False}"
            )

        if not formatted:
            scope = f"resource group '{resource_group}'" if resource_group else "subscription"
            return f"No web apps found in {scope}."

        return f"Web Apps ({len(formatted)} found):\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return format_error_message(e, "Failed to list web apps")
    except Exception as e:
        logger.error("webapp_list failed: %s", e)
        return format_error_message(e, "Failed to list web apps")


async def webapp_show(name: str, resource_group: str) -> str:
    """Show web app details: name, RG, location, state, hostname, kind, plan, HTTPS only, client cert, availability, outbound IPs, last modified, tags, ID."""
    try:
        client = _get_web_client()
        app = client.web_apps.get(resource_group, name)

        plan_name = app.server_farm_id.split("/")[-1] if app.server_farm_id else "N/A"
        outbound_ips = app.outbound_ip_addresses or "N/A"
        tags = ", ".join(f"{k}={v}" for k, v in (app.tags or {}).items()) or "None"

        return (
            f"Web App:\n"
            f"{'=' * 50}\n"
            f"Name: {app.name}\n"
            f"Resource Group: {resource_group}\n"
            f"Location: {app.location}\n"
            f"State: {app.state or 'N/A'}\n"
            f"Hostname: {app.default_host_name or 'N/A'}\n"
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

    except ImportError as e:
        return format_error_message(e, f"Failed to show web app '{name}'")
    except Exception as e:
        logger.error("webapp_show failed: %s", e)
        return format_error_message(e, f"Failed to show web app '{name}'")


async def webapp_start(name: str, resource_group: str) -> str:
    """Start web app."""
    try:
        client = _get_web_client()
        client.web_apps.start(resource_group, name)
        return f"Web app '{name}' started successfully."

    except ImportError as e:
        return format_error_message(e, f"Failed to start web app '{name}'")
    except Exception as e:
        logger.error("webapp_start failed: %s", e)
        return format_error_message(e, f"Failed to start web app '{name}'")


async def webapp_stop(name: str, resource_group: str) -> str:
    """Stop web app."""
    try:
        client = _get_web_client()
        client.web_apps.stop(resource_group, name)
        return f"Web app '{name}' stopped successfully."

    except ImportError as e:
        return format_error_message(e, f"Failed to stop web app '{name}'")
    except Exception as e:
        logger.error("webapp_stop failed: %s", e)
        return format_error_message(e, f"Failed to stop web app '{name}'")


async def webapp_restart(name: str, resource_group: str) -> str:
    """Restart web app."""
    try:
        client = _get_web_client()
        client.web_apps.restart(resource_group, name)
        return f"Web app '{name}' restarted successfully."

    except ImportError as e:
        return format_error_message(e, f"Failed to restart web app '{name}'")
    except Exception as e:
        logger.error("webapp_restart failed: %s", e)
        return format_error_message(e, f"Failed to restart web app '{name}'")
