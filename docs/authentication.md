---
title: Authentication
layout: default
nav_order: 5
---

# Authentication
{: .no_toc }

How azops-mcp authenticates with Azure and manages feature access.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Azure Authentication

azops-mcp uses the Azure SDK's credential classes to authenticate. The server tries credentials in a specific order and uses the first one that works.

### Priority Order

```
1. Service Principal (AZURE_CLIENT_ID + SECRET + TENANT_ID all set)
       ↓ (if not configured)
2. Azure CLI credentials (az login)
       ↓ (if not available)
3. Managed Identity (when running in Azure)
```

### Option 1: Azure CLI (Recommended for Development)

The simplest approach. Just log in once:

```bash
az login
```

The server uses `AzureCliCredential` which reads your local CLI token. No environment variables needed beyond `AZURE_SUBSCRIPTION_ID`.

### Option 2: Service Principal (Recommended for Production)

Create a Service Principal:

```bash
az ad sp create-for-rbac --name "azops-mcp" --role Contributor \
    --scopes /subscriptions/<your-subscription-id>
```

Add the output values to your `.env`:

```env
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

The server detects all three are set and uses `ClientSecretCredential`.

### Option 3: Managed Identity

When running inside Azure (e.g., Azure VM, App Service), the server falls back to `ManagedIdentityCredential` automatically. No configuration needed — just assign the appropriate RBAC role to the managed identity.

### Checking Auth Status

Use the `auth_status` tool in your AI client:

```
What's my Azure auth status?
```

This reports:
- Which authentication method is active
- Whether the token is valid
- Token expiry time
- Which subscription is configured and how (`.env` vs. chat)

---

## Runtime Subscription Switching

You don't have to restart the server to change subscriptions. Use `set_subscription` in chat:

```
Switch to subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Under the hood, this:
1. Validates the UUID format
2. Sets `_runtime_config["subscription_id"]` in `cloud.py`
3. Clears all cached Azure SDK clients (so they re-initialize with the new subscription)
4. Optionally validates the subscription exists by calling the Subscription API

The override persists for the session only. Restarting the server reverts to the `.env` value.

---

## Paywall Authentication (AUTH_TOKEN)

azops-mcp implements a two-tier access model controlled by the `AUTH_TOKEN` environment variable.

### Free Tier (No AUTH_TOKEN)

All read-only operations work without any token:

- `list_subscriptions`, `list_resource_groups`, `list_vms`, `list_storage_accounts`
- `get_vm_status`, `get_storage_status`, `list_locations`, `list_tenants`
- `auth_status`, `health_check`
- `list_management_groups`, `get_management_group`
- `list_role_definitions`, `list_resource_locks`, `list_tags`
- `get_activity_log`
- VM lifecycle: `start_vm`, `stop_vm`, `restart_vm`, `deallocate_vm`, `scale_vmss`

### Paid Tier (AUTH_TOKEN Required)

Write/modify/delete operations require a valid `AUTH_TOKEN`:

- `create_resource_group`, `delete_resource_group`
- `create_resource_lock`, `delete_resource_lock`
- `set_resource_group_tags`
- `list_role_assignments`

### Setting AUTH_TOKEN

Add to your `.env`:

```env
AUTH_TOKEN=your-secure-token-at-least-8-chars
```

Requirements:
- Must be at least 8 characters
- Can be any string — there is no external validation service

### How It Works Internally

The paywall is implemented in `utils/auth.py`:

```python
def is_paywall_enabled() -> bool:
    return config.auth_token is not None and len(config.auth_token) > 0

def check_auth_token() -> tuple[bool, str]:
    if config.auth_token is None or len(config.auth_token) == 0:
        return False, "AUTH_TOKEN not configured."
    if len(config.auth_token) < 8:
        return False, "AUTH_TOKEN must be at least 8 characters."
    return True, ""
```

In `server.py`, gated tools call `_check_paywall_access()` before proceeding:

```python
paywall_error = _check_paywall_access()
if paywall_error:
    return paywall_error
```

If the check fails, the tool returns a user-friendly error message explaining what's needed. The server does **not** crash or raise an exception.

A `@require_auth_token` decorator is also available for convenience:

```python
@require_auth_token
async def my_tool(...) -> str:
    # Only runs if AUTH_TOKEN is valid
    ...
```
