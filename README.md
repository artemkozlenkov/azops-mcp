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

### 3. Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

### 4. Configure Cursor (Optional)

Add to `~/.cursor/mcp.json`:

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

Restart Claude Desktop after adding the configuration.

### 5. Start Using

In Cursor chat, you can now:

```
User: List my Azure subscriptions
User: Show resource groups in subscription xxx-xxx-xxx
User: Start the VM "web-server" in resource group "production"
User: What VMs are running in my dev resource group?
```

### Optional: Configure Cursor

If you also use Cursor, add the same configuration to `~/.cursor/mcp.json`:

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

## Authentication

### Option 1: Azure CLI (Recommended)

```bash
az login
```

That's it! The server uses your CLI credentials automatically.

### Option 2: Service Principal (Production)

Create a `.env` file:

```env
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

### Option 3: Set Subscription in Chat

No configuration needed - use `list_subscriptions` and `set_subscription` tools directly in chat.

### Authentication Priority

1. **Service Principal** - If all credentials are set in `.env`
2. **Azure CLI** - Uses `az login` credentials
3. **Managed Identity** - When running in Azure

Use `auth_status` to check which method is active.

## Paywall Authentication

The server supports a paywall authentication system that restricts access to certain features:

### Free Tier (No AUTH_TOKEN required)
- Read-only operations
- `list_subscriptions`, `list_resource_groups`, `list_vms`, `list_storage_accounts`
- `get_vm_status`, `get_storage_status`, `list_locations`, `list_tenants`
- `auth_status`, `health_check`

### Paid Tier (AUTH_TOKEN required)
Full CRUD operations including:
- `create_resource_group`, `delete_resource_group`
- `create_resource_lock`, `delete_resource_lock`
- `set_resource_group_tags`
- `list_role_assignments` (RBAC assignment management)

### Setting AUTH_TOKEN

Add to your `.env` file:
```env
AUTH_TOKEN=your-secure-auth-token-min-8-chars
```

**Note**: AUTH_TOKEN must be at least 8 characters long.

If AUTH_TOKEN is not configured, paywall tools will return an access denied error with instructions on how to enable them.

## Available Tools (31)

### Health & Status
| Tool | Description |
|------|-------------|
| `health_check` | Server health and Azure SDK status |

### Subscription & Authentication
| Tool | Description |
|------|-------------|
| `list_subscriptions` | List accessible subscriptions |
| `set_subscription` | Set active subscription for session |
| `auth_status` | Current authentication method |
| `list_locations` | Available Azure regions |
| `list_tenants` | Azure AD tenants |

### Management Groups
| Tool | Description |
|------|-------------|
| `list_management_groups` | List all management groups |
| `get_management_group` | Details and child resources |
| `create_management_group` | Create new management group |
| `delete_management_group` | Delete (must be empty) |

### RBAC
| Tool | Description |
|------|-------------|
| `list_role_assignments` | Role assignments for scope (paywall) |
| `list_role_definitions` | Available built-in roles |

### Resource Locks
| Tool | Description |
|------|-------------|
| `list_resource_locks` | List locks on resources |
| `create_resource_lock` | Create CanNotDelete/ReadOnly lock (paywall) |
| `delete_resource_lock` | Remove a lock (paywall) |

### Tags
| Tool | Description |
|------|-------------|
| `list_tags` | Tags in subscription/resource group |
| `set_resource_group_tags` | Set tags (paywall) |

### Activity Log
| Tool | Description |
|------|-------------|
| `get_activity_log` | Recent audit log (1-7 days) |

### Resource Groups
| Tool | Description |
|------|-------------|
| `list_resource_groups` | All resource groups |
| `create_resource_group` | Create new resource group (paywall) |
| `delete_resource_group` | Delete with ALL resources ⚠️ (paywall) |

### Virtual Machines
| Tool | Description |
|------|-------------|
| `list_vms` | VMs in a resource group |
| `get_vm_status` | Power state and details |
| `start_vm` | Start a VM |
| `stop_vm` | Stop (stays allocated, charges continue) |
| `restart_vm` | Restart a VM |
| `deallocate_vm` | Deallocate (no compute charges) |
| `scale_vmss` | Scale VM Scale Set capacity |

### Storage Accounts
| Tool | Description |
|------|-------------|
| `list_storage_accounts` | Storage accounts in resource group |
| `get_storage_status` | Account status and endpoints |

## Usage Examples

### List and manage subscriptions
```
User: What subscriptions do I have access to?
User: Switch to subscription "Production"
```

### Work with resource groups
```
User: List all resource groups
User: Create a resource group called "dev-resources" in eastus
User: Tag the production resource group with environment=prod,team=platform
```

### Manage VMs
```
User: What VMs are in the web-servers resource group?
User: Start the VM "api-server-01" in production-rg
User: Deallocate all VMs in dev-rg to save costs
```

### Governance
```
User: Show me the management group hierarchy
User: Who has access to the production resource group?
User: Lock the production-db resource group to prevent deletion
User: Show activity log for the last 3 days
```

## Configuration

Environment variables (`.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR |
| `AZURE_SUBSCRIPTION_ID` | - | Default subscription |
| `AZURE_DEFAULT_LOCATION` | `eastus` | Default region for new resources |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Max requests/minute |
| `AUTH_TOKEN` | - | Paywall authentication token (min 8 chars) |

See `.env.example` for complete configuration examples.

## Project Structure

```
azops-mcp/
├── src/azops_mcp/
│   ├── __main__.py        # Module entry point
│   ├── server.py          # MCP server & tool definitions
│   ├── config.py          # Configuration management
│   └── tools/
│       └── cloud.py       # Azure SDK integrations
├── tests/                 # Unit tests
├── quickstart.sh          # Setup script
├── pyproject.toml         # Dependencies & metadata
└── .env.example           # Configuration template
```

## Development

### Run Tests
```bash
uv pip install -e ".[dev]"
pytest
pytest --cov=azops_mcp --cov-report=html
```

### Code Quality
```bash
black src/ tests/      # Format
ruff check src/ tests/ # Lint
mypy src/              # Type check
```

### Run Server Manually
```bash
uv run python -m azops_mcp
```

## Troubleshooting

### "Module not found" errors
```bash
# Reinstall dependencies
uv pip install -e . --reinstall
```

### "Subscription not configured"
```bash
# Option 1: Set in .env
echo "AZURE_SUBSCRIPTION_ID=$(az account show --query id -o tsv)" >> .env

# Option 2: Use set_subscription tool in chat
```

### "Authentication failed"
```bash
# Re-authenticate with Azure CLI
az login

# Check auth status in chat
User: What's my auth status?
```

### SDK not found
```bash
# Run quickstart.sh and select option 3 to install Azure SDKs
./quickstart.sh
```

## Azure SDK Dependencies

| Package | Purpose |
|---------|---------|
| `azure-identity` | Authentication |
| `azure-mgmt-subscription` | Subscriptions, tenants |
| `azure-mgmt-resource` | Resource groups, locks, tags |
| `azure-mgmt-compute` | VMs, VMSS |
| `azure-mgmt-storage` | Storage accounts |
| `azure-mgmt-managementgroups` | Management groups |
| `azure-mgmt-authorization` | RBAC |
| `azure-mgmt-monitor` | Activity logs |

## License

MIT
