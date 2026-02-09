# Azure Infrastructure MCP Server

A Model Context Protocol (MCP) server for managing Azure infrastructure directly from AI assistants like Claude in Cursor, VS Code, Claude Desktop, or any MCP-compatible client.

## What You Can Do

- **Manage Subscriptions** - List and switch between Azure subscriptions
- **Inspect Accounts** - View subscription details, get access tokens, clear cached credentials
- **Organize Resources** - List and manage resource groups
- **Control VMs** - Start, stop, restart, deallocate virtual machines
- **Scale VMSS** - Adjust VM Scale Set capacity
- **Manage Storage** - List and inspect storage accounts
- **Governance** - Work with management groups, RBAC, and resource locks
- **Audit** - View activity logs and track changes

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

## Available Tools (26)

| Category | Tools |
|:---------|:------|
| Health | `health_check` |
| Subscriptions & Auth | `list_subscriptions`, `set_subscription`, `auth_status`, `account_show`, `account_clear`, `account_get_access_token`, `list_locations`, `list_tenants` |
| Management Groups | `list_management_groups`, `get_management_group` |
| RBAC | `list_role_definitions` |
| Locks | `list_resource_locks` |
| Tags | `list_tags` |
| Activity Log | `get_activity_log` |
| Resource Groups | `list_resource_groups`, `list_resources` |
| VMs | `list_vms`, `get_vm_status`, `start_vm`, `stop_vm`, `restart_vm`, `deallocate_vm`, `scale_vmss` |
| Storage | `list_storage_accounts`, `get_storage_status` |

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
│   ├── __main__.py        # Module entry point
│   ├── server.py          # MCP server — all 26 tool definitions
│   ├── config.py          # Configuration management
│   ├── tools/
│   │   └── cloud.py       # Azure SDK integrations
│   └── utils/
│       └── helpers.py     # HTTP client, error formatting
├── tests/                 # Unit tests
├── docs/                  # GitHub Pages documentation
├── Dockerfile             # MCP server container image
├── docker-compose.yml     # Docker Compose for the MCP server
├── pyproject.toml         # Dependencies & metadata
├── quickstart.sh          # Setup script
└── .env.example           # Configuration template
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
