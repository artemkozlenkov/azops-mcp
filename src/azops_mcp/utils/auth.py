"""License validation for premium feature gating.

On server startup the AUTH_TOKEN is validated against a remote license API.
The result is cached for the lifetime of the process (configurable TTL).
Premium MCP tools are only registered when the license grants the
corresponding feature flag.

Feature flags returned by the license server:
    rg_write    - create/delete resource groups
    rbac        - list role assignments
    locks_write - create/delete resource locks
    tags_write  - set resource group tags
    mg_write    - create/delete management groups
"""

import logging
import time
from typing import Optional

import httpx

from ..config import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_license_cache: Optional[dict] = None
_license_cache_time: float = 0

FREE_TIER: dict = {"valid": False, "tier": "free", "features": []}


def invalidate_cache() -> None:
    """Clear the cached license result (useful for testing)."""
    global _license_cache, _license_cache_time
    _license_cache = None
    _license_cache_time = 0


# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------


def validate_license() -> dict:
    """Validate AUTH_TOKEN and return license info.

    Calls the remote license API on first invocation, then caches the
    result for ``config.license_cache_ttl`` seconds.

    Returns:
        dict with keys ``valid`` (bool), ``tier`` (str), ``features`` (list[str]).
    """
    global _license_cache, _license_cache_time

    # Return cached result if still fresh
    if _license_cache is not None:
        elapsed = time.monotonic() - _license_cache_time
        if elapsed < config.license_cache_ttl:
            return _license_cache

    # No token → free tier, skip network call
    if not config.auth_token:
        _license_cache = FREE_TIER
        _license_cache_time = time.monotonic()
        logger.info("No AUTH_TOKEN configured — running in free tier")
        return _license_cache

    # No license API URL → warn and refuse to grant premium
    if not config.license_api_url:
        logger.warning(
            "AUTH_TOKEN is set but LICENSE_API_URL is not configured. "
            "Cannot validate license — running in free tier."
        )
        _license_cache = FREE_TIER
        _license_cache_time = time.monotonic()
        return _license_cache

    # Remote validation
    api_url = config.license_api_url.rstrip("/")
    try:
        logger.info("Validating license against %s …", api_url)
        resp = httpx.post(
            f"{api_url}/v1/license/validate",
            json={"token": config.auth_token},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()

        _license_cache = {
            "valid": data.get("valid", False),
            "tier": data.get("tier", "free"),
            "features": data.get("features", []),
        }

        if _license_cache["valid"]:
            logger.info(
                "License valid — tier=%s, features=%s",
                _license_cache["tier"],
                _license_cache["features"],
            )
        else:
            logger.warning("License rejected: %s", data.get("message", "unknown reason"))

    except httpx.HTTPStatusError as e:
        logger.error("License API returned HTTP %s: %s", e.response.status_code, e.response.text)
        _license_cache = FREE_TIER
    except httpx.ConnectError:
        logger.error("Cannot reach license server at %s", api_url)
        _license_cache = FREE_TIER
    except Exception as e:
        logger.error("License validation failed: %s", e)
        _license_cache = FREE_TIER

    _license_cache_time = time.monotonic()
    return _license_cache


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------


def get_licensed_features() -> set[str]:
    """Return the set of feature flags granted by the current license."""
    result = validate_license()
    if result.get("valid"):
        return set(result.get("features", []))
    return set()


def has_feature(feature: str) -> bool:
    """Check whether a specific feature flag is licensed."""
    return feature in get_licensed_features()


def is_premium_licensed() -> bool:
    """Return True if any premium license is active."""
    return validate_license().get("valid", False)
