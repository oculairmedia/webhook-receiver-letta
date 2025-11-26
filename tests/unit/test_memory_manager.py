"""
Unit tests for webhook_server.memory_manager module.

Tests memory block creation, updates, and attachment operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from webhook_server.memory_manager import (
    create_memory_block,
    update_memory_block,
    attach_block_to_agent,
    create_tool_inventory_block
)


class TestCreateMemoryBlock:
    """Tests for create_memory_block function."""

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('webhook_server.memory_manager.requests.post')
    @patch('webhook_server.memory_manager.attach_block_to_agent')
    def test_create_new_block_without_agent(self, mock_attach, mock_post, mock_find):
        """Test creating a new memory block without agent_id."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "block-123",
            "label": "test_block",
            "value": "Test content"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        block_data = {
            "label": "test_block",
            "value": "Test content"
        }

        result = create_memory_block(block_data)

        assert result["id"] == "block-123"
        assert result["label"] == "test_block"
        mock_post.assert_called_once()
        mock_attach.assert_not_called()
        mock_find.assert_not_called()

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('webhook_server.memory_manager.requests.post')
    @patch('webhook_server.memory_manager.attach_block_to_agent')
    def test_create_new_block_with_agent_auto_attach(self, mock_attach, mock_post, mock_find):
        """Test creating a new block with agent_id triggers auto-attachment."""
        # No existing block found
        mock_find.return_value = (None, False)

        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "block-456",
            "label": "cumulative_context",
            "value": "New content"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        mock_attach.return_value = True

        block_data = {
            "label": "cumulative_context",
            "value": "New content"
        }

        result = create_memory_block(block_data, agent_id="agent-123")

        assert result["id"] == "block-456"
        mock_find.assert_called_once_with("agent-123", "cumulative_context")
        mock_attach.assert_called_once_with("agent-123", "block-456")

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('webhook_server.memory_manager.update_memory_block')
    @patch('webhook_server.memory_manager.attach_block_to_agent')
    def test_update_existing_attached_block(self, mock_attach, mock_update, mock_find):
        """Test updating an existing block that is already attached."""
        existing_block = {
            "id": "block-789",
            "label": "cumulative_context",
            "value": "Existing content"
        }
        # Block exists and is attached
        mock_find.return_value = (existing_block, True)

        mock_update.return_value = {
            "id": "block-789",
            "value": "Updated content"
        }

        block_data = {
            "label": "cumulative_context",
            "value": "New content to add"
        }

        result = create_memory_block(block_data, agent_id="agent-123")

        mock_find.assert_called_once()
        mock_update.assert_called_once()
        # Should not try to attach since already attached
        mock_attach.assert_not_called()

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('webhook_server.memory_manager.update_memory_block')
    @patch('webhook_server.memory_manager.attach_block_to_agent')
    def test_update_existing_unattached_block_triggers_attachment(self, mock_attach, mock_update, mock_find):
        """Test that finding an unattached block triggers attachment."""
        existing_block = {
            "id": "block-999",
            "label": "cumulative_context",
            "value": "Existing content"
        }
        # Block exists but NOT attached
        mock_find.return_value = (existing_block, False)

        mock_update.return_value = {"id": "block-999", "value": "Updated"}
        mock_attach.return_value = True

        block_data = {
            "label": "cumulative_context",
            "value": "New content"
        }

        result = create_memory_block(block_data, agent_id="agent-123")

        mock_attach.assert_called_once_with("agent-123", "block-999")
        mock_update.assert_called_once()


class TestUpdateMemoryBlock:
    """Tests for update_memory_block function."""

    @patch('webhook_server.memory_manager._build_cumulative_context')
    @patch('webhook_server.memory_manager.requests.patch')
    def test_update_block_calls_cumulative_context(self, mock_patch, mock_build_context):
        """Test that update uses _build_cumulative_context."""
        mock_build_context.return_value = "Cumulative context"

        mock_response = Mock()
        mock_response.json.return_value = {"id": "block-123", "value": "Cumulative context"}
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response

        existing_block = {"value": "Old content"}
        block_data = {"value": "New content"}

        result = update_memory_block("block-123", block_data, existing_block=existing_block)

        mock_build_context.assert_called_once_with("Old content", "New content")
        mock_patch.assert_called_once()

    @patch('webhook_server.memory_manager._build_cumulative_context')
    @patch('webhook_server.memory_manager.requests.patch')
    def test_update_block_with_agent_id_adds_header(self, mock_patch, mock_build_context):
        """Test that agent_id is added to headers when provided."""
        mock_build_context.return_value = "Context"

        mock_response = Mock()
        mock_response.json.return_value = {"id": "block-123"}
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response

        block_data = {"value": "New"}

        update_memory_block("block-123", block_data, agent_id="agent-456")

        # Check that user_id header was set
        call_args = mock_patch.call_args
        headers = call_args[1]['headers']
        assert headers.get('user_id') == "agent-456"

    @patch('webhook_server.memory_manager._build_cumulative_context')
    @patch('webhook_server.memory_manager.requests.patch')
    def test_update_block_with_metadata(self, mock_patch, mock_build_context):
        """Test updating block with metadata."""
        mock_build_context.return_value = "Context"

        mock_response = Mock()
        mock_response.json.return_value = {"id": "block-123"}
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response

        block_data = {
            "value": "New content",
            "metadata": {"source": "test", "priority": "high"}
        }

        update_memory_block("block-123", block_data)

        # Check that metadata was included
        call_args = mock_patch.call_args
        json_data = call_args[1]['json']
        assert json_data['metadata'] == {"source": "test", "priority": "high"}

    @patch('webhook_server.memory_manager._build_cumulative_context')
    @patch('webhook_server.memory_manager.requests.patch')
    def test_update_block_handles_http_error(self, mock_patch, mock_build_context):
        """Test that HTTP errors are raised properly."""
        mock_build_context.return_value = "Context"

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_patch.return_value = mock_response

        block_data = {"value": "New"}

        with pytest.raises(requests.exceptions.HTTPError):
            update_memory_block("block-123", block_data)


class TestAttachBlockToAgent:
    """Tests for attach_block_to_agent function."""

    @patch('webhook_server.memory_manager.requests.patch')
    def test_attach_block_success(self, mock_patch):
        """Test successful block attachment."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response

        result = attach_block_to_agent("agent-123", "block-456")

        assert result is True
        mock_patch.assert_called_once()

    @patch('webhook_server.memory_manager.requests.patch')
    def test_attach_block_with_list_block_id(self, mock_patch):
        """Test handling when block_id is accidentally passed as a list."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response

        # Pass block_id as a list
        result = attach_block_to_agent("agent-123", ["block-456"])

        assert result is True
        # Should have converted to string and called with first element
        call_args = mock_patch.call_args
        url = call_args[0][0]
        assert "block-456" in url

    @patch('webhook_server.memory_manager.requests.patch')
    def test_attach_block_with_empty_list_fails(self, mock_patch):
        """Test that empty list for block_id returns False."""
        result = attach_block_to_agent("agent-123", [])

        assert result is False
        mock_patch.assert_not_called()

    @patch('webhook_server.memory_manager.requests.patch')
    def test_attach_block_handles_request_exception(self, mock_patch):
        """Test that request exceptions are caught and return False."""
        mock_patch.side_effect = requests.exceptions.RequestException("Connection error")

        result = attach_block_to_agent("agent-123", "block-456")

        assert result is False

    @patch('webhook_server.memory_manager.requests.patch')
    def test_attach_block_adds_user_id_header(self, mock_patch):
        """Test that user_id header is set to agent_id."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response

        attach_block_to_agent("agent-789", "block-123")

        call_args = mock_patch.call_args
        headers = call_args[1]['headers']
        assert headers.get('user_id') == "agent-789"

    @patch('webhook_server.memory_manager.requests.patch')
    def test_attach_block_constructs_correct_url(self, mock_patch):
        """Test that the attachment URL is constructed correctly."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response

        attach_block_to_agent("agent-999", "block-888")

        call_args = mock_patch.call_args
        url = call_args[0][0]
        assert "agents/agent-999/core-memory/blocks/attach/block-888" in url

    @patch('webhook_server.memory_manager.requests.patch')
    def test_attach_block_with_http_error(self, mock_patch):
        """Test handling of HTTP errors during attachment."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Forbidden")
        mock_patch.return_value = mock_response

        result = attach_block_to_agent("agent-123", "block-456")

        assert result is False

    @patch('webhook_server.memory_manager.requests.patch')
    def test_attach_block_handles_409_conflict_as_success(self, mock_patch):
        """Test that 409 Conflict (already attached) is treated as success."""
        mock_response = Mock()
        mock_response.status_code = 409
        mock_patch.return_value = mock_response

        result = attach_block_to_agent("agent-123", "block-456")

        # 409 means block is already attached, which is still success
        assert result is True
        mock_response.raise_for_status.assert_not_called()


class TestMemoryManagerEdgeCases:
    """Edge case tests for memory manager module."""

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('webhook_server.memory_manager.requests.post')
    def test_create_block_with_empty_value(self, mock_post, mock_find):
        """Test creating block with empty value."""
        mock_find.return_value = (None, False)

        mock_response = Mock()
        mock_response.json.return_value = {"id": "block-123", "value": ""}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        block_data = {"label": "test", "value": ""}

        result = create_memory_block(block_data, agent_id="agent-123")

        assert "id" in result
        mock_post.assert_called_once()

    @patch('webhook_server.memory_manager.requests.patch')
    def test_attach_block_converts_numeric_block_id_to_string(self, mock_patch):
        """Test that numeric block_id is converted to string."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response

        # Pass numeric block_id
        result = attach_block_to_agent("agent-123", 456)

        assert result is True
        call_args = mock_patch.call_args
        url = call_args[0][0]
        assert "456" in url


class TestCreateToolInventoryBlock:
    """Tests for create_tool_inventory_block function."""

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('webhook_server.memory_manager.requests.patch')
    def test_update_existing_inventory_block(self, mock_patch, mock_find):
        """Test updating an existing tool inventory block."""
        existing_block = {
            "id": "block-tool-inv",
            "label": "available_tools",
            "value": "Old inventory"
        }
        mock_find.return_value = (existing_block, True)

        mock_response = Mock()
        mock_response.json.return_value = {"id": "block-tool-inv", "value": "New inventory"}
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response

        result = create_tool_inventory_block("agent-123", "New inventory content")

        assert "id" in result
        mock_patch.assert_called_once()

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('webhook_server.memory_manager.requests.post')
    @patch('webhook_server.memory_manager.attach_block_to_agent')
    def test_create_new_inventory_block(self, mock_attach, mock_post, mock_find):
        """Test creating a new tool inventory block."""
        mock_find.return_value = (None, False)

        mock_response = Mock()
        mock_response.json.return_value = {"id": "block-new", "label": "available_tools"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        mock_attach.return_value = True

        result = create_tool_inventory_block("agent-123", "Tool inventory content")

        assert result["id"] == "block-new"
        mock_post.assert_called_once()
        mock_attach.assert_called_once_with("agent-123", "block-new")

    def test_empty_agent_id_returns_empty(self):
        """Test that empty agent_id returns empty dict."""
        result = create_tool_inventory_block("", "content")
        assert result == {}

    def test_empty_content_returns_empty(self):
        """Test that empty content returns empty dict."""
        result = create_tool_inventory_block("agent-123", "")
        assert result == {}

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('webhook_server.memory_manager.requests.patch')
    @patch('webhook_server.memory_manager.attach_block_to_agent')
    def test_attach_unattached_existing_block(self, mock_attach, mock_patch, mock_find):
        """Test that existing but unattached block triggers attachment."""
        existing_block = {
            "id": "block-unattached",
            "label": "available_tools",
            "value": "Old content"
        }
        # Block exists but NOT attached
        mock_find.return_value = (existing_block, False)

        mock_response = Mock()
        mock_response.json.return_value = {"id": "block-unattached"}
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response

        mock_attach.return_value = True

        result = create_tool_inventory_block("agent-123", "New content")

        mock_attach.assert_called_once_with("agent-123", "block-unattached")
        mock_patch.assert_called_once()

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('webhook_server.memory_manager.requests.patch')
    def test_inventory_block_uses_snapshot_not_cumulative(self, mock_patch, mock_find):
        """Test that tool inventory replaces content, not cumulative."""
        existing_block = {
            "id": "block-123",
            "label": "available_tools",
            "value": "Old tools list"
        }
        mock_find.return_value = (existing_block, True)

        mock_response = Mock()
        mock_response.json.return_value = {"id": "block-123", "value": "New tools"}
        mock_response.raise_for_status = Mock()
        mock_patch.return_value = mock_response

        create_tool_inventory_block("agent-123", "Fresh tools list")

        # Check that the value is replaced directly, not cumulative
        call_args = mock_patch.call_args
        json_data = call_args[1]['json']
        assert json_data['value'] == "Fresh tools list"

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('webhook_server.memory_manager.requests.post')
    @patch('webhook_server.memory_manager.attach_block_to_agent')
    def test_inventory_block_has_correct_metadata(self, mock_attach, mock_post, mock_find):
        """Test that inventory block has correct metadata."""
        mock_find.return_value = (None, False)

        mock_response = Mock()
        mock_response.json.return_value = {"id": "block-123"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        create_tool_inventory_block("agent-123", "Tools content")

        call_args = mock_post.call_args
        json_data = call_args[1]['json']
        
        assert json_data['label'] == "available_tools"
        assert json_data['metadata']['source'] == "tool_inventory"
        assert json_data['metadata']['type'] == "snapshot"
