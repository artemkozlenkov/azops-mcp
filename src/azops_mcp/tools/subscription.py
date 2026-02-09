"""Subscription, auth, and account management tools."""

import logging
import re
from typing import Optional

from ..config import config
from ..utils.helpers import format_error_message
from ._clients import (
    _get_azure_credential,
    _get_subscription_client,
    _runtime_config,
    clear_subscription_id,
    get_subscription_id,
    reset_azure_credentials,
    set_subscription_id,
)

logger = logging.getLogger(__name__)

UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


async def configure_subscription(subscription_id: str) -> str:
    """Set the active Azure subscription ID for this session.

    Args:
        subscription_id: The Azure subscription ID to use

    Returns:
        Confirmation message
    """
    try:
        if not UUID_PATTERN.match(subscription_id.strip()):
            return (
                "Error: Invalid subscription ID format. "
                "Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            )

        set_subscription_id(subscription_id.strip())

        try:
            subscription_client = _get_subscription_client()
            subscription = subscription_client.subscriptions.get(subscription_id.strip())

            return (
                f"Subscription configured successfully!\n"
                f"{'='*50}\n"
                f"Subscription ID: {subscription.subscription_id}\n"
                f"Name: {subscription.display_name}\n"
                f"State: {subscription.state}\n"
                f"\nYou can now use Azure resource tools with this subscription."
            )
        except Exception as e:
            return (
                f"Subscription ID set to: {subscription_id}\n"
                f"Warning: Could not validate subscription. Error: {str(e)}\n"
                f"Make sure you're authenticated (run 'az login' or configure service principal)."
            )

    except ImportError as e:
        return str(e)
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
        from azure.core.exceptions import ClientAuthenticationError

        auth_info = {
            "method": "Unknown",
            "status": "Unknown",
            "details": [],
        }

        if config.azure_client_id and config.azure_client_secret and config.azure_tenant_id:
            auth_info["method"] = "Service Principal"
            auth_info["details"].append(
                f"Client ID: {config.azure_client_id[:8]}...{config.azure_client_id[-4:]}"
            )
            auth_info["details"].append(f"Tenant ID: {config.azure_tenant_id}")
        else:
            auth_info["method"] = "Azure CLI (az login)"
            auth_info["details"].append("Using local Azure CLI credentials")
            auth_info["details"].append("Run 'az login' if not authenticated")

        try:
            credential = _get_azure_credential()
            token = credential.get_token("https://management.azure.com/.default")
            if token:
                auth_info["status"] = "Authenticated"
                from datetime import datetime

                expiry = datetime.fromtimestamp(token.expires_on)
                auth_info["details"].append(f"Token expires: {expiry.isoformat()}")
        except ClientAuthenticationError as e:
            auth_info["status"] = "Not Authenticated"
            auth_info["details"].append(f"Error: {str(e)}")
        except Exception as e:
            auth_info["status"] = "Error"
            auth_info["details"].append(f"Error checking credentials: {str(e)}")

        subscription_id = get_subscription_id()
        runtime_sub = _runtime_config.get("subscription_id")

        if subscription_id:
            if runtime_sub:
                auth_info["details"].append(f"Subscription ID: {subscription_id} (set via chat)")
            else:
                auth_info["details"].append(f"Subscription ID: {subscription_id} (from .env)")
        else:
            auth_info["details"].append("Warning: No subscription ID configured")
            auth_info["details"].append(
                "Use azure_set_subscription to set one, or add AZURE_SUBSCRIPTION_ID to .env"
            )

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
        subscription = subscription_client.subscriptions.get(subscription_id)

        tenant_id = config.azure_tenant_id or "Not configured (using DefaultAzureCredential)"

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

        return f"Azure Subscriptions ({len(formatted_subs)} found):\n\n" + "\n---\n".join(
            formatted_subs
        )

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

        return f"Azure Locations ({len(formatted_locations)} available):\n\n" + "\n---\n".join(
            formatted_locations
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to list locations")
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


async def get_access_token(
    resource: str = "https://management.azure.com/.default",
) -> str:
    """Get an Azure access token for the current credentials (similar to 'az account get-access-token').

    Args:
        resource: The resource/scope to obtain a token for.
                  Default: https://management.azure.com/.default (Azure Resource Manager).

    Returns:
        Token information including the access token (masked), expiry, subscription, and tenant.
    """
    try:
        from datetime import datetime

        credential = _get_azure_credential()
        token = credential.get_token(resource)

        subscription_id = get_subscription_id() or "Not configured"
        tenant_id = config.azure_tenant_id or "N/A (using CLI/Managed Identity)"

        expiry = datetime.fromtimestamp(token.expires_on)

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

            if hasattr(tenant, "display_name") and tenant.display_name:
                details.append(f"Display Name: {tenant.display_name}")
            if hasattr(tenant, "default_domain") and tenant.default_domain:
                details.append(f"Default Domain: {tenant.default_domain}")
            if hasattr(tenant, "tenant_type") and tenant.tenant_type:
                details.append(f"Tenant Type: {tenant.tenant_type}")
            if hasattr(tenant, "country") and tenant.country:
                details.append(f"Country: {tenant.country}")

            formatted_tenants.append("\n".join(details))

        if not formatted_tenants:
            return "No tenants found for the current credentials."

        return f"Azure Tenants ({len(formatted_tenants)} found):\n\n" + "\n---\n".join(
            formatted_tenants
        )

    except ImportError as e:
        return str(e)
    except Exception as e:
        error_msg = format_error_message(e, "Failed to get tenant information")
        logger.error(error_msg)
        return error_msg
