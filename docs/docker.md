---
title: Docker
layout: default
nav_order: 7
---

# Docker
{: .no_toc }

Run azops-mcp with Docker Compose.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

The project includes a `docker-compose.yml` with the MCP server as a Docker service:

| Service | Type | Description |
|:--------|:-----|:------------|
| `mcp-server` | Interactive (stdio) | The MCP server, run on demand |

The MCP server uses stdio transport, so it cannot run as a long-lived daemon — it is spawned on demand with `docker compose run`.

---

## Prerequisites

- Docker (or Podman) with Compose v2
- A `.env` file in the project root (copy from `.env.example`)

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/artemkozlenkov/azops-mcp.git
cd azops-mcp

# 2. Create your .env
cp .env.example .env
# Edit .env with your Azure credentials

# 3. Build the image
docker compose build

# 4. Run the MCP server interactively
docker compose run --rm mcp-server
```

---

## Running the MCP Server

The MCP server uses stdio transport, so it must be started with `docker compose run`:

```bash
docker compose run --rm mcp-server
```

This:
- Reads Azure credentials from `.env`
- Runs interactively with stdin/stdout attached
- Removes the container when done (`--rm`)

{: .note }
`docker compose up` does **not** start the MCP server. The `cli` profile is excluded from the default `up` target. Use `docker compose run` instead.

---

## Connecting an AI Client to the Docker MCP Server

When running the MCP server in Docker, configure your AI client to use `docker compose run` as the command:

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "azops-mcp": {
      "command": "docker",
      "args": [
        "compose", "-f", "/full/path/to/azops-mcp/docker-compose.yml",
        "run", "--rm", "-T", "mcp-server"
      ]
    }
  }
}
```

The `-T` flag disables pseudo-TTY allocation, which is needed for stdio transport with some clients.

### Claude Desktop

```json
{
  "mcpServers": {
    "azops-mcp": {
      "command": "docker",
      "args": [
        "compose", "-f", "/full/path/to/azops-mcp/docker-compose.yml",
        "run", "--rm", "-T", "mcp-server"
      ]
    }
  }
}
```

---

## Building Images

```bash
# Build the image
docker compose build
```

The MCP server image uses `uv` for fast dependency installation.

---

## Environment Variables in Docker

The `mcp-server` service loads your `.env` file via the `env_file` directive:

| Variable | Source |
|:---------|:-------|
| `AZURE_SUBSCRIPTION_ID` | From `.env` |
| `AZURE_TENANT_ID` | From `.env` |
| `AZURE_CLIENT_ID` | From `.env` |
| `AZURE_CLIENT_SECRET` | From `.env` |
| `AZURE_DEFAULT_LOCATION` | From `.env` |
| `LOG_LEVEL` | From `.env` |

---

## Troubleshooting

### MCP server exits immediately

The MCP server expects stdio input. If run without an MCP client attached, it will exit. Use `docker compose run` (not `docker compose up`) and connect an AI client.

### Azure authentication errors

Make sure your `.env` file has valid Azure credentials:

```bash
# Check your credentials work locally first
az login
az account show
```

If using a Service Principal, verify all three variables are set: `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`.
