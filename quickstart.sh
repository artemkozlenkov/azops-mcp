#!/bin/bash

# Infrastructure MCP Server - Quick Start Script
# This script sets up and runs the Infrastructure MCP Server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${GREEN}Azure Infrastructure MCP Server - Quick Start${NC}"
echo "=============================================="
echo ""

# Check if uv is installed
echo -e "${YELLOW}Checking for uv...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv is not installed. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for current session
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    
    # Check if installation was successful
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Error: Failed to install uv. Please install manually from https://astral.sh/uv${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ uv installed successfully${NC}"
else
    echo -e "${GREEN}✓ uv found${NC}"
fi
echo ""

# Create virtual environment with Python 3.10+ (uv will download if needed)
echo -e "${YELLOW}Setting up virtual environment with Python 3.10+...${NC}"
if [ ! -d ".venv" ]; then
    uv venv --python 3.12
    echo -e "${GREEN}✓ Virtual environment created with Python 3.12${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Get Python version in venv
PYTHON_VERSION=$(.venv/bin/python --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✓ Using Python $PYTHON_VERSION${NC}"
echo ""

# Install dependencies using uv sync (preferred) or pip
echo -e "${YELLOW}Installing dependencies...${NC}"
uv pip install -e . --quiet
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created (edit it to add your API keys)${NC}"
    else
        echo -e "${YELLOW}⚠ .env.example not found, skipping .env creation${NC}"
    fi
    echo ""
fi

# Display configuration info
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Configuration:"
echo "  Project directory: $PROJECT_DIR"
echo "  Python version: $PYTHON_VERSION"
echo "  Virtual environment: $PROJECT_DIR/.venv"
echo ""

# Ask user what they want to do
echo "What would you like to do?"
echo "  1) Run the MCP server (for testing)"
echo "  2) Show Cursor configuration"
echo "  3) Install Azure SDK dependencies"
echo "  4) Exit"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo ""
        echo -e "${GREEN}Starting MCP server...${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
        echo ""
        uv run python -m azops_mcp
        ;;
    2)
        echo ""
        echo -e "${YELLOW}Cursor MCP Configuration:${NC}"
        echo ""
        echo "Add this to ~/.cursor/mcp.json:"
        echo ""
        cat << EOF
{
  "mcpServers": {
    "azops-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "$PROJECT_DIR",
        "run",
        "python",
        "-m",
        "azops_mcp"
      ]
    }
  }
}
EOF
        echo ""
        echo -e "${YELLOW}After adding the configuration, restart Cursor to use the MCP server.${NC}"
        ;;
    3)
        echo ""
        echo -e "${YELLOW}Installing Azure SDK dependencies...${NC}"
        echo ""
        uv pip install \
            azure-identity \
            azure-mgmt-compute \
            azure-mgmt-resource \
            azure-mgmt-storage \
            azure-mgmt-subscription \
            azure-mgmt-managementgroups \
            azure-mgmt-authorization \
            azure-mgmt-monitor
        echo ""
        echo -e "${GREEN}✓ Azure SDKs installed:${NC}"
        echo "  - azure-identity (authentication)"
        echo "  - azure-mgmt-subscription (subscriptions, tenants)"
        echo "  - azure-mgmt-managementgroups (management groups)"
        echo "  - azure-mgmt-authorization (RBAC)"
        echo "  - azure-mgmt-resource (resource groups, locks, tags)"
        echo "  - azure-mgmt-compute (VMs, VMSS)"
        echo "  - azure-mgmt-storage (storage accounts)"
        echo "  - azure-mgmt-monitor (activity logs)"
        echo ""
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
