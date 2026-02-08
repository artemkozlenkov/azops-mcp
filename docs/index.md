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
- **Resource Groups** — Create, delete, tag, and list resource groups
- **Virtual Machines** — Start, stop, restart, deallocate VMs and scale VMSS
- **Storage Accounts** — List and inspect storage account status
- **Governance** — Management groups, RBAC role assignments, resource locks
- **Auditing** — Query Azure Activity Log for recent changes
- **Health Monitoring** — Server health checks and Azure SDK availability

### How It Works

```
┌──────────────┐       MCP (stdio)       ┌──────────────┐     Azure SDK     ┌─────────┐
│  AI Assistant │  ◄──────────────────►  │  azops-mcp   │  ◄────────────►  │  Azure  │
│  (Cursor,     │   JSON-RPC messages    │  MCP Server   │   REST API calls │  Cloud  │
│   Claude, …)  │                        │               │                  │         │
└──────────────┘                         └──────────────┘                  └─────────┘
```

The server runs locally as a subprocess of your AI client. It communicates over **stdio** using the MCP JSON-RPC protocol. When the assistant decides to call a tool (e.g. `list_resource_groups`), the server authenticates against Azure using your CLI credentials or a Service Principal and returns the results.

### Free & Paid Tiers

Read-only tools work without any token. Write operations (create, delete, modify) require an `AUTH_TOKEN` in your `.env` file. See [Authentication](/azops-mcp/authentication) for details.

## Project Structure

```
azops-mcp/
├── src/azops_mcp/
│   ├── __main__.py          # Module entry point
│   ├── server.py            # MCP server — tool definitions & routing
│   ├── config.py            # ServerConfig dataclass & env loading
│   ├── tools/
│   │   ├── cloud.py         # Azure SDK integrations (all Azure calls)
│   │   ├── containers.py    # Docker container management
│   │   └── monitoring.py    # System metrics & service health
│   └── utils/
│       ├── auth.py          # Paywall / AUTH_TOKEN validation
│       └── helpers.py       # HTTP client, error formatting
├── tests/                   # pytest test suite
├── pyproject.toml           # Project metadata & dependencies
├── quickstart.sh            # One-command setup script
└── .env.example             # Configuration template
```
