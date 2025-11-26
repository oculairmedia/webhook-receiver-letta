"""
Unit tests for tool_manager module.

Tests tool discovery, attachment, and keep-tools wildcard logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import requests

# Import the functions we're testing
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tool_manager import get_agent_tools, find_attach_tools


class TestGetAgentTools:
    """Tests for get_agent_tools function."""

    @patch('tool_manager.requests.get')
    def test_get_agent_tools_success(self, mock_get):
        """Test successfully retrieving agent tools."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "tool-123", "name": "search"},
            {"id": "tool-456", "name": "calculator"}
        ]
        mock_get.return_value = mock_response

        result = get_agent_tools("agent-789")

        assert result == ["tool-123", "tool-456"]
        mock_get.assert_called_once()

    @patch('tool_manager.requests.get')
    def test_get_agent_tools_empty_agent_id(self, mock_get):
        """Test handling of empty agent_id."""
        result = get_agent_tools("")

        assert result == []
        mock_get.assert_not_called()

    @patch('tool_manager.requests.get')
    def test_get_agent_tools_none_agent_id(self, mock_get):
        """Test handling of None agent_id."""
        result = get_agent_tools(None)

        assert result == []
        mock_get.assert_not_called()

    @patch('tool_manager.requests.get')
    def test_get_agent_tools_http_error(self, mock_get):
        """Test handling of HTTP error responses."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        result = get_agent_tools("agent-789")

        assert result == []

    @patch('tool_manager.requests.get')
    def test_get_agent_tools_request_exception(self, mock_get):
        """Test handling of request exceptions."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = get_agent_tools("agent-789")

        assert result == []

    @patch('tool_manager.requests.get')
    def test_get_agent_tools_json_decode_error(self, mock_get):
        """Test handling of JSON decode errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"
        mock_get.return_value = mock_response

        result = get_agent_tools("agent-789")

        assert result == []

    @patch('tool_manager.requests.get')
    def test_get_agent_tools_non_list_response(self, mock_get):
        """Test handling when response is not a list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tools": [{"id": "tool-123"}]}
        mock_get.return_value = mock_response

        result = get_agent_tools("agent-789")

        # Should handle gracefully and return empty list
        assert result == []

    @patch('tool_manager.requests.get')
    def test_get_agent_tools_includes_user_id_header(self, mock_get):
        """Test that user_id header is included in the request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        get_agent_tools("agent-test-123")

        call_args = mock_get.call_args
        headers = call_args[1]['headers']
        assert headers.get('user_id') == "agent-test-123"

    @patch('tool_manager.requests.get')
    def test_get_agent_tools_includes_authentication(self, mock_get):
        """Test that authentication headers are included."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        get_agent_tools("agent-123")

        call_args = mock_get.call_args
        headers = call_args[1]['headers']
        assert 'X-BARE-PASSWORD' in headers

    @patch('tool_manager.requests.get')
    def test_get_agent_tools_timeout_configured(self, mock_get):
        """Test that timeout is configured for the request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        get_agent_tools("agent-123")

        call_args = mock_get.call_args
        assert 'timeout' in call_args[1]
        assert call_args[1]['timeout'] == 15


class TestFindAttachTools:
    """Tests for find_attach_tools function."""

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_success(self, mock_post):
        """Test successful tool attachment."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "details": {
                "successful_attachments": [
                    {"tool_id": "tool-123", "name": "search"}
                ],
                "detached_tools": [],
                "preserved_tools": []
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = find_attach_tools(query="search tool", agent_id="agent-789")

        assert "successfully" in result.lower()
        assert "Attached 1 tools" in result
        mock_post.assert_called_once()

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_with_keep_tools(self, mock_post):
        """Test tool attachment with keep_tools specified."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "details": {
                "successful_attachments": [],
                "detached_tools": [],
                "preserved_tools": ["tool-existing-1", "tool-existing-2"]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = find_attach_tools(
            query="calculator",
            agent_id="agent-789",
            keep_tools="tool-existing-1,tool-existing-2"
        )

        # Check that keep_tools was sent as a list in the payload
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['keep_tools'] == ["tool-existing-1", "tool-existing-2"]

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_without_query(self, mock_post):
        """Test tool attachment without a query."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "details": {}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = find_attach_tools(agent_id="agent-789")

        # Verify query is not in payload when not provided
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert 'query' not in payload

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_http_error(self, mock_post):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.return_value = {
            "error": "Database connection failed"
        }
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        mock_post.return_value = mock_response

        result = find_attach_tools(query="test", agent_id="agent-789")

        assert "Error" in result
        assert "500" in result or "error" in result.lower()

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_request_exception(self, mock_post):
        """Test handling of request exceptions."""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        result = find_attach_tools(query="test", agent_id="agent-789")

        assert "Error" in result

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_custom_limit(self, mock_post):
        """Test using custom limit parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "details": {}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        find_attach_tools(query="test", agent_id="agent-789", limit=10)

        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['limit'] == 10

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_custom_min_score(self, mock_post):
        """Test using custom min_score parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "details": {}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        find_attach_tools(query="test", agent_id="agent-789", min_score=80.0)

        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['min_score'] == 80.0

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_with_heartbeat(self, mock_post):
        """Test requesting heartbeat."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "details": {}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        find_attach_tools(query="test", agent_id="agent-789", request_heartbeat=True)

        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['request_heartbeat'] is True

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_json_decode_error(self, mock_post):
        """Test handling of JSON decode errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Not JSON"
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = find_attach_tools(query="test", agent_id="agent-789")

        # Should handle gracefully
        assert "HTTP 200" in result or "updated" in result.lower()

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_empty_keep_tools(self, mock_post):
        """Test that empty keep_tools string is handled correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "details": {}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        find_attach_tools(query="test", agent_id="agent-789", keep_tools="")

        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['keep_tools'] == []

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_whitespace_in_keep_tools(self, mock_post):
        """Test that whitespace in keep_tools is handled correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "details": {}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        find_attach_tools(
            query="test",
            agent_id="agent-789",
            keep_tools=" tool-1 , tool-2 , tool-3 "
        )

        call_args = mock_post.call_args
        payload = call_args[1]['json']
        # Should strip whitespace
        assert payload['keep_tools'] == ["tool-1", "tool-2", "tool-3"]

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_headers(self, mock_post):
        """Test that correct headers are sent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "details": {}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        find_attach_tools(query="test", agent_id="agent-789")

        call_args = mock_post.call_args
        headers = call_args[1]['headers']
        assert headers['Content-Type'] == "application/json"

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_timeout(self, mock_post):
        """Test that timeout is configured."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "details": {}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        find_attach_tools(query="test", agent_id="agent-789")

        call_args = mock_post.call_args
        assert call_args[1]['timeout'] == 15

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_unexpected_exception(self, mock_post):
        """Test handling of unexpected exceptions."""
        mock_post.side_effect = ValueError("Unexpected error")

        result = find_attach_tools(query="test", agent_id="agent-789")

        assert "Error" in result
        assert "unexpected" in result.lower()

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_return_structured_true(self, mock_post):
        """Test returning structured dict when return_structured=True."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "details": {
                "successful_attachments": [
                    {"tool_id": "tool-123", "name": "search", "match_score": 85}
                ],
                "detached_tools": ["tool-old"],
                "preserved_tools": ["tool-keep"]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = find_attach_tools(query="search", agent_id="agent-789", return_structured=True)

        # Should return a dict instead of string
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "details" in result
        assert len(result["details"]["successful_attachments"]) == 1

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_return_structured_false(self, mock_post):
        """Test returning string when return_structured=False (default)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "details": {
                "successful_attachments": [],
                "detached_tools": [],
                "preserved_tools": []
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = find_attach_tools(query="search", agent_id="agent-789", return_structured=False)

        # Should return a string
        assert isinstance(result, str)

    @patch('tool_manager.requests.post')
    def test_find_attach_tools_structured_error_response(self, mock_post):
        """Test error response when return_structured=True.
        
        Note: Currently error responses return strings even when return_structured=True.
        This test documents the current behavior.
        """
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        result = find_attach_tools(query="test", agent_id="agent-789", return_structured=True)

        # Current behavior: errors return strings regardless of return_structured
        # The string should contain "Error"
        assert "Error" in str(result)