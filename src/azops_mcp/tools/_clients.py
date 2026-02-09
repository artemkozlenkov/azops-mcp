"""Shared Azure SDK client factory module."""

import logging
from typing import Any, Dict, Optional

from ..config import config

logger = logging.getLogger(__name__)

# Azure SDK client globals (lazy loaded)
_azure_credential = None
_compute_client = None
_resource_client = None
_storage_client = None
_appconfig_mgmt_client = None
_appconfig_data_clients: Dict[str, Any] = {}  # keyed by store endpoint
_web_client = None
_network_client = None
_subscription_client = None
_authorization_client = None
_management_group_client = None

# Runtime configuration (can be set via chat)
_runtime_config: Dict[str, Optional[str]] = {
    "subscription_id": None,  # Overrides config.azure_subscription_id when set
}


def set_subscription_id(subscription_id: str) -> None:
    """Set the active subscription ID at runtime."""
    global _runtime_config, _compute_client, _resource_client, _storage_client
    global _subscription_client, _appconfig_mgmt_client, _appconfig_data_clients
    global _web_client, _network_client, _authorization_client, _management_group_client
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
    _authorization_client = None
    _management_group_client = None
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
    1. Service Principal (if AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID are set)
    2. ChainedTokenCredential: AzureCliCredential + ManagedIdentityCredential
    """
    global _azure_credential
    if _azure_credential is None:
        try:
            from azure.identity import (
                AzureCliCredential,
                ChainedTokenCredential,
                ClientSecretCredential,
                ManagedIdentityCredential,
            )

            if config.azure_client_id and config.azure_client_secret and config.azure_tenant_id:
                logger.info("Using Service Principal authentication")
                _azure_credential = ClientSecretCredential(
                    tenant_id=config.azure_tenant_id,
                    client_id=config.azure_client_id,
                    client_secret=config.azure_client_secret,
                )
            else:
                logger.info("Using Azure CLI / Managed Identity authentication")
                _azure_credential = ChainedTokenCredential(
                    AzureCliCredential(),
                    ManagedIdentityCredential(),
                )
        except ImportError as e:
            raise ImportError(
                "Azure SDK not installed. Run: pip install azure-identity azure-mgmt-compute "
                "azure-mgmt-resource azure-mgmt-storage"
            ) from e
    return _azure_credential


def reset_azure_credentials() -> None:
    """Reset cached Azure credentials (useful after re-authentication)."""
    global _azure_credential, _compute_client, _resource_client, _storage_client
    global _subscription_client, _appconfig_mgmt_client, _appconfig_data_clients
    global _web_client, _network_client, _authorization_client, _management_group_client
    _azure_credential = None
    _compute_client = None
    _resource_client = None
    _storage_client = None
    _subscription_client = None
    _appconfig_mgmt_client = None
    _appconfig_data_clients = {}
    _web_client = None
    _network_client = None
    _authorization_client = None
    _management_group_client = None
    logger.info("Azure credentials cache cleared")


def _get_compute_client():
    """Get Azure Compute Management client."""
    global _compute_client
    if _compute_client is None:
        try:
            from azure.mgmt.compute import ComputeManagementClient

            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError(
                    "Subscription ID not configured. Use azure_set_subscription to set it, "
                    "or configure AZURE_SUBSCRIPTION_ID in .env"
                )
            _compute_client = ComputeManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError as e:
            raise ImportError("Azure Compute SDK not installed. Run: pip install azure-mgmt-compute") from e
    return _compute_client


def _get_resource_client():
    """Get Azure Resource Management client."""
    global _resource_client
    if _resource_client is None:
        try:
            from azure.mgmt.resource import ResourceManagementClient

            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError(
                    "Subscription ID not configured. Use azure_set_subscription to set it, "
                    "or configure AZURE_SUBSCRIPTION_ID in .env"
                )
            _resource_client = ResourceManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError as e:
            raise ImportError("Azure Resource SDK not installed. Run: pip install azure-mgmt-resource") from e
    return _resource_client


def _get_storage_client():
    """Get Azure Storage Management client."""
    global _storage_client
    if _storage_client is None:
        try:
            from azure.mgmt.storage import StorageManagementClient

            subscription_id = get_subscription_id()
            if not subscription_id:
                raise ValueError(
                    "Subscription ID not configured. Use azure_set_subscription to set it, "
                    "or configure AZURE_SUBSCRIPTION_ID in .env"
                )
            _storage_client = StorageManagementClient(
                credential=_get_azure_credential(),
                subscription_id=subscription_id,
            )
        except ImportError as e:
            raise ImportError("Azure Storage SDK not installed. Run: pip install azure-mgmt-storage") from e
    return _storage_client


def _get_subscription_client():
    """Get Azure Subscription Management client."""
    global _subscription_client
    if _subscription_client is None:
        try:
            from azure.mgmt.subscription import SubscriptionClient

            _subscription_client = SubscriptionClient(
                credential=_get_azure_credential(),
            )
        except ImportError as e:
            raise ImportError(
                "Azure Subscription SDK not installed. Run: pip install azure-mgmt-subscription"
            ) from e
    return _subscription_client


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
        except ImportError as e:
            raise ImportError("Azure Web SDK not installed. Run: pip install azure-mgmt-web") from e
    return _web_client


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
        except ImportError as e:
            raise ImportError("Azure Network SDK not installed. Run: pip install azure-mgmt-network") from e
    return _network_client


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
        except ImportError as e:
            raise ImportError(
                "Azure Authorization SDK not installed. Run: pip install azure-mgmt-authorization"
            ) from e
    return _authorization_client


def _get_management_group_client():
    """Get Azure Management Group client."""
    global _management_group_client
    if _management_group_client is None:
        try:
            from azure.mgmt.managementgroups import ManagementGroupsAPI

            _management_group_client = ManagementGroupsAPI(
                credential=_get_azure_credential(),
            )
        except ImportError as e:
            raise ImportError(
                "Azure Management Groups SDK not installed. Run: pip install azure-mgmt-managementgroups"
            ) from e
    return _management_group_client


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
        except ImportError as e:
            raise ImportError(
                "Azure App Configuration SDK not installed. Run: pip install azure-mgmt-appconfiguration"
            ) from e
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
        except ImportError as e:
            raise ImportError(
                "Azure App Configuration data SDK not installed. Run: pip install azure-appconfiguration"
            ) from e
    return _appconfig_data_clients[endpoint]
