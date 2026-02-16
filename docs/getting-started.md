---
title: Getting Started
layout: default
nav_order: 2
---

# Getting Started
{: .no_toc }

Get azops-mcp running in under five minutes.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Prerequisites

| Requirement | Version | Check |
|:------------|:--------|:------|
| Python | 3.10+ | `python3 --version` |
| Azure CLI | any | `az version` |
| uv *(recommended)* | any | `uv --version` |

You need to be authenticated with Azure CLI (`az login`) **or** have Service Principal credentials ready.

For Docker-based usage you also need Docker (or Podman) with Compose v2.

---

## Installation

### Option A: Install from PyPI (recommended)
{: .d-inline-block }

New
{: .label .label-green }

The fastest way — no clone needed. Install the package globally or in an isolated environment:

```bash
# With pip
pip install azops-mcp

# Or with uv
uv pip install azops-mcp
```

After installing, the `azops-mcp` command is available on your `PATH`. You can verify with:

```bash
azops-mcp --help
```

{: .note }
> If you only need the server for an AI client (Claude Desktop, Cursor), you don't even need to install it — use **uvx** to run it on-the-fly. See [Connect to Your AI Client](#connect-to-your-ai-client) below.

### Option B: Run with uvx (zero-install)

[uvx](https://docs.astral.sh/uv/guides/tools/) runs Python packages in temporary, isolated environments — nothing is installed permanently:

```bash
uvx azops-mcp
```

This downloads `azops-mcp` and all its dependencies into a cached environment and starts the server. Perfect for one-off use or when configuring an AI client.

### Option C: Quick Start Script

```bash
git clone https://github.com/artemkozlenkov/azops-mcp.git
cd azops-mcp
./quickstart.sh
```

The script creates a `.venv`, installs all dependencies (including Azure SDKs), and walks you through configuration.

### Option D: Manual Install from Source

```bash
git clone https://github.com/artemkozlenkov/azops-mcp.git
cd azops-mcp
uv venv --python 3.12
uv pip install -e .
cp .env.example .env
```

Edit `.env` to set at least `AZURE_SUBSCRIPTION_ID`, or leave it blank and use the `set_subscription` tool in chat.

### Option E: Docker

If you prefer containers, see the [Docker](/azops-mcp/docker) page for full instructions. The short version:

```bash
git clone https://github.com/artemkozlenkov/azops-mcp.git
cd azops-mcp
cp .env.example .env          # edit with your credentials
docker compose build
docker compose run --rm mcp-server
```

---

## Connect to Your AI Client

### Claude Desktop

Open `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows).

**Using uvx (recommended — no install required):**

{: .important }
> **You must use the full absolute path to `uvx`.** Claude Desktop does not inherit your shell's `PATH`, so commands like `uvx` or `azops-mcp` that live in `~/.local/bin` will not be found. Find the path with `which uvx` and use that in the config.

```json
{
  "mcpServers": {
    "azops-mcp": {
      "command": "/Users/YOUR_USERNAME/.local/bin/uvx",
      "args": ["azops-mcp"]
    }
  }
}
```

Find your path:

```bash
which uvx
# Example output: /Users/yourname/.local/bin/uvx
```

**Using a pip-installed package:**

If you already ran `pip install azops-mcp`, use the full path to the binary:

```bash
which azops-mcp
# Example output: /Users/yourname/.local/bin/azops-mcp
```

```json
{
  "mcpServers": {
    "azops-mcp": {
      "command": "/Users/YOUR_USERNAME/.local/bin/azops-mcp"
    }
  }
}
```

**Using a local clone (development):**

```json
{
  "mcpServers": {
    "azops-mcp": {
      "command": "/Users/YOUR_USERNAME/.local/bin/uv",
      "args": [
        "--directory", "/full/path/to/azops-mcp",
        "run", "python", "-m", "azops_mcp"
      ]
    }
  }
}
```

{: .note }
> **Environment variables** — To pass Azure credentials or other config to the server, add an `"env"` key alongside `"command"`:
> ```json
> {
>   "mcpServers": {
>     "azops-mcp": {
>       "command": "/Users/YOUR_USERNAME/.local/bin/uvx",
>       "args": ["azops-mcp"],
>       "env": {
>         "AZURE_SUBSCRIPTION_ID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
>       }
>     }
>   }
> }
> ```

{: .warning }
> **Troubleshooting: "Failed to spawn process: No such file or directory"**
>
> This error in `~/Library/Logs/Claude/mcp-server-azops-mcp.log` means Claude Desktop cannot find the `uvx` binary. Claude Desktop only searches system paths (`/usr/local/bin`, `/opt/homebrew/bin`, `/usr/bin`, `/bin`) and does **not** include `~/.local/bin` or other directories added by your shell profile.
>
> **Fix:** Replace `"command": "uvx"` with the full path from `which uvx`.

### Cursor

Add to `~/.cursor/mcp.json`:

{: .note }
> Cursor inherits your shell's `PATH`, so short command names like `uvx` usually work. If you run into issues, use the full path as described in the Claude Desktop section above.

**Using uvx (recommended):**

```json
{
  "mcpServers": {
    "azops-mcp": {
      "command": "uvx",
      "args": ["azops-mcp"]
    }
  }
}
```

**Using a local clone:**

```json
{
  "mcpServers": {
    "azops-mcp": {
      "command": "uv",
      "args": [
        "--directory", "/full/path/to/azops-mcp",
        "run", "python", "-m", "azops_mcp"
      ]
    }
  }
}
```

Restart your AI client after saving the configuration.

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "azops-mcp": {
      "command": "uvx",
      "args": ["azops-mcp"]
    }
  }
}
```

{: .note }
> Windsurf inherits your shell's `PATH`. If `uvx` is not found, use the full path (e.g. `/Users/yourname/.local/bin/uvx`).

### VS Code (GitHub Copilot)

VS Code supports MCP servers via GitHub Copilot agent mode. Add to your **User** or **Workspace** settings (`.vscode/settings.json`):

```json
{
  "github.copilot.chat.mcpServers": {
    "azops-mcp": {
      "command": "uvx",
      "args": ["azops-mcp"]
    }
  }
}
```

Alternatively, create an `.vscode/mcp.json` file in your workspace root:

```json
{
  "servers": {
    "azops-mcp": {
      "command": "uvx",
      "args": ["azops-mcp"]
    }
  }
}
```

{: .note }
> VS Code inherits your terminal's `PATH`. If `uvx` isn't found, use the full absolute path.

### Zed

Add to your Zed settings (`~/.config/zed/settings.json` on Linux, `~/Library/Application Support/Zed/settings.json` on macOS):

```json
{
  "context_servers": {
    "azops-mcp": {
      "command": {
        "path": "uvx",
        "args": ["azops-mcp"]
      }
    }
  }
}
```

{: .note }
> If Zed cannot find `uvx`, replace `"path": "uvx"` with the full absolute path from `which uvx`.

### Continue (VS Code / JetBrains)

Add to your Continue config (`~/.continue/config.yaml`):

```yaml
mcpServers:
  - name: azops-mcp
    command: uvx
    args:
      - azops-mcp
```

### Any MCP-Compatible Client (generic stdio)

azops-mcp uses **stdio** transport. Any MCP client that can spawn a subprocess and communicate over stdin/stdout will work. The command is:

```bash
uvx azops-mcp
```

Or with a pip-installed package:

```bash
azops-mcp
```

The server speaks JSON-RPC over stdio, following the [Model Context Protocol](https://modelcontextprotocol.io/) specification. Pass environment variables for Azure credentials as needed.

{: .warning }
> **PATH issues with GUI applications:** Desktop apps (Claude Desktop, some Electron-based editors) often do **not** inherit your shell's `PATH`. If the client fails to start the server, use the full absolute path to `uvx` — find it with `which uvx` (typically `~/.local/bin/uvx`).

Restart your AI client after saving the configuration.

---

## First Commands

Once connected, try these in the chat:

```
List my Azure subscriptions
```

```
Show all resource groups
```

```
What VMs are running in the "production" resource group?
```

```
Check my Azure auth status
```

The assistant calls the corresponding MCP tools and returns the results inline.

---

## Next Steps

- [Architecture](/azops-mcp/architecture) — understand how the server works internally
- [Authentication](/azops-mcp/authentication) — configure Service Principal or managed identity
- [Tools Reference](/azops-mcp/tools-reference) — full list of every available tool
- [Configuration](/azops-mcp/configuration) — all environment variables and defaults
- [Docker](/azops-mcp/docker) — run with Docker Compose
