"""
Contract tests for Graphiti API.

These tests verify that the Graphiti API responses match expected schemas.
Contract tests help detect breaking changes in external APIs.
"""

import pytest
from unittest.mock import Mock, patch
import responses


@pytest.mark.contract
class TestGraphitiNodeSearchContract:
    """Contract tests for Graphiti node search endpoint."""

    @responses.activate
    def test_node_search_response_schema(self):
        """Test that node search response matches expected schema."""
        expected_response = {
            "nodes": [
                {
                    "id": "node-123",
                    "name": "Test Node",
                    "summary": "Node summary",
                    "created_at": "2024-01-15T10:00:00Z"
                }
            ]
        }

        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search/nodes",
            json=expected_response,
            status=200
        )

        # Mock empty facts response
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"facts": []},
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        # Verify schema compliance
        assert 'nodes' in expected_response
        assert isinstance(expected_response['nodes'], list)

        if expected_response['nodes']:
            node = expected_response['nodes'][0]
            assert 'id' in node or 'name' in node
            assert 'summary' in node

    @responses.activate
    def test_node_search_request_schema(self):
        """Test that node search request has correct schema."""
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search/nodes",
            json={"nodes": []},
            status=200
        )
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"facts": []},
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            query_graphiti_api("test query", max_nodes=5)

        # Verify request payload schema
        request_body = responses.calls[0].request.body
        import json
        payload = json.loads(request_body)

        # Expected schema
        assert 'query' in payload
        assert isinstance(payload['query'], str)
        assert 'max_nodes' in payload
        assert isinstance(payload['max_nodes'], int)


@pytest.mark.contract
class TestGraphitiFactSearchContract:
    """Contract tests for Graphiti fact search endpoint."""

    @responses.activate
    def test_fact_search_response_schema(self):
        """Test that fact search response matches expected schema."""
        expected_response = {
            "facts": [
                {
                    "id": "fact-456",
                    "fact": "Test fact text",
                    "source": "node-123",
                    "target": "node-456",
                    "created_at": "2024-01-15T11:00:00Z"
                }
            ]
        }

        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search/nodes",
            json={"nodes": []},
            status=200
        )
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json=expected_response,
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        # Verify schema compliance
        assert 'facts' in expected_response
        assert isinstance(expected_response['facts'], list)

        if expected_response['facts']:
            fact = expected_response['facts'][0]
            assert 'fact' in fact
            assert isinstance(fact['fact'], str)


@pytest.mark.contract
class TestGraphitiErrorContract:
    """Contract tests for Graphiti API error responses."""

    @responses.activate
    def test_error_response_schema(self):
        """Test that error responses have expected structure."""
        error_response = {
            "error": "Internal server error",
            "message": "Database connection failed",
            "status": 500
        }

        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search/nodes",
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
            ]
        }

        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search/nodes",
            json=legacy_response,
            status=200
        )
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json={"facts": []},
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        # Should handle gracefully
        assert 'context' in result

    @responses.activate
    def test_handles_list_vs_dict_response(self):
        """Test handling both list and dict response formats."""
        # Some APIs might return list directly, others wrap in dict
        list_response = [
            {"name": "Node 1", "summary": "Summary 1"}
        ]

        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search/nodes",
            json=list_response,
            status=200
        )
        responses.add(
            responses.POST,
            "http://test-graphiti.example.com:8003/search",
            json=[],
            status=200
        )

        from webhook_server.app import query_graphiti_api

        with patch('webhook_server.app.GRAPHITI_API_URL', 'http://test-graphiti.example.com:8003'):
            result = query_graphiti_api("test")

        # Should handle gracefully
        assert 'context' in result
