---
title: Architecture
layout: default
nav_order: 3
---

# Architecture
{: .no_toc }

How azops-mcp works under the hood.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## High-Level Overview

```
                              on startup: POST /v1/license/validate
                           ┌───────────────────────────────────────────────┐
                           │                                               │
                           ▼                                               │
┌──────────────────┐  stdio (JSON-RPC)  ┌───────────────────────────┐     │
│   AI Assistant    │ ◄────────────────► │       azops-mcp           │     │
│   (Cursor, etc.)  │                   │                           │     │
└──────────────────┘                    │  server.py                │     │
                                        │    ├─ free tools (always) │     │
                                        │    └─ premium tools       │     │
                                        │       (if licensed)       │     │
                                        │                           │     │
                                        │  tools/                   │     │
                                        │    └─ cloud.py  (Azure)   │     │
                                        │                           │     │
                                        │  utils/                   │     │
                                        │    ├─ auth.py  (license)  │─────┘
                                        │    └─ helpers.py          │
                                        │                           │
                                        │  config.py               │
                                        └────────────┬──────────────┘
                                                     │
                                           Azure SDK REST calls
                                                     │
                                                     ▼
                                           ┌─────────────────┐
                                           │   Azure Cloud   │
                                           │   (ARM API)     │
                                           └─────────────────┘

┌─────────────────────────────────────────┐
│         License Server                   │
│  (separate service — FastAPI)            │
│                                          │
│  POST /v1/license/validate               │
│  { token } → { valid, tier, features }  │
│                                          │
│  licenses.json (SHA-256 hashed tokens)  │
└─────────────────────────────────────────┘
```

The system consists of **two services**:

1. **azops-mcp** — the MCP server, a single Python process started by the AI client as a subprocess. It communicates over **stdio** using the [Model Context Protocol](https://modelcontextprotocol.io/).
2. **license-server** — a lightweight FastAPI service that validates `AUTH_TOKEN` and returns feature entitlements. It can run locally, as a container, or as a serverless function.

On startup, `azops-mcp` sends the `AUTH_TOKEN` to the license server. The response determines which premium tools are registered. Without a valid license, premium tools are never registered and are invisible to the MCP client.

---

## Licensing & Conditional Tool Registration

This is the core architectural pattern for feature gating:

```python
# Free tools — always registered at module level
@mcp.tool()
async def list_resource_groups() -> str: ...

# Premium tools — registered inside a function, only if licensed
def _register_premium_tools():
    features = get_licensed_features()  # calls license server once, then caches

    if "rg_write" in features:
        @mcp.tool()
        async def create_resource_group(...) -> str: ...

    if "rbac" in features:
        @mcp.tool()
        async def list_role_assignments(...) -> str: ...

_register_premium_tools()  # called once at import time
```

**Key properties:**

- The MCP `tools/list` response only includes tools whose feature flag is licensed
- The AI / LLM never sees premium tool names, signatures, or descriptions without a valid token
- A fake or expired token results in the license server rejecting it — premium tools stay hidden
- The license result is cached with a configurable TTL (`LICENSE_CACHE_TTL`, default 3600s)

### Feature Flags

| Flag | Premium Tools |
|:-----|:-------------|
| `rg_write` | `create_resource_group`, `delete_resource_group` |
| `rbac` | `list_role_assignments` |
| `locks_write` | `create_resource_lock`, `delete_resource_lock` |
| `tags_write` | `set_resource_group_tags` |
| `mg_write` | `create_management_group`, `delete_management_group` |

---

## Module Breakdown

### `__main__.py` — Entry Point

```python
from .server import main

if __name__ == "__main__":
    main()
```

When you run `python -m azops_mcp`, this module imports and calls `main()` from `server.py`. It is the only entry point.

### `server.py` — MCP Server & Tool Definitions

This is the core of the application. It:

1. **Initialises FastMCP** — creates a `FastMCP("azops-mcp")` instance from the `mcp` SDK.
2. **Registers free tools** — each `@mcp.tool()` decorated async function at module level becomes a callable tool for the AI assistant.
3. **Conditionally registers premium tools** — `_register_premium_tools()` checks the license and registers write/mutate tools only if the corresponding feature flag is granted.
4. **Handles lifecycle** — `main()` starts the MCP server on stdio transport and installs signal handlers for graceful shutdown.

**Free tool pattern** (always available):

```python
@mcp.tool()
async def list_resource_groups() -> str:
    """List all resource groups in the subscription."""
    try:
        return await cloud.list_resource_groups()
    except Exception as e:
        return f"Error: {e}"
```

**Premium tool pattern** (conditionally registered):

```python
def _register_premium_tools():
    features = get_licensed_features()

    if "rg_write" in features:
        @mcp.tool()
        async def create_resource_group(name: str, location: str) -> str:
            """Create a new Azure resource group."""
            ...
```

### `config.py` — Configuration Management

A `@dataclass` called `ServerConfig` with fields loaded from environment variables via `os.getenv()` with sensible defaults:

| Category | Fields |
|:---------|:-------|
| Logging | `log_level`, `log_format` |
| API | `api_timeout`, `api_retry_attempts`, `api_retry_delay` |
| Azure | `azure_tenant_id`, `azure_client_id`, `azure_client_secret`, `azure_subscription_id`, `azure_default_location` |
| Docker | `docker_timeout` |
| Monitoring | `monitoring_interval` |
| Rate Limiting | `rate_limit_enabled`, `rate_limit_requests_per_minute`, `rate_limit_burst_size` |
| Security | `secret_key`, `allowed_hosts` |
| License | `auth_token`, `license_api_url`, `license_cache_ttl` |
| Debug | `debug` |

A global `config` singleton is created at import time. The `validate()` method checks for inconsistencies (e.g., incomplete Service Principal credentials, invalid timeouts).

### `tools/cloud.py` — Azure SDK Integration

This is the largest module (~1300 lines). It contains **all Azure API interactions**.

#### Lazy Client Initialization

Azure SDK clients are expensive to construct. `cloud.py` uses a lazy-loading pattern with module-level globals:

```python
_azure_credential = None
_compute_client = None

def _get_compute_client():
    global _compute_client
    if _compute_client is None:
        _compute_client = ComputeManagementClient(
            credential=_get_azure_credential(),
            subscription_id=get_subscription_id(),
        )
    return _compute_client
```

Each client is created once on first use, then cached for the session.

#### Authentication Chain

```python
def _get_azure_credential():
    # Priority:
    # 1. Service Principal (if fully configured)
    # 2. Azure CLI + Managed Identity (ChainedTokenCredential)
```

If `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_TENANT_ID` are all set, a `ClientSecretCredential` is used. Otherwise, a `ChainedTokenCredential` tries Azure CLI first, then Managed Identity.

#### Runtime Subscription Override

Users can switch subscriptions at runtime without restarting the server:

```python
_runtime_config = {"subscription_id": None}

def set_subscription_id(subscription_id: str):
    _runtime_config["subscription_id"] = subscription_id
    # Clear cached clients so they pick up the new subscription
    _compute_client = None
    _resource_client = None
    ...
```

`get_subscription_id()` returns the runtime override if set, falling back to the `.env` value.

#### Azure Client Matrix

| Client | SDK Package | Used For |
|:-------|:-----------|:---------|
| `ComputeManagementClient` | `azure-mgmt-compute` | VMs, VMSS |
| `ResourceManagementClient` | `azure-mgmt-resource` | Resource groups, locks, tags |
| `StorageManagementClient` | `azure-mgmt-storage` | Storage accounts |
| `SubscriptionClient` | `azure-mgmt-subscription` | Subscriptions, tenants, locations |
| `ManagementGroupsAPI` | `azure-mgmt-managementgroups` | Management group hierarchy |
| `AuthorizationManagementClient` | `azure-mgmt-authorization` | RBAC role assignments & definitions |
| `MonitorManagementClient` | `azure-mgmt-monitor` | Activity / audit logs |

### `utils/auth.py` — License Validation

Handles remote license validation against the license server:

| Function | Purpose |
|:---------|:--------|
| `validate_license()` | POST `AUTH_TOKEN` to `LICENSE_API_URL`, cache result |
| `get_licensed_features()` | Return `set` of feature flags from cached license |
| `has_feature(name)` | Check a single feature flag |
| `is_premium_licensed()` | True if any premium license is active |
| `invalidate_cache()` | Clear cached license (for testing) |

The validation result is cached for `LICENSE_CACHE_TTL` seconds (default 3600). If the license server is unreachable or the token is invalid, the cache is set to free-tier and no premium tools are registered.

### `utils/helpers.py` — Shared Utilities

| Function | Purpose |
|:---------|:--------|
| `make_api_request()` | Async HTTP client using `httpx` with timeout and error handling |
| `get_env_var()` | Thin wrapper around `os.getenv()` |
| `format_error_message()` | Formats exceptions into user-friendly strings |

### `license-server/` — License Validation Service

A self-contained FastAPI microservice:

| File | Purpose |
|:-----|:--------|
| `main.py` | FastAPI app with `POST /v1/license/validate` and `GET /health` |
| `generate_license.py` | CLI tool to create API keys and hashed license entries |
| `licenses.json` | Token-hash-to-license mapping (the "database") |
| `Dockerfile` | Container image |
| `requirements.txt` | `fastapi`, `uvicorn`, `pydantic` |

Tokens are stored as **SHA-256 hashes** — the plaintext API key is never persisted. The license server checks the hash, verifies expiry, and returns the tier and feature flags.

---

## Request Lifecycle

### Free tool call

1. **AI client** sends a JSON-RPC `tools/call` message over stdio.
2. **FastMCP** deserializes the request and dispatches to the matching `@mcp.tool()` function in `server.py`.
3. **server.py** wrapper validates inputs and delegates to `tools/cloud.py`.
4. `cloud.py` lazily initializes the Azure SDK client (using credentials from `config.py`).
5. **Azure SDK** makes a REST call to the Azure Resource Manager API.
6. Response flows back: SDK -> `cloud.py` (formats as string) -> `server.py` -> FastMCP -> stdio -> AI client.

### Premium tool call

Same as above, but the tool only exists if `_register_premium_tools()` found the matching feature flag in the license at startup. If not licensed, the tool is not registered and the AI client gets a "tool not found" error from the MCP protocol layer — it never reaches application code.

### Startup license check

1. `server.py` is imported.
2. Free tools are registered via `@mcp.tool()` decorators at module level.
3. `_register_premium_tools()` is called.
4. Inside, `get_licensed_features()` calls `validate_license()`.
5. `validate_license()` reads `AUTH_TOKEN` and `LICENSE_API_URL` from `config`.
6. If both are set, it `POST`s to `LICENSE_API_URL/v1/license/validate`.
7. The license server hashes the token, looks it up in `licenses.json`, checks expiry.
8. Returns `{valid, tier, features}`.
9. `_register_premium_tools()` registers `@mcp.tool()` only for granted features.
10. The MCP server starts listening on stdio.

---

## Transport

The server uses **stdio** transport exclusively. The AI client spawns `uv run python -m azops_mcp` as a child process and communicates via stdin/stdout using the MCP protocol. Stderr is used for logging.

```python
mcp.run(transport="stdio")
```

---

## Docker Compose (Local Dev)

For local development, `docker-compose.yml` orchestrates both services:

- **license-server** — long-running HTTP service on port 8000
- **mcp-server** — interactive stdio process, run via `docker compose run`

See [Docker](/azops-mcp/docker) for full usage.

---

## Error Handling Strategy

Every tool follows defensive error handling:

- **Input validation** — required parameters checked before any SDK call
- **ImportError** — caught separately to suggest `pip install` commands
- **Azure exceptions** — caught and formatted via `format_error_message()`
- **Catch-all** — top-level `except Exception` in every tool ensures the server never crashes

Errors are returned as plain-text strings (not exceptions) so the AI can relay them to the user.
