"""Unit tests for the configuration module."""

import os
from unittest.mock import patch

from azops_mcp.config import ServerConfig, reload_config


class TestServerConfig:
    """Tests for ServerConfig class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        test_config = ServerConfig()

        assert test_config.log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert test_config.api_timeout > 0
        assert test_config.api_retry_attempts > 0
        assert test_config.docker_timeout > 0
        assert test_config.monitoring_interval > 0

    def test_get_log_level(self):
        """Test get_log_level returns correct integer."""
        import logging

        test_config = ServerConfig()
        test_config.log_level = "INFO"
        assert test_config.get_log_level() == logging.INFO

        test_config.log_level = "DEBUG"
        assert test_config.get_log_level() == logging.DEBUG

        test_config.log_level = "ERROR"
        assert test_config.get_log_level() == logging.ERROR

    def test_validate_returns_empty_list_for_valid_config(self):
        """Test that validate returns empty list for valid config."""
        test_config = ServerConfig()
        test_config.azure_subscription_id = "00000000-0000-0000-0000-000000000000"
        errors = test_config.validate()
        assert len(errors) == 0

    def test_validate_catches_invalid_log_level(self):
        """Test that validate catches invalid log level."""
        test_config = ServerConfig()
        test_config.log_level = "INVALID"
        errors = test_config.validate()
        assert any("log_level" in error for error in errors)

    def test_validate_catches_negative_timeout(self):
        """Test that validate catches negative timeout."""
        test_config = ServerConfig()
        test_config.api_timeout = -1
        errors = test_config.validate()
        assert any("api_timeout" in error for error in errors)

    def test_validate_catches_zero_timeout(self):
        """Test that validate catches zero timeout."""
        test_config = ServerConfig()
        test_config.docker_timeout = 0
        errors = test_config.validate()
        assert any("docker_timeout" in error for error in errors)

    def test_validate_catches_incomplete_azure_credentials(self):
        """Test that validate catches incomplete Azure credentials."""
        test_config = ServerConfig()
        test_config.azure_client_id = "client-id"
        test_config.azure_client_secret = None
        errors = test_config.validate()
        assert any("AZURE" in error for error in errors)

    def test_validate_catches_missing_tenant_id(self):
        """Test that validate catches missing tenant ID."""
        test_config = ServerConfig()
        test_config.azure_client_id = "client-id"
        test_config.azure_client_secret = "secret"
        test_config.azure_tenant_id = None
        errors = test_config.validate()
        assert any("TENANT" in error for error in errors)

    def test_validate_catches_missing_subscription_id(self):
        """Test that validate catches missing subscription ID."""
        test_config = ServerConfig()
        test_config.azure_client_id = "client-id"
        test_config.azure_client_secret = "secret"
        test_config.azure_tenant_id = "tenant-id"
        test_config.azure_subscription_id = None
        errors = test_config.validate()
        assert any("SUBSCRIPTION" in error for error in errors)


class TestEnvironmentVariables:
    """Tests for environment variable loading."""

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_log_level_from_env(self):
        """Test that LOG_LEVEL is loaded from environment."""
        test_config = ServerConfig()
        assert test_config.log_level == "DEBUG"

    @patch.dict(os.environ, {"API_TIMEOUT": "60"})
    def test_api_timeout_from_env(self):
        """Test that API_TIMEOUT is loaded from environment."""
        test_config = ServerConfig()
        assert test_config.api_timeout == 60

    @patch.dict(os.environ, {"RATE_LIMIT_ENABLED": "false"})
    def test_rate_limit_enabled_from_env(self):
        """Test that RATE_LIMIT_ENABLED is loaded from environment."""
        test_config = ServerConfig()
        assert test_config.rate_limit_enabled is False

    @patch.dict(os.environ, {"DEBUG": "true"})
    def test_debug_from_env(self):
        """Test that DEBUG is loaded from environment."""
        test_config = ServerConfig()
        assert test_config.debug is True


class TestReloadConfig:
    """Tests for reload_config function."""

    def test_reload_config_returns_new_instance(self):
        """Test that reload_config returns a new ServerConfig instance."""
        new_config = reload_config()
        assert isinstance(new_config, ServerConfig)
