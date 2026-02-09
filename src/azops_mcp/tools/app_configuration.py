"""App Configuration store and key-value management."""

import logging
from typing import Any

from ..utils.helpers import format_error_message
from ._clients import _get_appconfig_data_client, _get_appconfig_mgmt_client

logger = logging.getLogger(__name__)


async def _resolve_appconfig_endpoint(store_name: str, resource_group: str = "") -> str:
    """Resolve the endpoint URL for an App Configuration store.

    If resource_group is given, get store directly. Otherwise search all stores.
    Return endpoint URL. Raise ValueError if not found.
    """
    try:
        client = _get_appconfig_mgmt_client()

        if resource_group:
            store = client.configuration_stores.get(resource_group, store_name)
            return store.endpoint
        else:
            stores = client.configuration_stores.list()
            for store in stores:
                if store.name == store_name:
                    return store.endpoint
            raise ValueError(f"App Configuration store '{store_name}' not found in subscription")
    except ImportError:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.error("_resolve_appconfig_endpoint failed: %s", e)
        raise ValueError(f"App Configuration store '{store_name}' not found: {e}") from e


async def appconfig_list(resource_group: str = "") -> str:
    """List App Configuration stores.

    If resource_group given, list_by_resource_group. Otherwise list all.
    Show name, location, RG (from id), endpoint, SKU, provisioning state.
    """
    try:
        client = _get_appconfig_mgmt_client()

        if resource_group:
            stores = client.configuration_stores.list_by_resource_group(resource_group)
        else:
            stores = client.configuration_stores.list()

        formatted = []
        for store in stores:
            rg_from_id = store.id.split("/")[4] if store.id else "N/A"
            sku = store.sku.name if store.sku else "N/A"
            formatted.append(
                f"Name: {store.name}\n"
                f"Location: {store.location}\n"
                f"Resource Group: {rg_from_id}\n"
                f"Endpoint: {store.endpoint}\n"
                f"SKU: {sku}\n"
                f"Provisioning State: {store.provisioning_state}"
            )

        if not formatted:
            scope = f"resource group '{resource_group}'" if resource_group else "subscription"
            return f"No App Configuration stores found in {scope}."

        return f"App Configuration Stores ({len(formatted)} found):\n\n" + "\n---\n".join(formatted)

    except ImportError as e:
        return format_error_message(e, "Failed to list App Configuration stores")
    except Exception as e:
        logger.error("appconfig_list failed: %s", e)
        return format_error_message(e, "Failed to list App Configuration stores")


async def appconfig_show(store_name: str, resource_group: str) -> str:
    """Show store details: name, location, RG, endpoint, SKU, provisioning state, creation date, soft delete retention, public network access, disable local auth, tags, ID."""
    try:
        client = _get_appconfig_mgmt_client()
        store = client.configuration_stores.get(resource_group, store_name)

        sku = store.sku.name if store.sku else "N/A"
        tags = ", ".join(f"{k}={v}" for k, v in (store.tags or {}).items()) or "None"

        return (
            f"App Configuration Store:\n"
            f"{'=' * 50}\n"
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

    except ImportError as e:
        return format_error_message(e, f"Failed to show App Configuration store '{store_name}'")
    except Exception as e:
        logger.error("appconfig_show failed: %s", e)
        return format_error_message(e, f"Failed to show App Configuration store '{store_name}'")


async def appconfig_kv_list(
    store_name: str,
    resource_group: str = "",
    key_filter: str = "*",
    label_filter: str = "",
) -> str:
    """List key-values. Resolve endpoint, use data client. Support key_filter and label_filter. Truncate values at 100 chars. Limit to 50 entries."""
    try:
        endpoint = await _resolve_appconfig_endpoint(store_name, resource_group)
        client = _get_appconfig_data_client(endpoint)

        kwargs: dict[str, Any] = {"key_filter": key_filter}
        if label_filter:
            kwargs["label_filter"] = label_filter

        settings = client.list_configuration_settings(**kwargs)

        formatted = []
        count = 0
        for setting in settings:
            if count >= 50:
                formatted.append("... (truncated, more key-values exist)")
                break
            value_str = str(setting.value or "")
            value_preview = value_str[:100] + ("..." if len(value_str) > 100 else "")
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
        return format_error_message(e, f"Failed to list key-values in '{store_name}'")
    except ValueError as e:
        return format_error_message(e, str(e))
    except Exception as e:
        logger.error("appconfig_kv_list failed: %s", e)
        return format_error_message(e, f"Failed to list key-values in '{store_name}'")


async def appconfig_kv_show(
    store_name: str,
    key: str,
    resource_group: str = "",
    label: str = "",
) -> str:
    """Show single key-value with key, value, label, content_type, last_modified, read_only, etag."""
    try:
        endpoint = await _resolve_appconfig_endpoint(store_name, resource_group)
        client = _get_appconfig_data_client(endpoint)

        setting = client.get_configuration_setting(key=key, label=label or None)

        return (
            f"App Configuration Key-Value:\n"
            f"{'=' * 50}\n"
            f"Key: {setting.key}\n"
            f"Value: {setting.value}\n"
            f"Label: {setting.label or '(no label)'}\n"
            f"Content Type: {setting.content_type or 'N/A'}\n"
            f"Last Modified: {setting.last_modified.isoformat() if setting.last_modified else 'N/A'}\n"
            f"Read Only: {setting.read_only}\n"
            f"ETag: {setting.etag or 'N/A'}"
        )

    except ImportError as e:
        return format_error_message(e, f"Failed to get key '{key}' from '{store_name}'")
    except ValueError as e:
        return format_error_message(e, str(e))
    except Exception as e:
        logger.error("appconfig_kv_show failed: %s", e)
        return format_error_message(e, f"Failed to get key '{key}' from '{store_name}'")


async def appconfig_kv_set(
    store_name: str,
    key: str,
    value: str,
    resource_group: str = "",
    label: str = "",
    content_type: str = "",
) -> str:
    """Set key-value using ConfigurationSetting."""
    try:
        from azure.appconfiguration import ConfigurationSetting

        endpoint = await _resolve_appconfig_endpoint(store_name, resource_group)
        client = _get_appconfig_data_client(endpoint)

        setting = ConfigurationSetting(
            key=key,
            value=value,
            label=label or None,
            content_type=content_type or None,
        )

        result = client.set_configuration_setting(setting)

        return (
            f"Key-value set successfully in '{store_name}':\n"
            f"{'=' * 50}\n"
            f"Key: {result.key}\n"
            f"Value: {result.value}\n"
            f"Label: {result.label or '(no label)'}\n"
            f"Last Modified: {result.last_modified.isoformat() if result.last_modified else 'N/A'}"
        )

    except ImportError as e:
        return format_error_message(e, f"Failed to set key '{key}' in '{store_name}'")
    except ValueError as e:
        return format_error_message(e, str(e))
    except Exception as e:
        logger.error("appconfig_kv_set failed: %s", e)
        return format_error_message(e, f"Failed to set key '{key}' in '{store_name}'")


async def appconfig_kv_delete(
    store_name: str,
    key: str,
    resource_group: str = "",
    label: str = "",
) -> str:
    """Delete key-value."""
    try:
        endpoint = await _resolve_appconfig_endpoint(store_name, resource_group)
        client = _get_appconfig_data_client(endpoint)

        client.delete_configuration_setting(key=key, label=label or None)

        label_info = f" (label='{label}')" if label else ""
        return f"Key-value '{key}'{label_info} deleted from '{store_name}'."

    except ImportError as e:
        return format_error_message(e, f"Failed to delete key '{key}' from '{store_name}'")
    except ValueError as e:
        return format_error_message(e, str(e))
    except Exception as e:
        logger.error("appconfig_kv_delete failed: %s", e)
        return format_error_message(e, f"Failed to delete key '{key}' from '{store_name}'")
