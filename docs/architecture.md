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
┌──────────────────┐  stdio (JSON-RPC)  ┌───────────────────────────┐
│   AI Assistant    │ ◄────────────────► │       azops-mcp           │
│   (Cursor, etc.)  │                   │                           │
└──────────────────┘                    │  server.py                │
                                        │    └─ 26 tools            │
                                        │                           │
                                        │  tools/                   │
                                        │    └─ cloud.py  (Azure)   │
                                        │                           │
                                        │  utils/                   │
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
```

`azops-mcp` is a single Python process started by the AI client as a subprocess. It communicates over **stdio** using the [Model Context Protocol](https://modelcontextprotocol.io/) and calls Azure SDK operations using your local credentials or a configured Service Principal.

---

## Tool Registration

All 26 tools are registered at module level using the `@mcp.tool()` decorator. Each tool is a thin async wrapper that validates inputs, delegates to `tools/cloud.py`, and catches exceptions:

```python
@mcp.tool()
async def list_resource_groups() -> str:
    """List all resource groups in the subscription."""
    try:
        return await cloud.list_resource_groups()
    except Exception as e:
        return f"Error: {e}"
```

The MCP `tools/list` response includes all 26 tools with their names, descriptions, and parameter schemas. The AI client uses this to decide which tool to call.

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
2. **Registers all 26 tools** — each `@mcp.tool()` decorated async function becomes a callable tool for the AI assistant.
3. **Handles lifecycle** — `main()` starts the MCP server on stdio transport and installs signal handlers for graceful shutdown.

Tool pattern:

```python
@mcp.tool()
async def list_resource_groups() -> str:
    """List all resource groups in the subscription."""
    try:
        return await cloud.list_resource_groups()
    except Exception as e:
        return f"Error: {e}"
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
| `AuthorizationManagementClient` | `azure-mgmt-authorization` | RBAC role definitions |
| `MonitorManagementClient` | `azure-mgmt-monitor` | Activity / audit logs |

### `utils/helpers.py` — Shared Utilities

| Function | Purpose |
|:---------|:--------|
| `make_api_request()` | Async HTTP client using `httpx` with timeout and error handling |
| `get_env_var()` | Thin wrapper around `os.getenv()` |
| `format_error_message()` | Formats exceptions into user-friendly strings |

---

## Request Lifecycle

1. **AI client** sends a JSON-RPC `tools/call` message over stdio.
2. **FastMCP** deserializes the request and dispatches to the matching `@mcp.tool()` function in `server.py`.
3. **server.py** wrapper validates inputs and delegates to `tools/cloud.py`.
4. `cloud.py` lazily initializes the Azure SDK client (using credentials from `config.py`).
5. **Azure SDK** makes a REST call to the Azure Resource Manager API.
6. Response flows back: SDK -> `cloud.py` (formats as string) -> `server.py` -> FastMCP -> stdio -> AI client.

---

## Transport

The server uses **stdio** transport exclusively. The AI client spawns `uv run python -m azops_mcp` as a child process and communicates via stdin/stdout using the MCP protocol. Stderr is used for logging.

```python
mcp.run(transport="stdio")
```

---

## Docker Compose

For containerized usage, `docker-compose.yml` provides the MCP server as a Docker service:

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
