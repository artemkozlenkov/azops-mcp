# Azure Infrastructure MCP Server

A Model Context Protocol (MCP) server for managing Azure infrastructure directly from AI assistants like Claude in Cursor, VS Code, Claude Desktop, or any MCP-compatible client.

## What You Can Do

- **Manage Subscriptions** - List and switch between Azure subscriptions
- **Organize Resources** - Create, tag, and manage resource groups
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

### Azure Authentication

| Priority | Method | When |
|:---------|:-------|:-----|
| 1 | **Service Principal** | `AZURE_CLIENT_ID` + `SECRET` + `TENANT_ID` all set in `.env` |
| 2 | **Azure CLI** | After `az login` (recommended for development) |
| 3 | **Managed Identity** | When running in Azure |

### Premium License

The server has two tiers. Free-tier tools (23 read-only/operational) are always available. Premium tools (8 write/mutate operations) require a license validated against a remote license server.

**Without a valid license, premium tools are completely invisible** — they are not registered in the MCP tool catalog and the LLM never sees them.

To enable premium features:

```bash
# 1. Generate a license key
cd license-server
python generate_license.py --tier pro --customer your-name

# 2. Add the hash to license-server/licenses.json
# 3. Start the license server
uvicorn main:app --port 8000

# 4. Configure .env
AUTH_TOKEN=azops_your-key-here
LICENSE_API_URL=http://localhost:8000
```

See the [Authentication docs](https://artemkozlenkov.github.io/azops-mcp/authentication) for the full walkthrough.

## Available Tools

### Free Tier (23 tools — always available)

| Category | Tools |
|:---------|:------|
| Health | `health_check` |
| Subscriptions | `list_subscriptions`, `set_subscription`, `auth_status`, `list_locations`, `list_tenants` |
| Management Groups | `list_management_groups`, `get_management_group` |
| RBAC | `list_role_definitions` |
| Locks | `list_resource_locks` |
| Tags | `list_tags` |
| Activity Log | `get_activity_log` |
| Resource Groups | `list_resource_groups`, `list_resources` |
| VMs | `list_vms`, `get_vm_status`, `start_vm`, `stop_vm`, `restart_vm`, `deallocate_vm`, `scale_vmss` |
| Storage | `list_storage_accounts`, `get_storage_status` |

### Premium Tier (8 tools — require valid license)

| Feature Flag | Tools |
|:------------|:------|
| `rg_write` | `create_resource_group`, `delete_resource_group` |
| `rbac` | `list_role_assignments` |
| `locks_write` | `create_resource_lock`, `delete_resource_lock` |
| `tags_write` | `set_resource_group_tags` |
| `mg_write` | `create_management_group`, `delete_management_group` |

## Docker Compose (Local Dev)

Run everything with containers:

```bash
# Start the license server
docker compose up license-server

# Run the MCP server interactively
docker compose run --rm mcp-server

# Generate a license key
docker compose run --rm generate-license --tier pro --customer acme
```

See the [Docker docs](https://artemkozlenkov.github.io/azops-mcp/docker) for full instructions.

## Project Structure

```
azops-mcp/
├── src/azops_mcp/
│   ├── __main__.py        # Module entry point
│   ├── server.py          # MCP server — free + conditional premium tools
│   ├── config.py          # Configuration management
│   ├── tools/
│   │   └── cloud.py       # Azure SDK integrations
│   └── utils/
│       ├── auth.py        # Remote license validation & caching
│       └── helpers.py     # HTTP client, error formatting
├── license-server/        # License validation microservice
│   ├── main.py            # FastAPI app
│   ├── generate_license.py
│   ├── licenses.json      # Token hash → license mapping
│   └── Dockerfile
├── tests/                 # Unit tests
├── docs/                  # GitHub Pages documentation
├── Dockerfile             # MCP server container image
├── docker-compose.yml     # Local dev orchestration
├── pyproject.toml         # Dependencies & metadata
├── quickstart.sh          # Setup script
└── .env.example           # Configuration template
```

## Configuration

| Variable | Default | Description |
|:---------|:--------|:------------|
| `AZURE_SUBSCRIPTION_ID` | — | Default subscription |
| `AZURE_DEFAULT_LOCATION` | `eastus` | Default region for new resources |
| `AUTH_TOKEN` | — | License key (validated remotely) |
| `LICENSE_API_URL` | — | License server URL |
| `LICENSE_CACHE_TTL` | `3600` | License cache duration (seconds) |
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
