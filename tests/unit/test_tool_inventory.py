"""
Unit tests for webhook_server.tool_inventory module.

Tests categorization, formatting, attachment tracking, and inventory building.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, UTC

from webhook_server.tool_inventory import (
    CATEGORY_MAPPING,
    CORE_TOOL_NAMES,
    RECENT_ATTACHMENTS,
    get_agent_tools_with_details,
    categorize_tool,
    categorize_tools,
    record_tool_attachment,
    get_recent_attachments,
    format_tool_entry,
    format_tool_inventory,
    build_tool_inventory_block,
)


class TestCategoryMapping:
    """Tests for category mapping constants."""

    def test_category_mapping_exists(self):
        """Test that category mapping is defined."""
        assert CATEGORY_MAPPING is not None
        assert isinstance(CATEGORY_MAPPING, dict)
        assert len(CATEGORY_MAPPING) > 0

    def test_category_mapping_contains_expected_servers(self):
        """Test that expected MCP servers are mapped."""
        expected_servers = ["Searxng", "bookstack", "huly", "graphiti"]
        for server in expected_servers:
            assert server in CATEGORY_MAPPING

    def test_core_tool_names_defined(self):
        """Test that core tool names are defined."""
        assert CORE_TOOL_NAMES is not None
        assert isinstance(CORE_TOOL_NAMES, set)
        assert "send_message" in CORE_TOOL_NAMES
        assert "conversation_search" in CORE_TOOL_NAMES


class TestCategorizeTool:
    """Tests for categorize_tool function."""

    def test_categorize_core_tool(self):
        """Test that core tools are categorized correctly."""
        tool = {"name": "send_message"}
        assert categorize_tool(tool) == "Core"

    def test_categorize_tool_by_mcp_metadata(self):
        """Test categorization by MCP metadata."""
        tool = {
            "name": "searxng_web_search",
            "metadata_": {"mcp": {"server_name": "Searxng"}}
        }
        assert categorize_tool(tool) == "Web Search"

    def test_categorize_tool_by_mcp_server_name(self):
        """Test categorization by mcp_server_name field."""
        tool = {
            "name": "huly_list_issues",
            "mcp_server_name": "huly"
        }
        assert categorize_tool(tool) == "Project Management"

    def test_categorize_tool_by_tags(self):
        """Test categorization by tags."""
        tool = {
            "name": "some_tool",
            "tags": ["mcp:bookstack", "knowledge"]
        }
        assert categorize_tool(tool) == "Knowledge & Docs"

    def test_categorize_unknown_tool(self):
        """Test that unknown tools get 'Other' category."""
        tool = {"name": "unknown_tool"}
        assert categorize_tool(tool) == "Other"

    def test_categorize_tool_empty_dict(self):
        """Test categorization with empty tool dict."""
        tool = {}
        result = categorize_tool(tool)
        # Should not crash, should return "Other"
        assert result == "Other"


class TestCategorizeTools:
    """Tests for categorize_tools function."""

    def test_categorize_multiple_tools(self):
        """Test categorizing multiple tools."""
        tools = [
            {"name": "send_message"},
            {"name": "searxng_web_search", "metadata_": {"mcp": {"server_name": "Searxng"}}},
            {"name": "unknown_tool"}
        ]
        result = categorize_tools(tools)
        
        assert "Core" in result
        assert "Web Search" in result
        assert "Other" in result
        assert len(result["Core"]) == 1
        assert len(result["Web Search"]) == 1
        assert len(result["Other"]) == 1

    def test_categorize_empty_list(self):
        """Test categorizing empty list."""
        result = categorize_tools([])
        assert result == {}


class TestRecordToolAttachment:
    """Tests for record_tool_attachment function."""

    def setup_method(self):
        """Clear attachments before each test."""
        RECENT_ATTACHMENTS.clear()

    def test_record_single_attachment(self):
        """Test recording a single attachment."""
        record_tool_attachment(
            "agent-123", 
            "test_tool", 
            "tool-456", 
            "auto: 'search'", 
            85.5
        )
        
        assert "agent-123" in RECENT_ATTACHMENTS
        assert len(RECENT_ATTACHMENTS["agent-123"]) == 1
        
        record = RECENT_ATTACHMENTS["agent-123"][0]
        assert record["tool_name"] == "test_tool"
        assert record["tool_id"] == "tool-456"
        assert record["reason"] == "auto: 'search'"
        assert record["score"] == 85.5
        assert "timestamp" in record

    def test_record_multiple_attachments(self):
        """Test that multiple attachments are recorded in order."""
        for i in range(3):
            record_tool_attachment(
                "agent-123",
                f"tool_{i}",
                f"tool-{i}",
                f"reason_{i}",
                float(i * 10)
            )
        
        records = RECENT_ATTACHMENTS["agent-123"]
        assert len(records) == 3
        # Most recent should be first
        assert records[0]["tool_name"] == "tool_2"
        assert records[1]["tool_name"] == "tool_1"
        assert records[2]["tool_name"] == "tool_0"

    def test_attachment_limit(self):
        """Test that only 10 attachments are kept."""
        for i in range(15):
            record_tool_attachment(
                "agent-123",
                f"tool_{i}",
                f"tool-{i}",
                f"reason_{i}",
                float(i)
            )
        
        assert len(RECENT_ATTACHMENTS["agent-123"]) == 10
        # Should have tools 5-14 (most recent)
        assert RECENT_ATTACHMENTS["agent-123"][0]["tool_name"] == "tool_14"
        assert RECENT_ATTACHMENTS["agent-123"][9]["tool_name"] == "tool_5"

    def test_separate_agents(self):
        """Test that attachments are tracked separately per agent."""
        record_tool_attachment("agent-1", "tool_a", "id-a", "reason", 50.0)
        record_tool_attachment("agent-2", "tool_b", "id-b", "reason", 60.0)
        
        assert "agent-1" in RECENT_ATTACHMENTS
        assert "agent-2" in RECENT_ATTACHMENTS
        assert len(RECENT_ATTACHMENTS["agent-1"]) == 1
        assert len(RECENT_ATTACHMENTS["agent-2"]) == 1


class TestGetRecentAttachments:
    """Tests for get_recent_attachments function."""

    def setup_method(self):
        """Clear attachments before each test."""
        RECENT_ATTACHMENTS.clear()

    def test_get_recent_empty(self):
        """Test getting attachments for agent with none."""
        result = get_recent_attachments("agent-unknown")
        assert result == []

    def test_get_recent_with_limit(self):
        """Test getting attachments with limit."""
        for i in range(10):
            record_tool_attachment(
                "agent-123",
                f"tool_{i}",
                f"tool-{i}",
                f"reason_{i}",
                float(i)
            )
        
        result = get_recent_attachments("agent-123", limit=3)
        assert len(result) == 3
        # Should be most recent
        assert result[0]["tool_name"] == "tool_9"

    def test_get_recent_default_limit(self):
        """Test default limit of 5."""
        for i in range(10):
            record_tool_attachment(
                "agent-123",
                f"tool_{i}",
                f"tool-{i}",
                "reason",
                50.0
            )
        
        result = get_recent_attachments("agent-123")
        assert len(result) == 5


class TestFormatToolEntry:
    """Tests for format_tool_entry function."""

    def test_format_with_description(self):
        """Test formatting with description."""
        tool = {"name": "searxng_search", "description": "Search the web"}
        result = format_tool_entry(tool)
        
        assert "searxng_search" in result
        assert "Search the web" in result
        assert result.startswith("• ")

    def test_format_without_description(self):
        """Test formatting without description."""
        tool = {"name": "searxng_search", "description": "Search the web"}
        result = format_tool_entry(tool, include_description=False)
        
        assert "searxng_search" in result
        assert "Search the web" not in result

    def test_format_truncates_long_description(self):
        """Test that long descriptions are truncated."""
        long_desc = "A" * 200
        tool = {"name": "test_tool", "description": long_desc}
        result = format_tool_entry(tool)
        
        # Should be truncated to 80 chars + "..."
        assert len(result) < len(long_desc)
        assert "..." in result

    def test_format_missing_name(self):
        """Test formatting with missing name."""
        tool = {"description": "Some tool"}
        result = format_tool_entry(tool)
        
        assert "unknown" in result

    def test_format_empty_description(self):
        """Test formatting with empty description."""
        tool = {"name": "test_tool", "description": ""}
        result = format_tool_entry(tool)
        
        assert "test_tool" in result
        assert " - " not in result  # No separator when no description


class TestGetAgentToolsWithDetails:
    """Tests for get_agent_tools_with_details function."""

    def test_get_tools_no_agent_id(self):
        """Test with no agent ID."""
        result = get_agent_tools_with_details("")
        assert result == []
        
        result = get_agent_tools_with_details(None)
        assert result == []

    @patch('webhook_server.tool_inventory.requests.get')
    def test_get_tools_success(self, mock_get):
        """Test successful tool retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "tool-1", "name": "tool_one"},
            {"id": "tool-2", "name": "tool_two"}
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = get_agent_tools_with_details("agent-123")
        
        assert len(result) == 2
        assert result[0]["name"] == "tool_one"

    @patch('webhook_server.tool_inventory.requests.get')
    def test_get_tools_handles_error(self, mock_get):
        """Test error handling."""
        mock_get.side_effect = Exception("Network error")
        
        result = get_agent_tools_with_details("agent-123")
        
        assert result == []

    @patch('webhook_server.tool_inventory.requests.get')
    def test_get_tools_handles_non_list_response(self, mock_get):
        """Test handling of non-list response."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Not found"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = get_agent_tools_with_details("agent-123")
        
        assert result == []


class TestFormatToolInventory:
    """Tests for format_tool_inventory function."""

    def setup_method(self):
        """Clear attachments before each test."""
        RECENT_ATTACHMENTS.clear()

    def test_format_empty_tools(self):
        """Test formatting with no tools."""
        result = format_tool_inventory("agent-123", [])
        
        assert "None currently attached" in result

    def test_format_with_tools(self):
        """Test formatting with tools."""
        tools = [
            {"id": "tool-1", "name": "send_message", "description": "Send a message"},
            {"id": "tool-2", "name": "searxng_search", "description": "Search web",
             "metadata_": {"mcp": {"server_name": "Searxng"}}}
        ]
        
        result = format_tool_inventory("agent-123", tools)
        
        assert "Available Tools" in result
        assert "2 total" in result
        assert "send_message" in result
        assert "Core" in result
        assert "Web Search" in result

    def test_format_includes_recent_attachments(self):
        """Test that recent attachments are shown."""
        # First record an attachment
        record_tool_attachment("agent-123", "new_tool", "tool-99", "auto: 'test'", 90.0)
        
        tools = [
            {"id": "tool-99", "name": "new_tool", "description": "A new tool"}
        ]
        
        result = format_tool_inventory("agent-123", tools)
        
        assert "Recently Attached" in result
        assert "new_tool" in result
        assert "auto: 'test'" in result

    def test_format_truncates_long_inventory(self):
        """Test that very long inventories are truncated."""
        # Create many tools to exceed 4500 char limit
        tools = []
        for i in range(100):
            tools.append({
                "id": f"tool-{i}",
                "name": f"very_long_tool_name_number_{i}_with_extra_text",
                "description": "A" * 100
            })
        
        result = format_tool_inventory("agent-123", tools)
        
        # Should be truncated
        assert len(result) < 4600
        # Should indicate truncation
        if len(result) > 4450:
            assert "truncated" in result.lower() or "..." in result


class TestBuildToolInventoryBlock:
    """Tests for build_tool_inventory_block function."""

    def setup_method(self):
        """Clear attachments before each test."""
        RECENT_ATTACHMENTS.clear()

    @patch('webhook_server.tool_inventory.get_agent_tools_with_details')
    def test_build_success(self, mock_get_tools):
        """Test successful inventory build."""
        mock_get_tools.return_value = [
            {"id": "tool-1", "name": "send_message", "description": "Send msg"}
        ]
        
        result = build_tool_inventory_block("agent-123")
        
        assert result["success"] is True
        assert "content" in result
        assert "send_message" in result["content"]

    @patch('webhook_server.tool_inventory.get_agent_tools_with_details')
    def test_build_no_tools(self, mock_get_tools):
        """Test build with no tools."""
        mock_get_tools.return_value = []
        
        result = build_tool_inventory_block("agent-123")
        
        assert result["success"] is False
        assert "error" in result

    @patch('webhook_server.tool_inventory.get_agent_tools_with_details')
    def test_build_with_attachment_result(self, mock_get_tools):
        """Test build with attachment result."""
        mock_get_tools.return_value = [
            {"id": "tool-new", "name": "new_tool", "description": "New tool"}
        ]
        
        attachment_result = {
            "details": {
                "successful_attachments": [
                    {"name": "new_tool", "tool_id": "tool-new", "match_score": 88.5}
                ]
            }
        }
        
        result = build_tool_inventory_block(
            "agent-123", 
            prompt="search for data",
            attachment_result=attachment_result
        )
        
        assert result["success"] is True
        # Should have recorded the attachment
        assert "agent-123" in RECENT_ATTACHMENTS
        assert len(RECENT_ATTACHMENTS["agent-123"]) == 1

    @patch('webhook_server.tool_inventory.get_agent_tools_with_details')
    def test_build_handles_error(self, mock_get_tools):
        """Test error handling during build."""
        mock_get_tools.side_effect = Exception("API error")
        
        result = build_tool_inventory_block("agent-123")
        
        assert result["success"] is False
        assert "error" in result
        assert "API error" in result["error"]


class TestToolInventoryIntegration:
    """Integration tests for tool inventory workflow."""

    def setup_method(self):
        """Clear attachments before each test."""
        RECENT_ATTACHMENTS.clear()

    @patch('webhook_server.tool_inventory.get_agent_tools_with_details')
    def test_full_workflow(self, mock_get_tools):
        """Test complete workflow from attachment to inventory."""
        # Simulate tools returned by API
        mock_get_tools.return_value = [
            {"id": "tool-1", "name": "send_message", "description": "Send a message"},
            {"id": "tool-2", "name": "searxng_search", "description": "Web search",
             "metadata_": {"mcp": {"server_name": "Searxng"}}},
            {"id": "tool-3", "name": "huly_list", "description": "List issues",
             "mcp_server_name": "huly"},
            {"id": "tool-new", "name": "newly_attached", "description": "Just attached"}
        ]
        
        # Simulate attachment result
        attachment_result = {
            "details": {
                "successful_attachments": [
                    {"name": "newly_attached", "tool_id": "tool-new", "match_score": 92.0}
                ]
            }
        }
        
        result = build_tool_inventory_block(
            "agent-test",
            prompt="find project issues",
            attachment_result=attachment_result
        )
        
        assert result["success"] is True
        content = result["content"]
        
        # Should have all categories
        assert "Core" in content
        assert "Web Search" in content
        assert "Project Management" in content
        
        # Should show recent attachment
        assert "Recently Attached" in content
        assert "newly_attached" in content
        
        # Should show tool count
        assert "4 total" in content
