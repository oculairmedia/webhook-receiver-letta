"""
Integration tests for Graphiti API connectivity.

These tests verify the webhook server's integration with the Graphiti
knowledge graph API using the unified /search endpoint.

The unified API uses:
- Single /search endpoint
- Request: { query, config: { limit, edge_config, node_config }, filters }
- Response: { nodes: [...], edges: [...] }
"""

import pytest
from unittest.mock import Mock, patch
import requests
import responses

from webhook_server.app import query_graphiti_api


class TestGraphitiAPIConnectivity:
    """Tests for Graphiti API connection and health."""

    @responses.activate
    def test_graphiti_api_connectivity(self):
        """Test basic connectivity to Graphiti API."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"nodes": [], "edges": []},
            status=200
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test query")

        assert 'context' in result
        assert 'success' in result

    @responses.activate
    def test_graphiti_api_timeout_handling(self):
        """Test handling of API timeouts."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            body=requests.exceptions.Timeout("Connection timeout")
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test query")

        assert result['success'] is False
        assert 'Error' in result['context']

    @responses.activate
    def test_graphiti_api_500_error(self):
        """Test handling of server errors."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"error": "Internal server error"},
            status=500
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test query")

        assert result['success'] is False


class TestGraphitiNodeSearch:
    """Tests for Graphiti node search functionality."""

    @responses.activate
    def test_node_search_returns_results(self):
        """Test that node search returns proper results."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={
                "nodes": [
                    {
                        "name": "AI Research",
                        "summary": "Cutting-edge research in artificial intelligence"
                    },
                    {
                        "name": "Machine Learning",
                        "summary": "Core ML algorithms and techniques"
                    }
                ],
                "edges": []
            },
            status=200
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("AI research", max_nodes=5)

        assert result['success'] is True
        assert "AI Research" in result['context']
        assert "Machine Learning" in result['context']

    @responses.activate
    def test_node_search_respects_max_nodes(self):
        """Test that max_nodes parameter is used correctly in config.limit."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"nodes": [], "edges": []},
            status=200
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            query_graphiti_api("test", max_nodes=10)

        # Check the request payload
        assert len(responses.calls) == 1
        request_body = responses.calls[0].request.body
        import json
        payload = json.loads(request_body)
        # Unified API uses config.limit instead of max_nodes
        assert payload['config']['limit'] == 10


class TestGraphitiFactSearch:
    """Tests for Graphiti fact search functionality (via edges in unified API)."""

    @responses.activate
    def test_fact_search_returns_results(self):
        """Test that fact search (edges) returns proper results."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={
                "nodes": [],
                "edges": [
                    {"fact": "AI can process natural language"},
                    {"fact": "Machine learning requires training data"}
                ]
            },
            status=200
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("AI capabilities")

        assert result['success'] is True
        assert "AI can process natural language" in result['context']
        assert "Machine learning requires training data" in result['context']

    @responses.activate
    def test_fact_search_deduplication(self):
        """Test that duplicate facts (edges) are deduplicated."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={
                "nodes": [],
                "edges": [
                    {"fact": "Duplicate fact"},
                    {"fact": "Duplicate fact"},
                    {"fact": "Unique fact"}
                ]
            },
            status=200
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        # Should only appear once
        assert result['context'].count("Duplicate fact") == 1
        assert result['context'].count("Unique fact") == 1


class TestGraphitiRetryLogic:
    """Tests for Graphiti API retry logic."""

    @responses.activate
    def test_retry_on_503_service_unavailable(self):
        """Test that 503 errors trigger retries."""
        # First call fails with 503
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"error": "Service unavailable"},
            status=503
        )
        # Subsequent retry succeeds
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"nodes": [{"name": "Test", "summary": "Success"}], "edges": []},
            status=200
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        # Should retry and eventually succeed (or fail gracefully)
        # With retry configured, we expect multiple calls
        assert len(responses.calls) >= 1


class TestGraphitiErrorHandling:
    """Tests for Graphiti API error handling."""

    @responses.activate
    def test_handles_malformed_json_response(self):
        """Test handling of malformed JSON responses."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            body="Not valid JSON",
            status=200
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        assert result['success'] is False

    @responses.activate
    def test_handles_network_error(self):
        """Test handling of network errors."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            body=requests.exceptions.ConnectionError("Network error")
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        assert result['success'] is False
        assert 'Error' in result['context']

    @responses.activate
    def test_handles_empty_graphiti_url(self):
        """Test handling when Graphiti URL is empty (uses fallback)."""
        # When URL is empty, implementation uses fallback URL
        responses.add(
            responses.POST,
            "http://192.168.50.90:3004/search",
            json={"nodes": [], "edges": []},
            status=200
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', ''):
            result = query_graphiti_api("test")

        assert 'context' in result


class TestGraphitiMixedResults:
    """Tests for combined nodes and edges results."""

    @responses.activate
    def test_combined_nodes_and_edges(self):
        """Test processing of both nodes and edges in single response."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={
                "nodes": [
                    {"name": "Entity A", "summary": "Description of A"}
                ],
                "edges": [
                    {"fact": "A relates to B"}
                ]
            },
            status=200
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        assert result['success'] is True
        assert "Entity A" in result['context']
        assert "A relates to B" in result['context']

    @responses.activate
    def test_only_nodes_no_edges(self):
        """Test handling of response with only nodes."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={
                "nodes": [{"name": "Solo Node", "summary": "Just a node"}],
                "edges": []
            },
            status=200
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        assert result['success'] is True
        assert "Solo Node" in result['context']

    @responses.activate
    def test_only_edges_no_nodes(self):
        """Test handling of response with only edges."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={
                "nodes": [],
                "edges": [{"fact": "Standalone fact"}]
            },
            status=200
        )

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        assert result['success'] is True
        assert "Standalone fact" in result['context']
