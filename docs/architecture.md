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
┌──────────────────┐  stdio (JSON-RPC)  ┌───────────────────────────────────┐
│   AI Assistant    │ ◄────────────────► │           azops-mcp              │
│   (Cursor, etc.)  │                   │                                   │
└──────────────────┘                    │  server.py  (93 tools)            │
                                        │                                   │
                                        │  tools/                           │
                                        │    ├─ _clients.py      (shared)   │
                                        │    ├─ subscription.py  (auth)     │
                                        │    ├─ compute.py       (VMs)      │
                                        │    ├─ networking.py    (VNets)    │
                                        │    ├─ container_registry.py (ACR) │
                                        │    ├─ active_directory.py  (AAD)  │
                                        │    ├─ ...              (13 more)  │
                                        │                                   │
                                        │  config.py                        │
                                        │  utils/helpers.py                 │
                                        └──────────────┬────────────────────┘
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

All 93 tools are registered at module level using the `@mcp.tool()` decorator. Each tool is a thin async wrapper that validates inputs, delegates to the appropriate tool module, and catches exceptions:

```python
@mcp.tool()
async def list_resource_groups() -> str:
    """List all resource groups in the subscription."""
    try:
        return await resource_groups.list_resource_groups()
    except Exception as e:
        return f"Error: {e}"
```

The MCP `tools/list` response includes all 93 tools with their names, descriptions, and parameter schemas. The AI client uses this to decide which tool to call.

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
2. **Imports tool modules** — imports all 14 tool modules from the `tools/` package.
3. **Registers all 93 tools** — each `@mcp.tool()` decorated async function becomes a callable tool for the AI assistant.
4. **Handles lifecycle** — `main()` starts the MCP server on stdio transport and installs signal handlers for graceful shutdown.

Tool pattern:

```python
from .tools import subscription, compute, networking, ...

@mcp.tool()
async def start_vm(resource_group: str, vm_name: str) -> str:
    """Start a virtual machine."""
    try:
        return await compute.manage_vm(resource_group, vm_name, "start")
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

### `tools/` — Azure SDK Integrations (Modular)

The tools package is organized into 14 focused modules grouped by Azure service area:

| Module | Responsibility | Key Functions |
|:-------|:---------------|:-------------|
| `_clients.py` | Shared auth & lazy SDK client factories | `_get_azure_credential()`, `_get_compute_client()`, `set_subscription_id()` |
| `subscription.py` | Subscriptions, auth, tenants, locations | `list_subscriptions()`, `configure_subscription()`, `get_auth_status()` |
| `resource_groups.py` | Resource groups, tags, locks, activity log | `list_resource_groups()`, `list_tags()`, `get_activity_log()` |
| `compute.py` | VMs, VMSS, resource listing | `list_resources()`, `manage_vm()`, `scale_vmss()` |
| `networking.py` | VNets, subnets, peerings | `vnet_list()`, `vnet_create()`, `vnet_subnet_create()` |
| `authorization.py` | RBAC roles & assignments | `list_role_definitions()`, `create_role_assignment()` |
| `management_groups.py` | Management group hierarchy | `list_management_groups()`, `get_management_group()` |
| `app_configuration.py` | App Configuration stores & key-values | `appconfig_list()`, `appconfig_kv_set()` |
| `app_service.py` | App Service plans & web apps | `appservice_plan_list()`, `webapp_list()`, `webapp_start()` |
| `container_registry.py` | Azure Container Registry (ACR) | `acr_list_registries()`, `acr_create_registry()` |
| `active_directory.py` | Azure AD / Entra ID | `list_users()`, `create_user()`, `list_applications()` |
| `webapp_deployment.py` | Web App for Containers deployment | `webapp_create_for_container()`, `webapp_grant_cr_access()` |
| `docker.py` | Local Docker container runtime | `list_containers()`, `get_container_logs()` |
| `monitoring.py` | System metrics & health | `get_system_metrics()`, `check_service_health()` |

#### `_clients.py` — Shared Authentication & Client Factories

This is the foundation module. It provides:

**Lazy Client Initialization** — Azure SDK clients are expensive to construct. `_clients.py` uses module-level globals with lazy loading:

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

**Authentication Chain:**

```python
def _get_azure_credential():
    # Priority:
    # 1. Service Principal (if fully configured)
    # 2. Azure CLI + Managed Identity (ChainedTokenCredential)
```

If `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_TENANT_ID` are all set, a `ClientSecretCredential` is used. Otherwise, a `ChainedTokenCredential` tries Azure CLI first, then Managed Identity.

**Runtime Subscription Override:**

```python
_runtime_config = {"subscription_id": None}

def set_subscription_id(subscription_id: str):
    _runtime_config["subscription_id"] = subscription_id
    # Clear ALL cached clients so they pick up the new subscription
```

`get_subscription_id()` returns the runtime override if set, falling back to the `.env` value.

#### Azure Client Matrix

| Client | SDK Package | Used By |
|:-------|:-----------|:--------|
| `ComputeManagementClient` | `azure-mgmt-compute` | `compute.py` |
| `ResourceManagementClient` | `azure-mgmt-resource` | `resource_groups.py`, `compute.py` |
| `StorageManagementClient` | `azure-mgmt-storage` | `compute.py` |
| `SubscriptionClient` | `azure-mgmt-subscription` | `subscription.py` |
| `ManagementGroupsAPI` | `azure-mgmt-managementgroups` | `management_groups.py` |
| `AuthorizationManagementClient` | `azure-mgmt-authorization` | `authorization.py` |
| `MonitorManagementClient` | `azure-mgmt-monitor` | `resource_groups.py` |
| `WebSiteManagementClient` | `azure-mgmt-web` | `app_service.py`, `webapp_deployment.py` |
| `NetworkManagementClient` | `azure-mgmt-network` | `networking.py`, `webapp_deployment.py` |
| `ContainerRegistryManagementClient` | `azure-mgmt-containerregistry` | `container_registry.py` |
| `AppConfigurationManagementClient` | `azure-mgmt-appconfiguration` | `app_configuration.py` |
| `AzureAppConfigurationClient` | `azure-appconfiguration` | `app_configuration.py` |
| `GraphServiceClient` | `msgraph-sdk` | `active_directory.py` |

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
3. **server.py** wrapper validates inputs and delegates to the appropriate tool module (e.g., `compute.py`, `networking.py`).
4. The tool module lazily initializes the Azure SDK client via `_clients.py` (using credentials from `config.py`).
5. **Azure SDK** makes a REST call to the Azure Resource Manager API.
6. Response flows back: SDK -> tool module (formats as string) -> `server.py` -> FastMCP -> stdio -> AI client.

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

---

## Testing

Tests are organized into separate files by integration category, mirroring the tool module structure:

| Test File | Covers |
|:----------|:-------|
| `test_subscription.py` | Subscription, auth, account tools |
| `test_resource_groups.py` | Resource groups, tags, locks, activity log |
| `test_compute.py` | VMs, VMSS, storage, resources |
| `test_networking.py` | VNets, subnets, peerings |
| `test_authorization.py` | RBAC roles & assignments |
| `test_container_registry.py` | ACR tools |
| `test_active_directory.py` | Azure AD tools |
| `test_webapp_deployment.py` | Web App for Containers |
| `test_docker.py` | Docker container runtime |
| `test_monitoring.py` | System metrics & health |
| `test_health.py` | Health check & rate limiting |
| `test_config.py` | Configuration management |

All tests use `pytest` with `unittest.mock` to mock Azure SDK calls. Run with:

```bash
pytest tests/ -v
```
