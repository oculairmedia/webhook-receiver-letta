"""
Unit tests for webhook_server.block_finders module.

Tests memory block finding logic and attachment status detection.
"""

import pytest
from unittest.mock import Mock, patch
import requests

from webhook_server.block_finders import find_memory_block


class TestFindMemoryBlock:
    """Tests for find_memory_block function."""

    @patch('webhook_server.block_finders.requests.get')
    def test_find_attached_block(self, mock_get):
        """Test finding a block that is attached to the agent."""
        # Mock response for agent blocks endpoint
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "block-123", "label": "cumulative_context", "value": "content"},
            {"id": "block-456", "label": "other_label", "value": "other"}
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        block, is_attached = find_memory_block("agent-789", "cumulative_context")

        assert block is not None
        assert block["id"] == "block-123"
        assert block["label"] == "cumulative_context"
        assert is_attached is True
        mock_get.assert_called_once()

    @patch('webhook_server.block_finders.requests.get')
    def test_find_global_block_not_attached(self, mock_get):
        """Test finding a global block that is not attached to the agent."""
        # First call: agent blocks (empty)
        mock_agent_response = Mock()
        mock_agent_response.json.return_value = []
        mock_agent_response.raise_for_status = Mock()

        # Second call: global blocks
        mock_global_response = Mock()
        mock_global_response.json.return_value = [
            {"id": "block-global-123", "label": "cumulative_context", "value": "global content"}
        ]
        mock_global_response.raise_for_status = Mock()

        mock_get.side_effect = [mock_agent_response, mock_global_response]

        block, is_attached = find_memory_block("agent-789", "cumulative_context")

        assert block is not None
        assert block["id"] == "block-global-123"
        assert is_attached is False
        assert mock_get.call_count == 2

    @patch('webhook_server.block_finders.requests.get')
    def test_find_no_block_found(self, mock_get):
        """Test when no matching block is found."""
        # First call: agent blocks (empty)
        mock_agent_response = Mock()
        mock_agent_response.json.return_value = []
        mock_agent_response.raise_for_status = Mock()

        # Second call: global blocks (empty)
        mock_global_response = Mock()
        mock_global_response.json.return_value = []
        mock_global_response.raise_for_status = Mock()

        mock_get.side_effect = [mock_agent_response, mock_global_response]

        block, is_attached = find_memory_block("agent-789", "nonexistent_label")

        assert block is None
        assert is_attached is False
        assert mock_get.call_count == 2

    @patch('webhook_server.block_finders.requests.get')
    def test_find_block_with_dict_response(self, mock_get):
        """Test handling response as a dict with 'blocks' key."""
        # Some APIs return {"blocks": [...]} instead of [...]
        mock_response = Mock()
        mock_response.json.return_value = {
            "blocks": [
                {"id": "block-dict-123", "label": "cumulative_context", "value": "content"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        block, is_attached = find_memory_block("agent-789", "cumulative_context")

        assert block is not None
        assert block["id"] == "block-dict-123"
        assert is_attached is True

    @patch('webhook_server.block_finders.requests.get')
    def test_find_block_without_agent_id(self, mock_get):
        """Test that providing no agent_id returns (None, False)."""
        block, is_attached = find_memory_block("", "cumulative_context")

        assert block is None
        assert is_attached is False
        mock_get.assert_not_called()

    @patch('webhook_server.block_finders.requests.get')
    def test_find_block_none_agent_id(self, mock_get):
        """Test that providing None agent_id returns (None, False)."""
        block, is_attached = find_memory_block(None, "cumulative_context")

        assert block is None
        assert is_attached is False
        mock_get.assert_not_called()

    @patch('webhook_server.block_finders.requests.get')
    def test_find_block_handles_request_exception(self, mock_get):
        """Test that request exceptions are caught and return (None, False)."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        block, is_attached = find_memory_block("agent-789", "cumulative_context")

        assert block is None
        assert is_attached is False

    @patch('webhook_server.block_finders.requests.get')
    def test_find_block_handles_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        block, is_attached = find_memory_block("agent-789", "cumulative_context")

        assert block is None
        assert is_attached is False

    @patch('webhook_server.block_finders.requests.get')
    def test_find_block_handles_generic_exception(self, mock_get):
        """Test handling of unexpected exceptions."""
        mock_get.side_effect = ValueError("Unexpected error")

        block, is_attached = find_memory_block("agent-789", "cumulative_context")

        assert block is None
        assert is_attached is False

    @patch('webhook_server.block_finders.requests.get')
    def test_find_block_adds_user_id_header(self, mock_get):
        """Test that user_id header is added for agent blocks request."""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        find_memory_block("agent-test-123", "cumulative_context")

        # Check first call (agent blocks) has user_id header
        first_call_args = mock_get.call_args_list[0]
        headers = first_call_args[1]['headers']
        assert headers.get('user_id') == "agent-test-123"

    @patch('webhook_server.block_finders.requests.get')
    def test_find_block_global_search_params(self, mock_get):
        """Test that global blocks search includes correct parameters."""
        # First call: agent blocks (empty)
        mock_agent_response = Mock()
        mock_agent_response.json.return_value = []
        mock_agent_response.raise_for_status = Mock()

        # Second call: global blocks
        mock_global_response = Mock()
        mock_global_response.json.return_value = []
        mock_global_response.raise_for_status = Mock()

        mock_get.side_effect = [mock_agent_response, mock_global_response]

        find_memory_block("agent-789", "test_label")

        # Check second call (global blocks) has correct params
        second_call_args = mock_get.call_args_list[1]
        params = second_call_args[1]['params']
        assert params['label'] == "test_label"
        assert params['templates_only'] == "false"

    @patch('webhook_server.block_finders.requests.get')
    def test_find_block_prefers_attached_over_global(self, mock_get):
        """Test that attached blocks are found before checking global blocks."""
        # If block exists in agent blocks, should not check global
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "block-attached-123", "label": "cumulative_context", "value": "content"}
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        block, is_attached = find_memory_block("agent-789", "cumulative_context")

        assert block is not None
        assert is_attached is True
        # Should only call once (agent blocks endpoint)
        assert mock_get.call_count == 1

    @patch('webhook_server.block_finders.requests.get')
    def test_find_block_returns_first_matching_global_block(self, mock_get):
        """Test that first matching global block is returned when multiple exist."""
        # First call: agent blocks (empty)
        mock_agent_response = Mock()
        mock_agent_response.json.return_value = []
        mock_agent_response.raise_for_status = Mock()

        # Second call: multiple global blocks
        mock_global_response = Mock()
        mock_global_response.json.return_value = [
            {"id": "block-global-1", "label": "cumulative_context", "value": "first"},
            {"id": "block-global-2", "label": "cumulative_context", "value": "second"}
        ]
        mock_global_response.raise_for_status = Mock()

        mock_get.side_effect = [mock_agent_response, mock_global_response]

        block, is_attached = find_memory_block("agent-789", "cumulative_context")

        assert block is not None
        assert block["id"] == "block-global-1"
        assert is_attached is False

    @patch('webhook_server.block_finders.requests.get')
    def test_find_block_with_timeout(self, mock_get):
        """Test that requests have timeout configured."""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        find_memory_block("agent-789", "cumulative_context")

        # Check that timeout was specified
        first_call = mock_get.call_args_list[0]
        assert 'timeout' in first_call[1]
        assert first_call[1]['timeout'] == 10
