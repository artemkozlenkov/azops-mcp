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
┌──────────────────┐        stdio (JSON-RPC)        ┌───────────────────────────┐
│   AI Assistant    │  ◄────────────────────────────► │       azops-mcp           │
│   (Cursor, etc.)  │                                │                           │
└──────────────────┘                                 │  server.py                │
                                                     │    ├─ @mcp.tool() wrappers│
                                                     │    └─ paywall checks      │
                                                     │                           │
                                                     │  tools/                   │
                                                     │    ├─ cloud.py  (Azure)   │
                                                     │    ├─ containers.py       │
                                                     │    └─ monitoring.py       │
                                                     │                           │
                                                     │  utils/                   │
                                                     │    ├─ auth.py  (paywall)  │
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

The server is a single Python process started by the AI client as a subprocess. Communication happens over **stdio** using the [Model Context Protocol](https://modelcontextprotocol.io/) — a JSON-RPC-based protocol that lets AI assistants discover and call tools.

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
2. **Registers tools** — each `@mcp.tool()` decorated async function becomes a callable tool for the AI assistant.
3. **Routes calls** — thin wrappers that validate inputs, check paywall access, and delegate to the appropriate `tools/` module.
4. **Handles lifecycle** — `main()` starts the MCP server on stdio transport and installs signal handlers for graceful shutdown.

**Tool registration pattern:**

```python
@mcp.tool()
async def list_resource_groups() -> str:
    """List all resource groups in the subscription."""
    try:
        return await cloud.list_resource_groups()
    except Exception as e:
        return f"Error: {str(e)}"
```

Every tool follows this pattern:
- Decorated with `@mcp.tool()` so MCP SDK advertises it to clients
- Async function returning a `str` (or `Dict` for `health_check`)
- Input validation at the top
- Paywall check via `_check_paywall_access()` for write operations
- Delegates to the real implementation in `tools/cloud.py`
- Catches all exceptions and returns user-friendly error strings

**Paywall gating** is done by a helper function:

```python
def _check_paywall_access() -> Optional[str]:
    if not is_paywall_enabled():
        return "Access denied: AUTH_TOKEN not configured. ..."
    is_valid, error_msg = check_auth_token()
    if not is_valid:
        return f"Access denied: {error_msg} ..."
    return None  # Access granted
```

Tools that mutate resources call this before proceeding.

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
| Security | `secret_key`, `allowed_hosts`, `auth_token` |
| Debug | `debug` |

A global `config` singleton is created at import time. The `validate()` method checks for inconsistencies (e.g., incomplete Service Principal credentials, invalid timeouts).

`reload_config()` re-reads environment variables and creates a fresh instance.

### `tools/cloud.py` — Azure SDK Integration

This is the largest module (~1300 lines). It contains **all Azure API interactions**.

#### Lazy Client Initialization

Azure SDK clients are expensive to construct. `cloud.py` uses a lazy-loading pattern with module-level globals:

```python
_azure_credential = None
_compute_client = None
_resource_client = None
_storage_client = None

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

### `tools/containers.py` — Docker Management

Manages local Docker containers via `subprocess` calls to the `docker` CLI:

- `list_containers()` — runs `docker ps` with a custom format
- `get_container_logs(container_id, lines)` — runs `docker logs --tail`
- `restart_container(container_id)` — runs `docker restart`

Each function handles `FileNotFoundError` (Docker not installed) and `TimeoutExpired` gracefully.

### `tools/monitoring.py` — System Metrics

Collects local system health using platform-specific commands:

- `get_system_metrics()` — CPU (via `top`), memory (`free` / `vm_stat`), disk (`df -h`)
- `check_service_health(service_name)` — `systemctl` on Linux, `launchctl` on macOS
- `get_infrastructure_status()` — checks Docker availability and system uptime

### `utils/auth.py` — Paywall Authentication

Three functions for the AUTH_TOKEN paywall system:

| Function | Purpose |
|:---------|:--------|
| `is_paywall_enabled()` | Returns `True` if `AUTH_TOKEN` is set and non-empty |
| `check_auth_token()` | Validates token exists and is >= 8 characters; returns `(bool, str)` |
| `require_auth_token` | Decorator that wraps an async tool function with auth check |

### `utils/helpers.py` — Shared Utilities

| Function | Purpose |
|:---------|:--------|
| `make_api_request()` | Async HTTP client using `httpx` with timeout and error handling |
| `get_env_var()` | Thin wrapper around `os.getenv()` |
| `format_error_message()` | Formats exceptions into user-friendly strings |

---

## Request Lifecycle

Here is the full path of a typical tool call:

1. **AI client** sends a JSON-RPC `tools/call` message over stdio.
2. **FastMCP** deserializes the request and dispatches to the matching `@mcp.tool()` function in `server.py`.
3. **server.py** wrapper validates inputs and (for write ops) checks paywall via `_check_paywall_access()`.
4. Wrapper calls the appropriate function in **`tools/cloud.py`**.
5. `cloud.py` lazily initializes the Azure SDK client (using credentials from `config.py`).
6. **Azure SDK** makes a REST call to the Azure Resource Manager API.
7. Response flows back: SDK → `cloud.py` (formats as string) → `server.py` → FastMCP → stdio → AI client.
8. The AI assistant presents the result to the user.

---

## Transport

The server uses **stdio** transport exclusively. The AI client spawns `uv run python -m azops_mcp` as a child process and communicates via stdin/stdout using the MCP protocol. Stderr is used for logging.

```python
mcp.run(transport="stdio")
```

---

## Error Handling Strategy

Every tool follows defensive error handling:

- **Input validation** — required parameters checked before any SDK call
- **ImportError** — caught separately to suggest `pip install` commands
- **Azure exceptions** — caught and formatted via `format_error_message()`
- **Catch-all** — top-level `except Exception` in every tool ensures the server never crashes

Errors are returned as plain-text strings (not exceptions) so the AI can relay them to the user.
