"""
Integration tests for Letta API connectivity.

These tests verify the webhook server's integration with the Letta API,
including memory block operations, agent retrieval, and authentication.
"""

import pytest
from unittest.mock import Mock, patch
import requests
import responses

from webhook_server.memory_manager import (
    create_memory_block,
    update_memory_block,
    attach_block_to_agent
)
from webhook_server.block_finders import find_memory_block


class TestLettaAPIAuthentication:
    """Tests for Letta API authentication."""

    @responses.activate
    def test_letta_api_uses_authentication_headers(self):
        """Test that Letta API requests include authentication."""
        responses.add(
            responses.POST,
            "http://test-letta.example.com/v1/blocks",
            json={"id": "block-123", "label": "test"},
            status=200
        )

        with patch('webhook_server.memory_manager.get_api_url', return_value="http://test-letta.example.com/v1/blocks"):
            create_memory_block({"label": "test", "value": "content"})

        # Check that authentication header was sent
        assert len(responses.calls) == 1
        request_headers = responses.calls[0].request.headers
        assert 'X-BARE-PASSWORD' in request_headers or 'Authorization' in request_headers

    @responses.activate
    def test_letta_api_401_unauthorized(self):
        """Test handling of authentication failures."""
        responses.add(
            responses.POST,
            "http://test-letta.example.com/v1/blocks",
            json={"error": "Unauthorized"},
            status=401
        )

        with patch('webhook_server.memory_manager.get_api_url', return_value="http://test-letta.example.com/v1/blocks"):
            with pytest.raises(requests.exceptions.HTTPError):
                create_memory_block({"label": "test", "value": "content"})


class TestLettaMemoryBlockCRUD:
    """Tests for Letta memory block CRUD operations."""

    @responses.activate
    def test_create_memory_block_success(self):
        """Test successful memory block creation."""
        responses.add(
            responses.POST,
            "http://test-letta.example.com/v1/blocks",
            json={
                "id": "block-new-123",
                "label": "cumulative_context",
                "value": "Test content",
                "limit": 6000
            },
            status=200
        )

        with patch('webhook_server.memory_manager.get_api_url', return_value="http://test-letta.example.com/v1/blocks"), \
             patch('webhook_server.memory_manager.find_memory_block', return_value=(None, False)):

            result = create_memory_block({
                "label": "cumulative_context",
                "value": "Test content"
            })

        assert result['id'] == "block-new-123"
        assert result['label'] == "cumulative_context"

    @responses.activate
    def test_update_memory_block_success(self):
        """Test successful memory block update."""
        responses.add(
            responses.PATCH,
            "http://test-letta.example.com/v1/blocks/block-456",
            json={
                "id": "block-456",
                "value": "Updated content"
            },
            status=200
        )

        with patch('webhook_server.memory_manager.get_api_url', return_value="http://test-letta.example.com/v1/blocks/block-456"), \
             patch('webhook_server.memory_manager._build_cumulative_context', return_value="Updated content"):

            result = update_memory_block(
                "block-456",
                {"value": "New content"},
                existing_block={"value": "Old content"}
            )

        assert result['value'] == "Updated content"

    @responses.activate
    def test_attach_block_to_agent_success(self):
        """Test successful block attachment to agent."""
        responses.add(
            responses.PATCH,
            "http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks/attach/block-456",
            json={"success": True},
            status=200
        )

        with patch('webhook_server.memory_manager.get_api_url',
                   return_value="http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks/attach/block-456"):

            result = attach_block_to_agent("agent-123", "block-456")

        assert result is True

    @responses.activate
    def test_find_attached_memory_block(self):
        """Test finding a memory block attached to an agent."""
        responses.add(
            responses.GET,
            "http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks",
            json=[
                {
                    "id": "block-attached-789",
                    "label": "cumulative_context",
                    "value": "Context content"
                }
            ],
            status=200
        )

        with patch('webhook_server.block_finders.get_api_url',
                   return_value="http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks"):

            block, is_attached = find_memory_block("agent-123", "cumulative_context")

        assert block is not None
        assert block['id'] == "block-attached-789"
        assert is_attached is True

    @responses.activate
    def test_find_global_memory_block(self):
        """Test finding a global memory block not attached to agent."""
        # First call: no attached blocks
        responses.add(
            responses.GET,
            "http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks",
            json=[],
            status=200
        )
        # Second call: global blocks
        responses.add(
            responses.GET,
            "http://test-letta.example.com/v1/blocks",
            json=[
                {
                    "id": "block-global-999",
                    "label": "cumulative_context",
                    "value": "Global content"
                }
            ],
            status=200
        )

        with patch('webhook_server.block_finders.get_api_url', side_effect=[
            "http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks",
            "http://test-letta.example.com/v1/blocks"
        ]):
            block, is_attached = find_memory_block("agent-123", "cumulative_context")

        assert block is not None
        assert block['id'] == "block-global-999"
        assert is_attached is False


class TestLettaAPIErrorHandling:
    """Tests for Letta API error handling."""

    @responses.activate
    def test_handles_404_not_found(self):
        """Test handling of 404 errors."""
        responses.add(
            responses.GET,
            "http://test-letta.example.com/v1/agents/agent-nonexistent/core-memory/blocks",
            json={"error": "Agent not found"},
            status=404
        )

        with patch('webhook_server.block_finders.get_api_url',
                   return_value="http://test-letta.example.com/v1/agents/agent-nonexistent/core-memory/blocks"):

            block, is_attached = find_memory_block("agent-nonexistent", "cumulative_context")

        assert block is None
        assert is_attached is False

    @responses.activate
    def test_handles_500_server_error(self):
        """Test handling of server errors."""
        responses.add(
            responses.POST,
            "http://test-letta.example.com/v1/blocks",
            json={"error": "Internal server error"},
            status=500
        )

        with patch('webhook_server.memory_manager.get_api_url', return_value="http://test-letta.example.com/v1/blocks"), \
             patch('webhook_server.memory_manager.find_memory_block', return_value=(None, False)):

            with pytest.raises(requests.exceptions.HTTPError):
                create_memory_block({"label": "test", "value": "content"})

    @responses.activate
    def test_handles_network_timeout(self):
        """Test handling of network timeouts."""
        responses.add(
            responses.GET,
            "http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks",
            body=requests.exceptions.Timeout("Request timeout")
        )

        with patch('webhook_server.block_finders.get_api_url',
                   return_value="http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks"):

            block, is_attached = find_memory_block("agent-123", "cumulative_context")

        assert block is None
        assert is_attached is False


class TestLettaAgentOperations:
    """Tests for Letta agent-related operations."""

    @responses.activate
    def test_create_and_attach_block_workflow(self):
        """Test the complete workflow of creating and attaching a block."""
        # Step 1: Check for existing block (none found)
        responses.add(
            responses.GET,
            "http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks",
            json=[],
            status=200
        )
        responses.add(
            responses.GET,
            "http://test-letta.example.com/v1/blocks",
            json=[],
            status=200
        )

        # Step 2: Create new block
        responses.add(
            responses.POST,
            "http://test-letta.example.com/v1/blocks",
            json={
                "id": "block-new-555",
                "label": "cumulative_context",
                "value": "New context"
            },
            status=200
        )

        # Step 3: Attach block to agent
        responses.add(
            responses.PATCH,
            "http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks/attach/block-new-555",
            json={"success": True},
            status=200
        )

        with patch('webhook_server.memory_manager.get_api_url', side_effect=[
            "http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks",
            "http://test-letta.example.com/v1/blocks",
            "http://test-letta.example.com/v1/blocks",
            "http://test-letta.example.com/v1/agents/agent-123/core-memory/blocks/attach/block-new-555"
        ]):
            result = create_memory_block(
                {"label": "cumulative_context", "value": "New context"},
                agent_id="agent-123"
            )

        assert result['id'] == "block-new-555"
        # Should have called attach endpoint
        assert any('attach' in call.request.url for call in responses.calls)
