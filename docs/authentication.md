---
title: Authentication
layout: default
nav_order: 5
---

# Authentication
{: .no_toc }

How azops-mcp authenticates with Azure and validates premium licenses.
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

## License-Based Feature Gating

azops-mcp implements a two-tier access model. Premium tools are **conditionally registered** at startup — they only exist in the MCP tool catalog when a valid license grants the corresponding feature flag.

### How It Works

```
Server startup
     │
     ├─ Read AUTH_TOKEN and LICENSE_API_URL from .env
     │
     ├─ No AUTH_TOKEN? ──────────────► Free tier (23 tools)
     │
     ├─ No LICENSE_API_URL? ─────────► Free tier (cannot validate remotely)
     │
     └─ POST LICENSE_API_URL/v1/license/validate { token: AUTH_TOKEN }
            │
            ├─ { valid: false } ─────► Free tier
            │
            └─ { valid: true,
                 tier: "pro",
                 features: ["rg_write", "rbac", ...] }
                      │
                      └─► Register premium tools matching features
                          (23 free + 8 premium = 31 tools)
```

This is fundamentally different from a runtime "access denied" check. Premium tools are **never registered** unless the license grants them, so:

- The MCP `tools/list` response does not include them
- The LLM never sees their names, descriptions, or parameter schemas
- There is no error message hinting at hidden functionality

### Feature Flags

The license server returns a list of feature flags. Each flag controls one or more premium tools:

| Feature Flag | Premium Tools |
|:------------|:-------------|
| `rg_write` | `create_resource_group`, `delete_resource_group` |
| `rbac` | `list_role_assignments` |
| `locks_write` | `create_resource_lock`, `delete_resource_lock` |
| `tags_write` | `set_resource_group_tags` |
| `mg_write` | `create_management_group`, `delete_management_group` |

### Free Tier (No License)

All read-only and operational tools work without any token:

- `list_subscriptions`, `set_subscription`, `auth_status`, `list_locations`, `list_tenants`
- `list_management_groups`, `get_management_group`
- `list_role_definitions`
- `list_resource_locks`
- `list_tags`
- `get_activity_log`
- `list_resource_groups`, `list_resources`
- `list_vms`, `get_vm_status`, `start_vm`, `stop_vm`, `restart_vm`, `deallocate_vm`, `scale_vmss`
- `list_storage_accounts`, `get_storage_status`
- `health_check`

### Premium Tier

Write, modify, and delete operations require a valid license:

- `create_resource_group`, `delete_resource_group`
- `create_resource_lock`, `delete_resource_lock`
- `set_resource_group_tags`
- `list_role_assignments`
- `create_management_group`, `delete_management_group`

---

## Setting Up the License Server

The license server is a small FastAPI app included in the `license-server/` directory. You need to run it somewhere accessible to the MCP server.

### 1. Generate a License Key

```bash
cd license-server
python generate_license.py --tier pro --customer your-name --days 365
```

Output:

```
================================================================
  azops-mcp License Generated
================================================================
  API Key (give to customer):  azops_AbCdEf...
  Token Hash (licenses.json):  e3b0c44298fc1c14...
  Tier:                        pro
  Features:                    rg_write, rbac, locks_write, tags_write, mg_write
  Expires:                     2027-02-08T00:00:00Z
================================================================
```

### 2. Add to licenses.json

Paste the hash entry into `license-server/licenses.json`:

```json
{
  "e3b0c44298fc1c14...": {
    "customer": "your-name",
    "tier": "pro",
    "features": ["rg_write", "rbac", "locks_write", "tags_write", "mg_write"],
    "expires_at": "2027-02-08T00:00:00Z",
    "created_at": "2026-02-08T00:00:00Z"
  }
}
```

Tokens are stored as **SHA-256 hashes** — the plaintext key is never persisted.

### 3. Start the License Server

```bash
# Local development
cd license-server
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000

# Or with Docker Compose (from the project root)
docker compose up license-server
```

### 4. Configure the MCP Server

Add to your `.env`:

```env
AUTH_TOKEN=azops_AbCdEf...
LICENSE_API_URL=http://localhost:8000
```

Restart the MCP server. It will validate the token on startup and register premium tools if the license is valid.

### Verifying

Use `health_check` in your AI client:

```
Check the server health
```

The response includes a `license_tier` field showing `"free"` or `"pro"`.

---

## Token Security

| Concern | Mitigation |
|:--------|:-----------|
| Token stored in plaintext on license server | Tokens are SHA-256 hashed in `licenses.json` |
| Token intercepted in transit | Use HTTPS for `LICENSE_API_URL` in production |
| Token guessed / brute-forced | Keys are 44+ character `secrets.token_urlsafe` values |
| Expired token | License server checks `expires_at` and rejects expired tokens |
| Revocation | Remove the hash from `licenses.json` and restart the license server |

### Production Recommendations

- Deploy the license server behind HTTPS (TLS)
- Replace `licenses.json` with a database (PostgreSQL, Redis) for multi-instance deployments
- Add rate limiting to the `/v1/license/validate` endpoint
- Monitor license validation logs for abuse patterns
