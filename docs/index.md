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
                                                          on startup
┌──────────────┐       MCP (stdio)       ┌──────────────┐ ─────────► ┌─────────────────┐
│  AI Assistant │  ◄──────────────────►  │  azops-mcp   │            │ License Server  │
│  (Cursor,     │   JSON-RPC messages    │  MCP Server   │ ◄──────── │ (validates keys) │
│   Claude, …)  │                        │               │  features └─────────────────┘
└──────────────┘                         └───────┬───────┘
                                                 │
                                          Azure SDK REST
                                                 │
                                                 ▼
                                          ┌─────────────┐
                                          │  Azure Cloud │
                                          └─────────────┘
```

The server runs locally as a subprocess of your AI client. On startup it validates the `AUTH_TOKEN` against a **license server** to determine which features are available. Free-tier tools (read-only) are always registered. Premium tools (write/mutate) only appear when the license grants the corresponding feature flag — without a valid token, premium tools are completely invisible to the AI client.

### Free & Premium Tiers

| Tier | What you get |
|:-----|:-------------|
| **Free** | 23 read-only and operational tools — no token needed |
| **Premium** | 8 additional write/mutate tools — requires a validated `AUTH_TOKEN` |

Premium tools are **not registered** without a valid license. They don't show up in `tools/list`, the LLM never sees them, and there is no "access denied" leakage. See [Authentication](/azops-mcp/authentication) for details.

## Project Structure

```
azops-mcp/
├── src/azops_mcp/
│   ├── __main__.py          # Module entry point
│   ├── server.py            # MCP server — free tools + conditional premium registration
│   ├── config.py            # ServerConfig dataclass & env loading
│   ├── tools/
│   │   └── cloud.py         # Azure SDK integrations (all Azure calls)
│   └── utils/
│       ├── auth.py          # Remote license validation & caching
│       └── helpers.py       # HTTP client, error formatting
├── license-server/          # License validation microservice
│   ├── main.py              # FastAPI app (POST /v1/license/validate)
│   ├── generate_license.py  # CLI tool to create license keys
│   ├── licenses.json        # Token-hash → license mapping (the "database")
│   ├── Dockerfile           # Container image for the license server
│   └── requirements.txt     # FastAPI + uvicorn
├── tests/                   # pytest test suite
├── Dockerfile               # Container image for the MCP server
├── docker-compose.yml       # Local dev: both services
├── pyproject.toml           # Project metadata & dependencies
├── quickstart.sh            # One-command setup script
└── .env.example             # Configuration template
```
