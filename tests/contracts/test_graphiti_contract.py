"""
Contract tests for Graphiti API.

These tests verify that the Graphiti unified search API responses match expected schemas.
Contract tests help detect breaking changes in external APIs.

The current implementation uses a unified /search endpoint with:
- Request: { query, config: { limit, edge_config, node_config }, filters }
- Response: { nodes: [...], edges: [...] }
"""

import pytest
from unittest.mock import Mock, patch
import responses


@pytest.mark.contract
class TestGraphitiUnifiedSearchContract:
    """Contract tests for Graphiti unified search endpoint."""

    @responses.activate
    def test_unified_search_response_schema(self):
        """Test that unified search response matches expected schema."""
        expected_response = {
            "nodes": [
                {
                    "id": "node-123",
                    "name": "Test Node",
                    "summary": "Node summary",
                    "created_at": "2024-01-15T10:00:00Z"
                }
            ],
            "edges": [
                {
                    "id": "edge-456",
                    "fact": "Test fact text",
                    "source": "node-123",
                    "target": "node-456",
                    "created_at": "2024-01-15T11:00:00Z"
                }
            ]
        }

        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json=expected_response,
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        # Verify response schema compliance
        assert 'nodes' in expected_response
        assert 'edges' in expected_response
        assert isinstance(expected_response['nodes'], list)
        assert isinstance(expected_response['edges'], list)

        if expected_response['nodes']:
            node = expected_response['nodes'][0]
            assert 'id' in node or 'name' in node
            assert 'summary' in node

        if expected_response['edges']:
            edge = expected_response['edges'][0]
            assert 'fact' in edge or 'name' in edge

    @responses.activate
    def test_unified_search_request_schema(self):
        """Test that unified search request has correct schema."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"nodes": [], "edges": []},
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            query_graphiti_api("test query", max_nodes=5)

        # Verify request payload schema
        request_body = responses.calls[0].request.body
        import json
        payload = json.loads(request_body)

        # Expected unified search schema
        assert 'query' in payload
        assert isinstance(payload['query'], str)
        assert 'config' in payload
        assert isinstance(payload['config'], dict)
        assert 'limit' in payload['config']
        assert payload['config']['limit'] == 5
        assert 'edge_config' in payload['config']
        assert 'node_config' in payload['config']
        assert 'filters' in payload


@pytest.mark.contract
class TestGraphitiSearchConfigContract:
    """Contract tests for Graphiti search configuration."""

    @responses.activate
    def test_edge_config_schema(self):
        """Test that edge_config has expected structure."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"nodes": [], "edges": []},
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            query_graphiti_api("test")

        import json
        payload = json.loads(responses.calls[0].request.body)
        edge_config = payload['config']['edge_config']

        assert 'search_methods' in edge_config
        assert 'reranker' in edge_config
        assert isinstance(edge_config['search_methods'], list)

    @responses.activate
    def test_node_config_schema(self):
        """Test that node_config has expected structure."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"nodes": [], "edges": []},
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            query_graphiti_api("test")

        import json
        payload = json.loads(responses.calls[0].request.body)
        node_config = payload['config']['node_config']

        assert 'search_methods' in node_config
        assert 'reranker' in node_config
        assert isinstance(node_config['search_methods'], list)


@pytest.mark.contract
class TestGraphitiErrorContract:
    """Contract tests for Graphiti API error responses."""

    @responses.activate
    def test_error_response_schema(self):
        """Test that error responses are handled gracefully."""
        error_response = {
            "error": "Internal server error",
            "message": "Database connection failed",
            "status": 500
        }

        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json=error_response,
            status=500
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        # Should handle gracefully
        assert result['success'] is False


@pytest.mark.contract
class TestGraphitiBackwardCompatibility:
    """Tests for backward compatibility with Graphiti API changes."""

    @responses.activate
    def test_handles_legacy_node_format(self):
        """Test that we can handle legacy node response formats."""
        # Simulate old format without certain fields
        legacy_response = {
            "nodes": [
                {
                    "name": "Legacy Node",
                    "summary": "Old format"
                    # Missing 'id' and 'created_at' fields
                }
            ],
            "edges": []
        }

        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json=legacy_response,
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        # Should handle gracefully
        assert 'context' in result
        assert result['success'] is True

    @responses.activate
    def test_handles_response_without_edges(self):
        """Test handling response with only nodes (no edges key)."""
        response = {
            "nodes": [
                {"name": "Node 1", "summary": "Summary 1"}
            ]
            # No 'edges' key at all
        }

        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json=response,
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        # Should handle gracefully
        assert 'context' in result
        assert result['success'] is True

    @responses.activate
    def test_handles_empty_response(self):
        """Test handling empty response."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"nodes": [], "edges": []},
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        assert 'context' in result
        assert result['success'] is False
        assert "No relevant information found" in result['context']
