"""Authentication utilities for paywall feature access."""

import functools
from typing import Callable, Optional

from ..config import config


def is_paywall_enabled() -> bool:
    """Check if paywall authentication is enabled (AUTH_TOKEN is configured).

    Returns:
        True if AUTH_TOKEN is set, False otherwise.
    """
    return config.auth_token is not None and len(config.auth_token) > 0


def check_auth_token() -> tuple[bool, str]:
    """Check if AUTH_TOKEN is configured and valid.

    Returns:
        Tuple of (is_valid, error_message).
        is_valid is True if AUTH_TOKEN is configured.
        error_message is empty if valid, otherwise describes the issue.
    """
    if config.auth_token is None or len(config.auth_token) == 0:
        return False, "AUTH_TOKEN not configured. Please set AUTH_TOKEN in .env to use this feature."
    if len(config.auth_token) < 8:
        return False, "AUTH_TOKEN must be at least 8 characters."
    return True, ""


def require_auth_token(func: Callable) -> Callable:
    """Decorator to require AUTH_TOKEN for a tool.

    Usage:
        @require_auth_token
        async def my_paywall_tool(...) -> str:
            ...

    The decorated function will receive an additional first parameter:
    `auth_valid: bool` indicating if authentication is valid.

    Returns:
        Decorated function that checks auth before executing.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        is_valid, error_msg = check_auth_token()
        if not is_valid:
            return error_msg
        return await func(*args, **kwargs)

    return wrapper
