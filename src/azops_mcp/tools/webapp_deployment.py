"""Web App for Containers tools for Azure deployment."""

import logging
from typing import Dict

from ..utils.helpers import format_error_message
from ._clients import (
    _get_authorization_client,
    _get_azure_credential,
    _get_network_client,
    _get_resource_client,
    _get_web_client,
    get_subscription_id,
)

logger = logging.getLogger(__name__)


async def webapp_create_for_container(
    name: str,
    resource_group: str,
    plan_name: str,
    plan_sku: str = "P1v2",
    plan_tier: str = "PremiumV2",
    location: str = "",
    image: str = "",
    registry_url: str = "",
    registry_username: str = "",
    registry_password: str = "",
    os_type: str = "linux",
    multi_container: bool = False,
    startup_command: str = "",
    env_variables: Dict[str, str] = None,
    vnet_subnet_id: str = "",
    assign_identity: bool = False,
) -> str:
    """Create a Web App for Containers on Azure App Service.

    This function creates a complete web app infrastructure including:
    - App Service Plan (if not exists)
    - Web App for Containers
    - Container registry configuration
    - Virtual Network integration (optional)
    - RBAC assignments (optional)

    Args:
        name: Web app name (must be unique across Azure)
        resource_group: Resource group to deploy to
        plan_name: App Service plan name
        plan_sku: SKU tier (F1, D1, B1, B2, B3, S1, S2, S3, P1v2, P2v2, P3v2, etc.)
        plan_tier: SKU tier (Free, Shared, Basic, Standard, PremiumV2, PremiumV3, etc.)
        location: Azure region (defaults to resource group location)
        image: Container image (e.g., myregistry.azurecr.io/myapp:latest)
        registry_url: Container registry URL (e.g., myregistry.azurecr.io)
        registry_username: Registry username (admin user)
        registry_password: Registry password/access key
        os_type: OS type - 'linux' or 'windows'
        multi_container: Whether to use multi-container (Docker Compose)
        startup_command: Startup command (e.g., 'python app.py')
        env_variables: Environment variables dict
        vnet_subnet_id: Subnet resource ID for VNet integration
        assign_identity: Whether to assign system-assigned managed identity

    Returns:
        Result of the creation operation
    """
    try:
        subscription_id = get_subscription_id()
        if not subscription_id:
            return "Error: Subscription ID not configured"

        # Resolve location from resource group if not specified
        if not location:
            resource_client = _get_resource_client()
            rg = resource_client.resource_groups.get(resource_group)
            location = rg.location

        web_client = _get_web_client()

        # Check if App Service Plan exists, create if not
        try:
            plan = web_client.app_service_plans.get(resource_group, plan_name)
            logger.info(f"App Service Plan '{plan_name}' exists")
        except Exception:
            logger.info(f"Creating App Service Plan '{plan_name}'")
            plan_params = {
                "location": location,
                "reserved": os_type == "linux",  # Linux plans need reserved=True
                "sku": {
                    "name": plan_sku,
                    "tier": plan_tier,
                    "capacity": 1,
                },
            }
            poller = web_client.app_service_plans.begin_create_or_update(resource_group, plan_name, plan_params)
            plan = poller.result()
            logger.info(f"App Service Plan '{plan_name}' created")

        # Build container configuration
        app_settings = []

        if os_type == "linux":
            if image:
                app_settings.append({"name": "WEBSITES_ENABLE_APP_SERVICE_STORAGE", "value": "false"})
                app_settings.append(
                    {"name": "DOCKER_REGISTRY_SERVER_URL", "value": f"https://{registry_url}" if registry_url else ""}
                )
                app_settings.append({"name": "DOCKER_ENABLE_CI", "value": "false"})

                if assign_identity:
                    app_settings.append({"name": "DOCKER_REGISTRY_SERVER_USERNAME", "value": "[system]"})
                else:
                    app_settings.append({"name": "DOCKER_REGISTRY_SERVER_USERNAME", "value": registry_username or ""})
                    app_settings.append({"name": "DOCKER_REGISTRY_SERVER_PASSWORD", "value": registry_password or ""})

                if multi_container:
                    app_settings.append({"name": "COMPOSE_APPLICATION_NAME", "value": name})
                    app_settings.append({"name": "WEBSITES_ENABLE_OVERLAY", "value": "true"})
                else:
                    app_settings.append({"name": "DOCKER_CUSTOM_IMAGE_NAME", "value": image})

            if startup_command:
                app_settings.append({"name": "STARTUP_COMMAND", "value": startup_command})

        # Add environment variables
        if env_variables:
            for key, value in env_variables.items():
                app_settings.append({"name": key.upper(), "value": value})

        # Build web app parameters
        app_params = {
            "location": location,
            "kind": "app,linux" if os_type == "linux" else "app",
            "reserved": os_type == "linux",
            "server_farm_id": plan.id,
            "site_config": {
                "app_settings": app_settings,
                "linux_fx_version": f"DOCKER|{image}" if image else "",
            },
        }

        # Create web app
        logger.info(f"Creating Web App '{name}' in '{resource_group}'")
        poller = web_client.web_apps.begin_create_or_update(resource_group, name, app_params)
        result = poller.result()

        # Configure VNet integration if specified
        if vnet_subnet_id:
            try:
                vnet_info = await webapp_configure_vnet_integration(name, resource_group, vnet_subnet_id)
                logger.info(f"VNet integration configured: {vnet_info}")
            except Exception as e:
                logger.warning(f"Failed to configure VNet integration: {e}")

        # Configure managed identity if requested
        if assign_identity:
            try:
                identity_result = await webapp_assign_identity(name, resource_group)
                logger.info(f"Managed identity assigned: {identity_result}")
            except Exception as e:
                logger.warning(f"Failed to assign identity: {e}")

        # Get connection strings and other info
        connection_strings = web_client.web_apps.list_connection_strings(resource_group, name)

        output = (
            f"Web App for Containers created successfully!\n"
            f"{'=' * 60}\n"
            f"Name: {result.name}\n"
            f"Resource Group: {resource_group}\n"
            f"Location: {result.location}\n"
            f"State: {result.state or 'N/A'}\n"
            f"Hostname: {result.default_host_name or 'N/A'}\n"
            f"App Service Plan: {plan_name}\n"
            f"SKU: {plan_sku} ({plan_tier})\n"
            f"OS: {os_type.capitalize()}\n"
            f"Container Image: {image if image else 'Not configured'}\n"
            f"{'=' * 60}\n"
            f"\nConnection Strings:\n"
        )

        if connection_strings and connection_strings.value:
            for conn_str in connection_strings.value:
                output += f"  - {conn_str.name}: {conn_str.value if conn_str.type != 'Custom' else '***'}\n"

        if app_settings:
            output += "\nApp Settings:\n"
            for setting in app_settings:
                if "PASSWORD" in setting["name"] or "SECRET" in setting["name"]:
                    output += f"  - {setting['name']}: ***\n"
                else:
                    output += f"  - {setting['name']}: {setting['value']}\n"

        if vnet_subnet_id:
            output += "\nVNet Integration: Configured\n"

        if assign_identity:
            output += "\nManaged Identity: System-assigned enabled\n"

        return output

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to create web app '{name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_configure_vnet_integration(webapp_name: str, resource_group: str, subnet_id: str) -> str:
    """Configure Virtual Network integration for a web app.

    Args:
        webapp_name: Web app name
        resource_group: Resource group containing the web app
        subnet_id: Subnet resource ID to integrate with

    Returns:
        Result of the configuration
    """
    try:
        web_client = _get_web_client()

        # Get the subnet
        subnet_client = _get_network_client()
        subnet_parts = subnet_id.split("/")
        vnet_name = subnet_parts[-3] if len(subnet_parts) > 3 else ""
        subnet_name = subnet_parts[-1] if len(subnet_parts) > 0 else ""

        subnet = subnet_client.subnets.get(resource_group, vnet_name, subnet_name)

        # Configure VNet integration

        web_client.web_apps.begin_create_or_update_configuration(
            resource_group,
            webapp_name,
            {
                "properties": {
                    "vnet_name": vnet_name,
                    "vnet_resource_group": resource_group,
                    "vnet_subnet_name": subnet_name,
                }
            },
        )

        return (
            f"VNet integration configured for '{webapp_name}'\n"
            f"{'=' * 60}\n"
            f"Subnet: {subnet_name}\n"
            f"VNet: {vnet_name}\n"
            f"Resource Group: {resource_group}\n"
            f"Address Prefix: {subnet.address_prefix or 'N/A'}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to configure VNet integration for '{webapp_name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_assign_identity(webapp_name: str, resource_group: str) -> str:
    """Assign a system-assigned managed identity to a web app.

    Args:
        webapp_name: Web app name
        resource_group: Resource group containing the web app

    Returns:
        Result with identity details
    """
    try:
        web_client = _get_web_client()

        # Get current web app
        app = web_client.web_apps.get(resource_group, webapp_name)

        # Update with managed identity
        app.identity = {
            "type": "SystemAssigned",
        }

        poller = web_client.web_apps.begin_create_or_update(resource_group, webapp_name, app)
        result = poller.result()

        output = (
            f"Managed identity assigned to '{webapp_name}'\n"
            f"{'=' * 60}\n"
            f"Principal ID: {result.identity.principal_id or 'N/A'}\n"
            f"Tenant ID: {result.identity.tenant_id or 'N/A'}\n"
            f"Type: {result.identity.type or 'N/A'}\n"
        )

        return output

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to assign identity to '{webapp_name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_set_container_registry_credentials(
    webapp_name: str,
    resource_group: str,
    registry_url: str,
    username: str,
    password: str,
    os_type: str = "linux",
) -> str:
    """Set container registry credentials for a web app.

    Args:
        webapp_name: Web app name
        resource_group: Resource group containing the web app
        registry_url: Container registry URL (e.g., myregistry.azurecr.io)
        username: Registry username (admin user)
        password: Registry password/access key
        os_type: OS type - 'linux' or 'windows'

    Returns:
        Result of the configuration
    """
    try:
        web_client = _get_web_client()

        # Update container settings
        container_settings = {
            "properties": {
                "linuxFxVersion": f"DOCKER|{registry_url}",
                "windowsFxVersion": None,
                "dockerRegistryUrl": registry_url,
                "dockerRegistryServerUrl": registry_url,
                "dockerRegistryUsername": username,
                "dockerRegistryPassword": password,
            }
        }

        web_client.web_apps.update_configuration(resource_group, webapp_name, container_settings)

        # Update app settings
        app_settings = [
            {"name": "WEBSITES_ENABLE_APP_SERVICE_STORAGE", "value": "false"},
            {"name": "DOCKER_REGISTRY_SERVER_URL", "value": f"https://{registry_url}"},
            {"name": "DOCKER_REGISTRY_SERVER_USERNAME", "value": username},
            {"name": "DOCKER_REGISTRY_SERVER_PASSWORD", "value": password},
        ]

        web_client.web_apps.update_application_settings(resource_group, webapp_name, app_settings)

        return (
            f"Container registry credentials configured for '{webapp_name}'\n"
            f"{'=' * 60}\n"
            f"Registry URL: {registry_url}\n"
            f"Username: {username}\n"
            f"OS Type: {os_type}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to set registry credentials for '{webapp_name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_grant_cr_access(
    webapp_name: str,
    resource_group: str,
    registry_name: str,
    registry_resource_group: str,
    role: str = "AcrPull",
) -> str:
    """Grant Web App access to Container Registry via RBAC.

    Args:
        webapp_name: Web app name
        resource_group: Resource group containing the web app
        registry_name: Container registry name
        registry_resource_group: Resource group containing the registry
        role: Role name (AcrPull, Acrpush, etc.)

    Returns:
        Result of the RBAC assignment
    """
    try:
        web_client = _get_web_client()
        authorization_client = _get_authorization_client()

        # Get web app to get its identity
        app = web_client.web_apps.get(resource_group, webapp_name)

        if not app.identity or not app.identity.principal_id:
            return "Error: Web app does not have a managed identity. Run webapp_assign_identity first."

        principal_id = app.identity.principal_id

        # Get registry resource ID
        subscription_id = get_subscription_id()
        registry_id = (
            f"/subscriptions/{subscription_id}/resourceGroups/{registry_resource_group}"
            f"/providers/Microsoft.ContainerRegistry/registries/{registry_name}"
        )

        # Get role definition ID for the specified role
        scope = registry_id
        roles = authorization_client.role_definitions.list(scope)
        role_def_id = None

        for role_def in roles:
            if role_def.role_name == role or role_def.name == role:
                role_def_id = role_def.id
                break

        if not role_def_id:
            return f"Error: Role '{role}' not found. Available roles: AcrPull, AcrPush, etc."

        # Create role assignment
        from azure.mgmt.authorization.models import RoleAssignmentCreateParameters

        assignment_params = RoleAssignmentCreateParameters(
            role_definition_id=role_def_id,
            principal_id=principal_id,
            principal_type="ServicePrincipal",
        )

        # Generate unique assignment name
        import uuid

        assignment_name = str(uuid.uuid4())

        authorization_client.role_assignments.create(scope, assignment_name, assignment_params)

        return (
            f"RBAC permission granted for '{webapp_name}' to access '{registry_name}'\n"
            f"{'=' * 60}\n"
            f"Web App: {webapp_name}\n"
            f"Registry: {registry_name}\n"
            f"Role: {role}\n"
            f"Principal ID: {principal_id}\n"
            f"Scope: {scope}"
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to grant CR access for '{webapp_name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_view_logs(webapp_name: str, resource_group: str, days: int = 1) -> str:
    """View web app logs from Azure Monitor.

    Args:
        webapp_name: Web app name
        resource_group: Resource group containing the web app
        days: Number of days to look back (1-7)

    Returns:
        Recent log entries
    """
    try:
        from datetime import datetime, timedelta

        from azure.mgmt.monitor import MonitorManagementClient

        web_client = _get_web_client()
        subscription_id = get_subscription_id()

        # Get web app details
        app = web_client.web_apps.get(resource_group, webapp_name)

        # Build resource ID
        webapp_id = app.id

        # Initialize monitor client
        credential = _get_azure_credential()
        monitor_client = MonitorManagementClient(credential, subscription_id)

        # Calculate time range
        days = min(max(days, 1), 7)
        start_time = datetime.utcnow() - timedelta(days=days)
        end_time = datetime.utcnow()

        # Build filter for web app logs
        filter_str = (
            f"eventTimestamp ge '{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}' "
            f"and eventTimestamp le '{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}' "
            f"and resourceId eq '{webapp_id}'"
        )

        # Get activity logs
        logs = monitor_client.activity_logs.list(filter=filter_str)

        formatted = []
        for log in logs:
            if len(formatted) >= 20:  # Limit to 20 entries
                break

            timestamp = log.event_timestamp.isoformat() if log.event_timestamp else "N/A"
            operation = log.operation_name.localized_value if log.operation_name else "N/A"
            status = log.status.localized_value if log.status else "N/A"
            caller = log.caller or "N/A"

            formatted.append(f"Time: {timestamp}\nOperation: {operation}\nStatus: {status}\nCaller: {caller}")

        if not formatted:
            return f"No log entries found for '{webapp_name}' in the last {days} day(s)."

        return f"Web App Activity Log (last {days} day(s)):\n\n" + "\n---\n".join(formatted)

    except ImportError:
        return "Azure Monitor SDK not installed. Run: pip install azure-mgmt-monitor"
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to get logs for '{webapp_name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_restart(webapp_name: str, resource_group: str) -> str:
    """Restart a web app.

    Args:
        webapp_name: Web app name
        resource_group: Resource group containing the web app

    Returns:
        Result of the restart operation
    """
    try:
        web_client = _get_web_client()
        web_client.web_apps.restart(resource_group, webapp_name)
        return f"Web app '{webapp_name}' restarted successfully."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to restart web app '{webapp_name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_stop(webapp_name: str, resource_group: str) -> str:
    """Stop a web app.

    Args:
        webapp_name: Web app name
        resource_group: Resource group containing the web app

    Returns:
        Result of the stop operation
    """
    try:
        web_client = _get_web_client()
        web_client.web_apps.stop(resource_group, webapp_name)
        return f"Web app '{webapp_name}' stopped successfully."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to stop web app '{webapp_name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_start(webapp_name: str, resource_group: str) -> str:
    """Start a web app.

    Args:
        webapp_name: Web app name
        resource_group: Resource group containing the web app

    Returns:
        Result of the start operation
    """
    try:
        web_client = _get_web_client()
        web_client.web_apps.start(resource_group, webapp_name)
        return f"Web app '{webapp_name}' started successfully."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to start web app '{webapp_name}'")
        logger.error(error_msg)
        return error_msg


async def webapp_delete(webapp_name: str, resource_group: str) -> str:
    """Delete a web app.

    Args:
        webapp_name: Web app name
        resource_group: Resource group containing the web app

    Returns:
        Result of the delete operation
    """
    try:
        web_client = _get_web_client()
        web_client.web_apps.delete(resource_group, webapp_name)
        return f"Web app '{webapp_name}' deleted from '{resource_group}'."

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, f"Failed to delete web app '{webapp_name}'")
        logger.error(error_msg)
        return error_msg
