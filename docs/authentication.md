---
title: Authentication
layout: default
nav_order: 5
---

# Authentication
{: .no_toc }

How azops-mcp authenticates with Azure.
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

## Account Tools

azops-mcp provides several account management tools similar to `az account` CLI commands:

### `account_show`

Get details of the current Azure subscription — similar to `az account show`. Shows the subscription name, ID, tenant, state, and environment.

### `account_clear`

Clear cached Azure credentials and subscription override — similar to `az account clear`. Resets the in-memory subscription override and clears all cached SDK clients so the next operation re-authenticates from scratch.

### `account_get_access_token`

Get an Azure access token — similar to `az account get-access-token`. By default fetches a token for Azure Resource Manager. You can specify a different resource/scope:

```
Get an access token for Azure Key Vault
```

The token is masked in the output for security.

---

## Token Security

| Concern | Mitigation |
|:--------|:-----------|
| Azure CLI token exposure | Tokens are read from the Azure CLI cache and never logged |
| Service Principal secret | Stored in `.env` which is gitignored; never sent over MCP |
| Access tokens from `account_get_access_token` | Masked in output — only first 8 and last 4 characters shown |
| Credential caching | `account_clear` resets all cached credentials and SDK clients |

### Production Recommendations

- Use Service Principal with least-privilege RBAC roles
- Rotate client secrets regularly
- Use Managed Identity when running in Azure to avoid managing secrets entirely
- Set `AZURE_SUBSCRIPTION_ID` in `.env` to avoid accidental operations on the wrong subscription
