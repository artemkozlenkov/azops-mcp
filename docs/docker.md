---
title: Docker
layout: default
nav_order: 7
---

# Docker
{: .no_toc }

Run azops-mcp and the license server with Docker Compose.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

The project includes a `docker-compose.yml` that orchestrates two services:

| Service | Type | Port | Description |
|:--------|:-----|:-----|:------------|
| `license-server` | Long-running daemon | `8000` | FastAPI license validation API |
| `mcp-server` | Interactive (stdio) | — | The MCP server, run on demand |

There is also a `generate-license` one-shot service for creating license keys.

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

# 3. Generate a license key
docker compose run --rm generate-license --tier pro --customer my-name

# 4. Add the hash output to license-server/licenses.json

# 5. Add the API key to .env
echo "AUTH_TOKEN=azops_..." >> .env
echo "LICENSE_API_URL=http://license-server:8000" >> .env

# 6. Start the license server
docker compose up license-server

# 7. Run the MCP server interactively
docker compose run --rm mcp-server
```

---

## Services

### license-server

The license validation API. Runs as a standard daemon with a healthcheck.

```bash
# Start in foreground (see logs)
docker compose up license-server

# Start in background
docker compose up -d license-server

# Check health
curl http://localhost:8000/health

# Test license validation
curl -X POST http://localhost:8000/v1/license/validate \
  -H "Content-Type: application/json" \
  -d '{"token": "your-auth-token"}'
```

`licenses.json` is volume-mounted so you can edit it without rebuilding:

```yaml
volumes:
  - ./license-server/licenses.json:/app/licenses.json:ro
```

### mcp-server

The MCP server uses stdio transport, so it cannot run as a background daemon. It is placed in the `cli` profile and must be started with `docker compose run`:

```bash
docker compose run --rm mcp-server
```

This:
- Waits for `license-server` to be healthy (via `depends_on`)
- Connects to `http://license-server:8000` for license validation (Docker networking)
- Reads `AUTH_TOKEN` and Azure credentials from `.env`
- Runs interactively with stdin/stdout attached

{: .note }
`docker compose up` does **not** start the MCP server. The `cli` profile is excluded from the default `up` target. Use `docker compose run` instead.

### generate-license

A one-shot utility to create new license keys:

```bash
# Pro license, 365 days
docker compose run --rm generate-license --tier pro --customer acme-corp

# Starter license, 30 days
docker compose run --rm generate-license --tier starter --customer trial-user --days 30
```

Available tiers:

| Tier | Features |
|:-----|:---------|
| `pro` | `rg_write`, `rbac`, `locks_write`, `tags_write`, `mg_write` |
| `team` | `rg_write`, `rbac`, `locks_write`, `tags_write`, `mg_write` |
| `starter` | `rg_write`, `tags_write` |

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
# Build both images
docker compose build

# Build individually
docker compose build license-server
docker compose build mcp-server
```

The MCP server image uses `uv` for fast dependency installation. The license server image is a minimal Python + FastAPI setup.

---

## Environment Variables in Docker

The `mcp-server` service loads your `.env` file via the `env_file` directive. It also sets:

| Variable | Value | Source |
|:---------|:------|:-------|
| `LICENSE_API_URL` | `http://license-server:8000` | Set in `docker-compose.yml` (Docker internal DNS) |
| `LICENSE_CACHE_TTL` | `3600` | Set in `docker-compose.yml` |
| `AUTH_TOKEN` | Your key | From `.env` |
| `AZURE_*` | Your credentials | From `.env` |

{: .warning }
When running in Docker, `LICENSE_API_URL` should use the Docker service name (`http://license-server:8000`), not `localhost`. The compose file sets this automatically.

---

## Troubleshooting

### "Cannot reach license server"

Make sure `license-server` is running and healthy:

```bash
docker compose ps
docker compose logs license-server
curl http://localhost:8000/health
```

### "No premium tools registered"

Check that:
1. `AUTH_TOKEN` is set in `.env`
2. The token hash exists in `license-server/licenses.json`
3. The license has not expired
4. `LICENSE_API_URL` is set (the compose file sets it to `http://license-server:8000` automatically)

### MCP server exits immediately

The MCP server expects stdio input. If run without an MCP client attached, it will exit. Use `docker compose run` (not `docker compose up`) and connect an AI client.
