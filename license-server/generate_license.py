#!/usr/bin/env python3
"""
Generate a license key and its hashed entry for the license server.

Usage:
    python generate_license.py                          # pro license, 365 days
    python generate_license.py --tier pro --customer acme --days 365
    python generate_license.py --tier team --customer beta-user --days 30

The script prints:
  - The API key to give to the customer (set as AUTH_TOKEN in .env)
  - The hashed entry to add to licenses.json
"""

import argparse
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone

# Feature sets per tier
TIER_FEATURES = {
    "pro": ["rg_write", "rbac", "locks_write", "tags_write", "mg_write"],
    "team": ["rg_write", "rbac", "locks_write", "tags_write", "mg_write"],
    "starter": ["rg_write", "tags_write"],
}


def generate_license(
    tier: str = "pro",
    customer: str = "",
    days_valid: int = 365,
) -> tuple[str, str, dict]:
    """Generate a new license key and its storage entry.

    Returns:
        (api_key, token_hash, license_entry)
        - api_key: plaintext key given to the customer
        - token_hash: SHA-256 hash used as key in licenses.json
        - license_entry: dict stored as the value in licenses.json
    """
    api_key = f"azops_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(api_key.encode()).hexdigest()

    features = TIER_FEATURES.get(tier, TIER_FEATURES["pro"])
    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(days=days_valid)).strftime("%Y-%m-%dT%H:%M:%SZ")

    license_entry = {
        "customer": customer,
        "tier": tier,
        "features": features,
        "expires_at": expires_at,
        "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    return api_key, token_hash, license_entry


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an azops-mcp license key")
    parser.add_argument("--tier", default="pro", choices=TIER_FEATURES.keys(), help="License tier")
    parser.add_argument("--customer", default="", help="Customer name or identifier")
    parser.add_argument("--days", type=int, default=365, help="Days until expiration")
    args = parser.parse_args()

    api_key, token_hash, entry = generate_license(
        tier=args.tier,
        customer=args.customer,
        days_valid=args.days,
    )

    print(f"\n{'=' * 64}")
    print("  azops-mcp License Generated")
    print(f"{'=' * 64}")
    print(f"  API Key (give to customer):  {api_key}")
    print(f"  Token Hash (licenses.json):  {token_hash}")
    print(f"  Tier:                        {entry['tier']}")
    print(f"  Features:                    {', '.join(entry['features'])}")
    print(f"  Expires:                     {entry['expires_at']}")
    if args.customer:
        print(f"  Customer:                    {args.customer}")
    print(f"{'=' * 64}")

    print("\nAdd the following to licenses.json:")
    print(json.dumps({token_hash: entry}, indent=2))

    print("\nCustomer sets this in their .env:")
    print(f"  AUTH_TOKEN={api_key}")
    print()


if __name__ == "__main__":
    main()
