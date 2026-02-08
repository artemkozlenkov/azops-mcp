# azops-mcp server
FROM python:3.12-slim AS base

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ src/

# Install the project and its dependencies
RUN uv pip install --system -e .

# MCP uses stdio transport — the container is spawned by the AI client
# and communicates over stdin/stdout.  Stderr is used for logging.
CMD ["python", "-m", "azops_mcp"]
