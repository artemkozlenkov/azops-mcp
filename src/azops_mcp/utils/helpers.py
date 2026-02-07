"""Helper functions for API requests, error handling, and configuration."""

import logging
import os
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


async def make_api_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0,
) -> Optional[Dict[str, Any]]:
    """Make an HTTP request with proper error handling.
    
    Args:
        url: The URL to request
        method: HTTP method (GET, POST, etc.)
        headers: Optional headers dictionary
        json_data: Optional JSON data for POST/PUT requests
        timeout: Request timeout in seconds
        
    Returns:
        Response JSON as dictionary, or None on error
    """
    default_headers = {"User-Agent": "azops-mcp/1.0", "Accept": "application/json"}
    if headers:
        default_headers.update(headers)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=default_headers,
                json=json_data,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error making request to {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error making request to {url}: {e}")
        return None


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        
    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


def format_error_message(error: Exception, context: str = "") -> str:
    """Format an error message for user-friendly display.
    
    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred
        
    Returns:
        Formatted error message
    """
    error_msg = str(error)
    if context:
        return f"{context}: {error_msg}"
    return f"Error: {error_msg}"
