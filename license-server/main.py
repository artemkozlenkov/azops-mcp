"""
Minimal license validation API for azops-mcp.

This service validates AUTH_TOKENs and returns licensed features.
Deploy as a container, Azure Function, or any ASGI-compatible host.

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="azops-mcp License Server", version="1.0.0")


# =============================================================================
# Models
# =============================================================================


class ValidateRequest(BaseModel):
    token: str


class ValidateResponse(BaseModel):
    valid: bool
    tier: str
    features: list[str]
    expires_at: Optional[str] = None
    message: str = ""


# =============================================================================
# License Store
# =============================================================================
#
# In production, replace with a real database (PostgreSQL, Redis, etc.).
# Licenses are loaded from licenses.json or the LICENSES_JSON env var.
# Keys in the store are SHA-256 hashes of the actual API tokens — the
# plaintext token is never stored.
# =============================================================================

_licenses: dict = {}


def hash_token(token: str) -> str:
    """SHA-256 hash a token for secure storage comparison."""
    return hashlib.sha256(token.encode()).hexdigest()


def _load_licenses() -> None:
    """Load licenses from env var or JSON file."""
    global _licenses

    # 1. Try LICENSES_JSON env var (for containerized / serverless deploys)
    env_licenses = os.getenv("LICENSES_JSON")
    if env_licenses:
        try:
            _licenses = json.loads(env_licenses)
            logger.info("Loaded %d license(s) from LICENSES_JSON env var", len(_licenses))
            return
        except json.JSONDecodeError:
            logger.error("Invalid JSON in LICENSES_JSON env var")

    # 2. Fall back to licenses.json file next to this script
    licenses_path = Path(__file__).parent / "licenses.json"
    if licenses_path.exists():
        with open(licenses_path) as f:
            _licenses = json.load(f)
        logger.info("Loaded %d license(s) from %s", len(_licenses), licenses_path)
    else:
        logger.warning(
            "No licenses found. Create licenses.json or set LICENSES_JSON env var. "
            "Run 'python generate_license.py' to create a license."
        )


# =============================================================================
# Endpoints
# =============================================================================


@app.on_event("startup")
async def startup() -> None:
    _load_licenses()


@app.post("/v1/license/validate", response_model=ValidateResponse)
async def validate_license(req: ValidateRequest) -> ValidateResponse:
    """Validate an API token and return the licensed tier and features."""
    if not req.token or len(req.token) < 8:
        return ValidateResponse(
            valid=False,
            tier="free",
            features=[],
            message="Invalid token format.",
        )

    token_hash = hash_token(req.token)
    license_entry = _licenses.get(token_hash)

    if not license_entry:
        return ValidateResponse(
            valid=False,
            tier="free",
            features=[],
            message="Token not recognized.",
        )

    # Check expiration
    expires_at = license_entry.get("expires_at")
    if expires_at:
        try:
            expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expiry:
                return ValidateResponse(
                    valid=False,
                    tier="expired",
                    features=[],
                    expires_at=expires_at,
                    message="License has expired.",
                )
        except ValueError:
            logger.warning("Invalid expires_at format: %s", expires_at)

    return ValidateResponse(
        valid=True,
        tier=license_entry.get("tier", "pro"),
        features=license_entry.get("features", []),
        expires_at=expires_at,
        message="License valid.",
    )


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "licenses_loaded": len(_licenses)}
