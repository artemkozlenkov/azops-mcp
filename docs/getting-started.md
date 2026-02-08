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
| uv | any | `uv --version` |

You need to be authenticated with Azure CLI (`az login`) **or** have Service Principal credentials ready.

---

## Installation

### Option A: Quick Start Script

```bash
git clone https://github.com/artemkozlenkov/azops-mcp.git
cd azops-mcp
./quickstart.sh
```

The script creates a `.venv`, installs all dependencies (including Azure SDKs), and walks you through configuration.

### Option B: Manual Install

```bash
git clone https://github.com/artemkozlenkov/azops-mcp.git
cd azops-mcp
uv venv --python 3.12
uv pip install -e .
cp .env.example .env
```

Edit `.env` to set at least `AZURE_SUBSCRIPTION_ID`, or leave it blank and use the `set_subscription` tool in chat.

---

## Connect to Your AI Client

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

### Cursor

Add to `~/.cursor/mcp.json`:

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
- [Authentication](/azops-mcp/authentication) — configure Service Principal or paywall tokens
- [Tools Reference](/azops-mcp/tools-reference) — full list of every available tool
- [Configuration](/azops-mcp/configuration) — all environment variables and defaults
