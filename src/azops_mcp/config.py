"""Centralized configuration for the infrastructure MCP server."""

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class ServerConfig:
    """Configuration settings for the MCP server."""

    # Logging configuration
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    log_format: str = field(
        default_factory=lambda: os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # API configuration
    api_timeout: int = field(default_factory=lambda: int(os.getenv("API_TIMEOUT", "30")))
    api_retry_attempts: int = field(default_factory=lambda: int(os.getenv("API_RETRY_ATTEMPTS", "3")))
    api_retry_delay: float = field(default_factory=lambda: float(os.getenv("API_RETRY_DELAY", "1")))

    # Azure configuration
    azure_tenant_id: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_TENANT_ID"))
    azure_client_id: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_CLIENT_ID"))
    azure_client_secret: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_CLIENT_SECRET"))
    azure_subscription_id: Optional[str] = field(default_factory=lambda: os.getenv("AZURE_SUBSCRIPTION_ID"))
    azure_default_location: str = field(default_factory=lambda: os.getenv("AZURE_DEFAULT_LOCATION", "eastus"))

    # Docker configuration
    docker_timeout: int = field(default_factory=lambda: int(os.getenv("DOCKER_TIMEOUT", "30")))

    # Monitoring configuration
    monitoring_interval: int = field(default_factory=lambda: int(os.getenv("MONITORING_INTERVAL", "60")))

    # Rate limiting configuration
    rate_limit_enabled: bool = field(default_factory=lambda: os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true")
    rate_limit_requests_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
    )
    rate_limit_burst_size: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_BURST_SIZE", "10")))

    # Security configuration
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", "default-secret-key-change-in-production"))
    allowed_hosts: str = field(default_factory=lambda: os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1"))

    # Debug mode
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # Paywall authentication
    auth_token: Optional[str] = field(default_factory=lambda: os.getenv("AUTH_TOKEN"))

    def get_log_level(self) -> int:
        """Get logging level as integer."""
        return getattr(logging, self.log_level, logging.INFO)

    def validate(self) -> list[str]:
        """Validate configuration and return list of validation errors."""
        errors = []

        # Validate log level
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"Invalid log_level: {self.log_level}")

        # Validate timeouts
        if self.api_timeout <= 0:
            errors.append(f"api_timeout must be positive: {self.api_timeout}")
        if self.docker_timeout <= 0:
            errors.append(f"docker_timeout must be positive: {self.docker_timeout}")
        if self.monitoring_interval <= 0:
            errors.append(f"monitoring_interval must be positive: {self.monitoring_interval}")

        # Validate rate limiting
        if self.rate_limit_requests_per_minute <= 0:
            errors.append(f"rate_limit_requests_per_minute must be positive: {self.rate_limit_requests_per_minute}")
        if self.rate_limit_burst_size <= 0:
            errors.append(f"rate_limit_burst_size must be positive: {self.rate_limit_burst_size}")

        # Validate Azure credentials
        # Service Principal requires all three: client_id, client_secret, tenant_id
        if self.azure_client_id or self.azure_client_secret or self.azure_tenant_id:
            # If any SP credential is set, all must be set
            if not (self.azure_client_id and self.azure_client_secret and self.azure_tenant_id):
                missing = []
                if not self.azure_client_id:
                    missing.append("AZURE_CLIENT_ID")
                if not self.azure_client_secret:
                    missing.append("AZURE_CLIENT_SECRET")
                if not self.azure_tenant_id:
                    missing.append("AZURE_TENANT_ID")
                errors.append(f"Incomplete Service Principal config. Missing: {', '.join(missing)}")

        # Validate paywall auth token
        if self.auth_token and len(self.auth_token) < 8:
            errors.append("AUTH_TOKEN must be at least 8 characters")

        # Subscription ID is always required
        if not self.azure_subscription_id:
            errors.append("AZURE_SUBSCRIPTION_ID is required. Get it with: az account show --query id -o tsv")

        return errors


# Global configuration instance
config = ServerConfig()


def reload_config() -> ServerConfig:
    """Reload configuration from environment variables."""
    global config
    config = ServerConfig()
    return config


def print_config() -> None:
    """Print current configuration (useful for debugging)."""
    print("Current Configuration:")
    print(f"  log_level: {config.log_level}")
    print(f"  api_timeout: {config.api_timeout}")
    print(f"  debug: {config.debug}")
    print(f"  rate_limit_enabled: {config.rate_limit_enabled}")
    print(f"  azure_tenant_id: {'***' if config.azure_tenant_id else 'Not set'}")
    print(f"  azure_subscription_id: {'***' if config.azure_subscription_id else 'Not set'}")
    print(f"  azure_default_location: {config.azure_default_location}")