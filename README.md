# Azure Infrastructure MCP Server

A Model Context Protocol (MCP) server for managing Azure infrastructure directly from AI assistants like Claude in Cursor, VS Code, Claude Desktop, or any MCP-compatible client.

## What You Can Do

- **Manage Subscriptions** — List and switch between Azure subscriptions
- **Inspect Accounts** — View subscription details, get access tokens, clear cached credentials
- **Organize Resources** — List and manage resource groups, tags, locks
- **Control VMs** — Start, stop, restart, deallocate virtual machines and scale VMSS
- **Manage Storage** — List and inspect storage accounts
- **App Configuration** — Manage App Configuration stores and key-values
- **App Service** — List and manage App Service plans and web apps
- **Deploy Web Apps** — Create and manage Web Apps for Containers with Docker/Podman
- **Container Registry** — List, create, and manage ACR instances, images, tasks, and network rules
- **Virtual Networks** — Create and manage VNets, subnets, and peerings
- **Identity & Access** — Manage Azure AD users, groups, applications, and RBAC permissions
- **Governance** — Work with management groups, resource locks, and tags
- **Audit** — View activity logs and track changes
- **Docker Runtime** — List, inspect logs, and restart local Docker containers
- **Monitoring** — System metrics, service health, and infrastructure status

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Azure CLI installed and logged in (`az login`)
- [uv](https://astral.sh/uv) package manager

### 2. Install

```bash
git clone <repo-url> azops-mcp
cd azops-mcp
./quickstart.sh
```

The script will:
- Create a virtual environment with Python 3.12
- Install all dependencies (including Azure SDKs)
- Show configuration for Claude Desktop and Cursor

### 3. Configure Your AI Client

**Claude Desktop** — add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "azops-mcp": {
      "command": "uv",
      "args": ["--directory", "/full/path/to/azops-mcp", "run", "python", "-m", "azops_mcp"]
    }
  }
}
```

**Cursor** — add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "azops-mcp": {
      "command": "uv",
      "args": ["--directory", "/full/path/to/azops-mcp", "run", "python", "-m", "azops_mcp"]
    }
  }
}
```

Restart your AI client after saving the configuration.

### 4. Start Using

```
User: List my Azure subscriptions
User: Show resource groups in subscription xxx-xxx-xxx
User: Start the VM "web-server" in resource group "production"
User: What VMs are running in my dev resource group?
```

## Authentication

| Priority | Method | When |
|:---------|:-------|:-----|
| 1 | **Service Principal** | `AZURE_CLIENT_ID` + `SECRET` + `TENANT_ID` all set in `.env` |
| 2 | **Azure CLI** | After `az login` (recommended for development) |
| 3 | **Managed Identity** | When running in Azure |

See the [Authentication docs](https://artemkozlenkov.github.io/azops-mcp/authentication) for the full walkthrough.

## Available Tools (90+)

| Category | Tools |
|:---------|:------|
| Health | `health_check` |
| Subscriptions & Auth | `list_subscriptions`, `set_subscription`, `auth_status`, `account_show`, `account_clear`, `account_get_access_token`, `list_locations`, `list_tenants` |
| Management Groups | `list_management_groups`, `get_management_group` |
| RBAC | `list_role_definitions`, `create_role_assignment`, `delete_role_assignment`, `list_role_assignments_for_principal` |
| Governance | `list_resource_locks`, `list_tags`, `get_activity_log` |
| Resource Groups | `list_resource_groups`, `list_resources` |
| VMs & VMSS | `list_vms`, `get_vm_status`, `start_vm`, `stop_vm`, `restart_vm`, `deallocate_vm`, `scale_vmss` |
| Storage | `list_storage_accounts`, `get_storage_status` |
| App Configuration | `appconfig_list`, `appconfig_show`, `appconfig_kv_list`, `appconfig_kv_show`, `appconfig_kv_set`, `appconfig_kv_delete` |
| App Service | `appservice_plan_list`, `appservice_plan_show`, `webapp_list`, `webapp_show`, `webapp_start`, `webapp_stop`, `webapp_restart` |
| Web Apps for Containers | `webapp_create_for_container`, `webapp_grant_cr_access`, `webapp_configure_vnet_integration`, `webapp_assign_identity`, `webapp_view_logs`, `webapp_set_container_registry_credentials`, `webapp_delete` |
| Container Registry | `acr_list_registries`, `acr_show_registry`, `acr_create_registry`, `acr_delete_registry`, `acr_update_registry`, `acr_get_credentials`, `acr_get_login_server`, `acr_list_repositories`, `acr_list_tags`, `acr_show_task`, `acr_list_tasks`, `acr_create_task`, `acr_delete_task`, `acr_run_task`, `acr_list_builds`, `acr_show_quotas`, `acr_show_usage`, `acr_list_network_rules`, `acr_update_network_rules`, `acr_reset_client` |
| Virtual Networks | `vnet_list`, `vnet_show`, `vnet_create`, `vnet_delete`, `vnet_subnet_list`, `vnet_subnet_show`, `vnet_subnet_create`, `vnet_subnet_delete`, `vnet_peering_list` |
| Azure AD (Entra ID) | `aad_list_users`, `aad_show_user`, `aad_create_user`, `aad_delete_user`, `aad_list_applications`, `aad_create_application`, `aad_list_groups`, `aad_verify_tenant`, `aad_reset_client` |
| Docker Runtime | `list_containers`, `get_container_logs`, `restart_container` |
| Monitoring | `get_system_metrics`, `check_service_health`, `get_infrastructure_status` |

## Docker

Run the MCP server as a container:

```bash
# Build the image
docker compose build

# Run the MCP server interactively (stdio transport)
docker compose run --rm mcp-server
```

See the [Docker docs](https://artemkozlenkov.github.io/azops-mcp/docker) for full instructions.

## Project Structure

```
azops-mcp/
├── src/azops_mcp/
│   ├── __main__.py               # Module entry point
│   ├── server.py                 # MCP server — 93 tool definitions
│   ├── config.py                 # Configuration management
│   ├── tools/                    # Azure SDK integrations (by category)
│   │   ├── _clients.py           # Shared auth & Azure SDK client factories
│   │   ├── subscription.py       # Subscriptions, auth, tenants, locations
│   │   ├── resource_groups.py    # Resource groups, tags, locks, activity log
│   │   ├── compute.py            # VMs, VMSS, resource listing
│   │   ├── networking.py         # VNets, subnets, peerings
│   │   ├── authorization.py      # RBAC roles & assignments
│   │   ├── management_groups.py  # Management group hierarchy
│   │   ├── app_configuration.py  # App Configuration stores & key-values
│   │   ├── app_service.py        # App Service plans & web apps
│   │   ├── container_registry.py # Azure Container Registry (ACR)
│   │   ├── active_directory.py   # Azure AD / Entra ID
│   │   ├── webapp_deployment.py  # Web App for Containers deployment
│   │   ├── docker.py             # Local Docker container runtime
│   │   └── monitoring.py         # System metrics & health
│   └── utils/
│       └── helpers.py            # HTTP client, error formatting
├── tests/                        # Unit tests (per integration)
│   ├── test_subscription.py
│   ├── test_resource_groups.py
│   ├── test_compute.py
│   ├── test_networking.py
│   ├── test_authorization.py
│   ├── test_container_registry.py
│   ├── test_active_directory.py
│   ├── test_webapp_deployment.py
│   ├── test_docker.py
│   ├── test_monitoring.py
│   ├── test_health.py
│   └── test_config.py
├── docs/                          # GitHub Pages documentation
├── Dockerfile                     # MCP server container image
├── docker-compose.yml             # Docker Compose for the MCP server
├── pyproject.toml                 # Dependencies & metadata
├── quickstart.sh                  # Setup script
└── .env.example                   # Configuration template
```

## Configuration

| Variable | Default | Description |
|:---------|:--------|:------------|
| `AZURE_SUBSCRIPTION_ID` | — | Default subscription |
| `AZURE_DEFAULT_LOCATION` | `eastus` | Default region for new resources |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Max requests/minute |

See `.env.example` for the complete list.

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Code quality
black src/ tests/
ruff check src/ tests/
mypy src/

# Run server manually
uv run python -m azops_mcp
```

## Documentation

Full documentation is available at [artemkozlenkov.github.io/azops-mcp](https://artemkozlenkov.github.io/azops-mcp/).

- [Getting Started](https://artemkozlenkov.github.io/azops-mcp/getting-started)
- [Architecture](https://artemkozlenkov.github.io/azops-mcp/architecture)
- [Tools Reference](https://artemkozlenkov.github.io/azops-mcp/tools-reference)
- [Authentication](https://artemkozlenkov.github.io/azops-mcp/authentication)
- [Configuration](https://artemkozlenkov.github.io/azops-mcp/configuration)
- [Docker](https://artemkozlenkov.github.io/azops-mcp/docker)

## License

MIT
