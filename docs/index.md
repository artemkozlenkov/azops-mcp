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
- **Resource Groups** — List and inspect resource groups
- **Virtual Machines** — Start, stop, restart, deallocate VMs and scale VMSS
- **Storage Accounts** — List and inspect storage account status
- **Governance** — Management groups, RBAC role definitions, resource locks
- **Auditing** — Query Azure Activity Log for recent changes
- **Health Monitoring** — Server health checks and Azure SDK availability

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

### 26 Tools

| Category | Count | Examples |
|:---------|:------|:--------|
| Health & Status | 1 | `health_check` |
| Subscriptions & Auth | 8 | `list_subscriptions`, `auth_status`, `account_show`, `account_get_access_token` |
| Management Groups | 2 | `list_management_groups`, `get_management_group` |
| RBAC | 1 | `list_role_definitions` |
| Locks & Tags | 2 | `list_resource_locks`, `list_tags` |
| Activity Log | 1 | `get_activity_log` |
| Resource Groups | 2 | `list_resource_groups`, `list_resources` |
| Virtual Machines | 7 | `start_vm`, `stop_vm`, `deallocate_vm`, `scale_vmss` |
| Storage | 2 | `list_storage_accounts`, `get_storage_status` |

See the [Tools Reference](/azops-mcp/tools-reference) for full details on every tool.

## Project Structure

```
azops-mcp/
├── src/azops_mcp/
│   ├── __main__.py          # Module entry point
│   ├── server.py            # MCP server — all 26 tool definitions
│   ├── config.py            # ServerConfig dataclass & env loading
│   ├── tools/
│   │   └── cloud.py         # Azure SDK integrations (all Azure calls)
│   └── utils/
│       └── helpers.py       # HTTP client, error formatting
├── tests/                   # pytest test suite
├── Dockerfile               # Container image for the MCP server
├── docker-compose.yml       # Docker Compose for the MCP server
├── pyproject.toml           # Project metadata & dependencies
├── quickstart.sh            # One-command setup script
└── .env.example             # Configuration template
```
