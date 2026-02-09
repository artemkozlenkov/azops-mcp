---
title: Home
layout: home
nav_order: 1
---

# azops-mcp

**Azure Infrastructure MCP Server** — manage Azure cloud resources directly from AI assistants like Claude, Cursor, or any MCP-compatible client.
{: .fs-6 .fw-300 }

[Get Started](/azops-mcp/getting-started){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[Tools Reference](/azops-mcp/tools-reference){: .btn .fs-5 .mb-4 .mb-md-0 }

---

## What is azops-mcp?

`azops-mcp` is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that exposes Azure management operations as tools that AI assistants can invoke. Instead of switching between the Azure Portal, CLI, and your editor, you talk to your AI assistant in natural language and it calls the right Azure SDK operations behind the scenes.

### Key Capabilities

- **Subscription Management** — List, switch, and inspect Azure subscriptions and tenants
- **Account Operations** — View subscription details, get access tokens, clear cached credentials
- **Resource Groups** — List and manage resource groups, tags, locks
- **Virtual Machines** — Start, stop, restart, deallocate VMs and scale VMSS
- **Storage Accounts** — List and inspect storage account status
- **App Configuration** — Manage stores and key-value pairs
- **App Service** — Manage App Service plans and web apps
- **Web Apps for Containers** — Deploy containerized apps with VNet integration and RBAC
- **Container Registry** — Manage ACR instances, images, tasks, and network rules
- **Virtual Networks** — Create and manage VNets, subnets, and peerings
- **Azure AD / Entra ID** — Manage users, groups, applications, and tenants
- **Governance** — Management groups, RBAC role definitions and assignments, resource locks
- **Auditing** — Query Azure Activity Log for recent changes
- **Docker Runtime** — List, inspect, and restart local Docker containers
- **System Monitoring** — CPU, memory, disk metrics, service health, infrastructure status

### How It Works

```
┌──────────────┐       MCP (stdio)       ┌──────────────┐
│  AI Assistant │  ◄──────────────────►  │  azops-mcp   │
│  (Cursor,     │   JSON-RPC messages    │  MCP Server   │
│   Claude, …)  │                        │               │
└──────────────┘                         └───────┬───────┘
                                                 │
                                          Azure SDK REST
                                                 │
                                                 ▼
                                          ┌─────────────┐
                                          │  Azure Cloud │
                                          └─────────────┘
```

The server runs locally as a subprocess of your AI client. It communicates over **stdio** using the Model Context Protocol and calls Azure SDK operations on your behalf using your local credentials (`az login`) or a configured Service Principal.

### 93 Tools Across 17 Categories

| Category | Count | Examples |
|:---------|:------|:--------|
| Health & Status | 1 | `health_check` |
| Subscriptions & Auth | 8 | `list_subscriptions`, `auth_status`, `account_show`, `account_get_access_token` |
| Management Groups | 2 | `list_management_groups`, `get_management_group` |
| RBAC | 4 | `list_role_definitions`, `create_role_assignment`, `list_role_assignments_for_principal` |
| Governance | 3 | `list_resource_locks`, `list_tags`, `get_activity_log` |
| Resource Groups | 2 | `list_resource_groups`, `list_resources` |
| Virtual Machines | 7 | `start_vm`, `stop_vm`, `deallocate_vm`, `scale_vmss` |
| Storage | 2 | `list_storage_accounts`, `get_storage_status` |
| App Configuration | 6 | `appconfig_list`, `appconfig_kv_list`, `appconfig_kv_set` |
| App Service | 7 | `appservice_plan_list`, `webapp_list`, `webapp_start` |
| Web Apps for Containers | 7 | `webapp_create_for_container`, `webapp_grant_cr_access` |
| Container Registry | 20 | `acr_list_registries`, `acr_create_registry`, `acr_list_tags` |
| Virtual Networks | 9 | `vnet_list`, `vnet_create`, `vnet_subnet_create` |
| Azure AD (Entra ID) | 9 | `aad_list_users`, `aad_create_user`, `aad_list_applications` |
| Docker Runtime | 3 | `list_containers`, `get_container_logs`, `restart_container` |
| Monitoring | 3 | `get_system_metrics`, `check_service_health`, `get_infrastructure_status` |

See the [Tools Reference](/azops-mcp/tools-reference) for full details on every tool.

## Project Structure

```
azops-mcp/
├── src/azops_mcp/
│   ├── __main__.py               # Module entry point
│   ├── server.py                 # MCP server — 93 tool definitions
│   ├── config.py                 # ServerConfig dataclass & env loading
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
├── Dockerfile                    # Container image for the MCP server
├── docker-compose.yml            # Docker Compose for the MCP server
├── pyproject.toml                # Project metadata & dependencies
├── quickstart.sh                 # One-command setup script
└── .env.example                  # Configuration template
```
