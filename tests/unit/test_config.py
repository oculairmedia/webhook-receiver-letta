"""
Unit tests for webhook_server.config module.

Tests configuration loading, environment variable handling,
and API URL construction.
"""

import pytest
import os
from unittest.mock import patch

from webhook_server.config import (
    get_api_url,
    get_graphiti_config,
    LETTA_BASE_URL,
    GRAPHITI_API_URL,
    GRAPHITI_MAX_NODES,
    GRAPHITI_MAX_FACTS,
    MAX_CONTEXT_SNIPPET_LENGTH
)


class TestGetApiUrl:
    """Tests for get_api_url function."""

    def test_get_api_url_with_leading_slash(self):
        """Test URL construction with leading slash in path."""
        url = get_api_url("/agents")
        assert url.endswith("/v1/agents")
        assert "//" not in url.replace("https://", "").replace("http://", "")

    def test_get_api_url_without_leading_slash(self):
        """Test URL construction without leading slash in path."""
        url = get_api_url("agents")
        assert url.endswith("/v1/agents")

    def test_get_api_url_with_trailing_slash_base(self):
        """Test URL construction handles trailing slash in base URL."""
        with patch.dict(os.environ, {"LETTA_BASE_URL": "http://test.com/"}):
            from importlib import reload
            from webhook_server import config
            reload(config)
            url = config.get_api_url("agents")
            # Should not have double slashes
            assert "//" not in url.replace("http://", "")

    def test_get_api_url_nested_path(self):
        """Test URL construction with nested path."""
        url = get_api_url("/agents/123/memory")
        assert url.endswith("/v1/agents/123/memory")

    def test_get_api_url_with_query_params(self):
        """Test URL construction preserves query parameters."""
        url = get_api_url("/blocks?label=test")
        assert "label=test" in url


class TestGraphitiConfig:
    """Tests for Graphiti configuration."""

    def test_get_graphiti_config_returns_dict(self):
        """Test get_graphiti_config returns a dictionary."""
        config = get_graphiti_config()
        assert isinstance(config, dict)

    def test_get_graphiti_config_has_required_keys(self):
        """Test config has all required keys."""
        config = get_graphiti_config()
        assert "api_url" in config
        assert "max_nodes" in config
        assert "max_facts" in config

    def test_get_graphiti_config_correct_types(self):
        """Test config values are correct types."""
        config = get_graphiti_config()
        assert isinstance(config["api_url"], str)
        assert isinstance(config["max_nodes"], int)
        assert isinstance(config["max_facts"], int)

    def test_graphiti_max_nodes_from_env(self):
        """Test GRAPHITI_MAX_NODES loaded from environment."""
        with patch.dict(os.environ, {"GRAPHITI_MAX_NODES": "15"}):
            from importlib import reload
            from webhook_server import config
            reload(config)
            assert config.GRAPHITI_MAX_NODES == 15

    def test_graphiti_max_facts_from_env(self):
        """Test GRAPHITI_MAX_FACTS loaded from environment."""
        with patch.dict(os.environ, {"GRAPHITI_MAX_FACTS": "25"}):
            from importlib import reload
            from webhook_server import config
            reload(config)
            assert config.GRAPHITI_MAX_FACTS == 25


class TestEnvironmentVariables:
    """Tests for environment variable loading."""

    def test_letta_base_url_default(self):
        """Test LETTA_BASE_URL has a default value."""
        assert LETTA_BASE_URL is not None
        assert isinstance(LETTA_BASE_URL, str)
        assert len(LETTA_BASE_URL) > 0

    def test_graphiti_api_url_default(self):
        """Test GRAPHITI_API_URL has a default value."""
        assert GRAPHITI_API_URL is not None
        assert isinstance(GRAPHITI_API_URL, str)
        assert len(GRAPHITI_API_URL) > 0

    def test_max_context_snippet_length_is_positive(self):
        """Test MAX_CONTEXT_SNIPPET_LENGTH is a positive integer."""
        assert isinstance(MAX_CONTEXT_SNIPPET_LENGTH, int)
        assert MAX_CONTEXT_SNIPPET_LENGTH > 0

    def test_graphiti_max_nodes_default(self):
        """Test GRAPHITI_MAX_NODES has a sensible default."""
        assert isinstance(GRAPHITI_MAX_NODES, int)
        assert GRAPHITI_MAX_NODES > 0

    def test_graphiti_max_facts_default(self):
        """Test GRAPHITI_MAX_FACTS has a sensible default."""
        assert isinstance(GRAPHITI_MAX_FACTS, int)
        assert GRAPHITI_MAX_FACTS > 0

    @patch.dict(os.environ, {"LETTA_BASE_URL": "http://custom.letta.com"})
    def test_custom_letta_base_url(self):
        """Test custom LETTA_BASE_URL from environment."""
        from importlib import reload
        from webhook_server import config
        reload(config)
        assert "custom.letta.com" in config.LETTA_BASE_URL

    @patch.dict(os.environ, {"GRAPHITI_URL": "http://custom.graphiti.com:9000"})
    def test_custom_graphiti_url(self):
        """Test custom GRAPHITI_URL from environment."""
        from importlib import reload
        from webhook_server import config
        reload(config)
        assert "custom.graphiti.com" in config.GRAPHITI_API_URL


class TestLettaApiHeaders:
    """Tests for Letta API headers configuration."""

    def test_letta_api_headers_exist(self):
        """Test LETTA_API_HEADERS is defined."""
        from webhook_server.config import LETTA_API_HEADERS
        assert LETTA_API_HEADERS is not None
        assert isinstance(LETTA_API_HEADERS, dict)

    def test_letta_api_headers_content_type(self):
        """Test Content-Type header is set."""
        from webhook_server.config import LETTA_API_HEADERS
        assert "Content-Type" in LETTA_API_HEADERS
        assert LETTA_API_HEADERS["Content-Type"] == "application/json"

    def test_letta_api_headers_accept(self):
        """Test Accept header is set."""
        from webhook_server.config import LETTA_API_HEADERS
        assert "Accept" in LETTA_API_HEADERS
        assert LETTA_API_HEADERS["Accept"] == "application/json"

    def test_letta_api_headers_authentication(self):
        """Test authentication headers are present."""
        from webhook_server.config import LETTA_API_HEADERS
        # Should have either X-BARE-PASSWORD or Authorization
        assert "X-BARE-PASSWORD" in LETTA_API_HEADERS or "Authorization" in LETTA_API_HEADERS
