---
title: Configuration
layout: default
nav_order: 6
---

# Configuration
{: .no_toc }

All environment variables and how the server loads them.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

Configuration is managed by the `ServerConfig` dataclass in `config.py`. It reads environment variables at startup via `python-dotenv` (from a `.env` file) and `os.getenv()` with defaults.

A global singleton `config` is created at import time and used throughout the application.

---

## Environment Variables

### Azure Authentication

| Variable | Default | Description |
|:---------|:--------|:------------|
| `AZURE_SUBSCRIPTION_ID` | — | Default subscription ID. Can also be set via `set_subscription` tool at runtime. |
| `AZURE_TENANT_ID` | — | Azure AD tenant ID (for Service Principal auth) |
| `AZURE_CLIENT_ID` | — | Service Principal application/client ID |
| `AZURE_CLIENT_SECRET` | — | Service Principal secret |
| `AZURE_DEFAULT_LOCATION` | `eastus` | Default Azure region for new resources |

If `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_TENANT_ID` are **all** set, the server uses Service Principal authentication. Otherwise, it falls back to Azure CLI / Managed Identity.

### License / Premium Features

| Variable | Default | Description |
|:---------|:--------|:------------|
| `AUTH_TOKEN` | — | License key for premium features. Validated remotely against `LICENSE_API_URL`. |
| `LICENSE_API_URL` | — | URL of the license validation server (e.g. `http://localhost:8000`). Required for premium features. |
| `LICENSE_CACHE_TTL` | `3600` | How long (seconds) to cache the license validation result. |

Both `AUTH_TOKEN` and `LICENSE_API_URL` must be set for premium tools to be registered. If either is missing, the server runs in free tier.

The license is validated **once on startup** and cached for `LICENSE_CACHE_TTL` seconds. Restarting the MCP server triggers a fresh validation.

### Server Settings

| Variable | Default | Description |
|:---------|:--------|:------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `LOG_FORMAT` | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` | Python logging format string |
| `API_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `API_RETRY_ATTEMPTS` | `3` | Number of retry attempts for API calls |
| `API_RETRY_DELAY` | `1` | Delay between retries in seconds |
| `DEBUG` | `false` | Enable debug mode (verbose error messages) |

### Rate Limiting

| Variable | Default | Description |
|:---------|:--------|:------------|
| `RATE_LIMIT_ENABLED` | `true` | Enable/disable rate limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `60` | Maximum requests per minute per key |
| `RATE_LIMIT_BURST_SIZE` | `10` | Burst allowance above the per-minute rate |

### Docker & Monitoring

| Variable | Default | Description |
|:---------|:--------|:------------|
| `DOCKER_TIMEOUT` | `30` | Timeout for Docker CLI commands in seconds |
| `MONITORING_INTERVAL` | `60` | Default interval for monitoring checks in seconds |

### Security

| Variable | Default | Description |
|:---------|:--------|:------------|
| `SECRET_KEY` | `default-secret-key-change-in-production` | Application secret key |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hostnames |

---

## Validation

`ServerConfig.validate()` checks for common misconfigurations and returns a list of error strings:

| Check | Condition |
|:------|:----------|
| Log level | Must be one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| Timeouts | `api_timeout`, `docker_timeout`, `monitoring_interval` must be > 0 |
| Rate limits | `rate_limit_requests_per_minute`, `rate_limit_burst_size` must be > 0 |
| Service Principal | If **any** of `client_id` / `client_secret` / `tenant_id` is set, **all** must be set |
| AUTH_TOKEN | If set, must be >= 8 characters |
| Subscription | `AZURE_SUBSCRIPTION_ID` is required (warning) |

---

## Reloading Configuration

To pick up changed environment variables without restarting:

```python
from azops_mcp.config import reload_config

new_config = reload_config()
```

This creates a fresh `ServerConfig` instance and replaces the global `config` singleton.

{: .warning }
Reloading config does **not** re-validate the license or re-register premium tools. Restart the MCP server to pick up license changes.

---

## Example `.env` File

```env
# Minimal — uses az login credentials
AZURE_SUBSCRIPTION_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Optional: Service Principal
# AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# AZURE_CLIENT_SECRET=your-secret

# Defaults
AZURE_DEFAULT_LOCATION=eastus
LOG_LEVEL=INFO
API_TIMEOUT=30
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
DEBUG=false

# Premium features — uncomment to enable write operations
# AUTH_TOKEN=azops_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# LICENSE_API_URL=http://localhost:8000
# LICENSE_CACHE_TTL=3600
```
