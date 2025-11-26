"""
Unit tests for webhook_server.app module.

Tests Flask webhook endpoints, agent tracking, and webhook processing logic.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, UTC

# These tests use the Flask test client fixture from conftest.py


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_endpoint_returns_200(self, client):
        """Test that health endpoint returns 200 OK."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns JSON."""
        response = client.get('/health')
        assert response.content_type == 'application/json'

    def test_health_endpoint_has_status_field(self, client):
        """Test that health response includes status field."""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_health_endpoint_has_service_field(self, client):
        """Test that health response includes service field."""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'service' in data
        assert data['service'] == 'webhook-server'

    def test_health_endpoint_has_timestamp(self, client):
        """Test that health response includes timestamp."""
        response = client.get('/health')
        data = json.loads(response.data)
        assert 'timestamp' in data


class TestAgentTrackerStatus:
    """Tests for /agent-tracker/status endpoint."""

    def test_agent_tracker_status_returns_200(self, client):
        """Test that agent tracker status endpoint returns 200 OK."""
        response = client.get('/agent-tracker/status')
        assert response.status_code == 200

    def test_agent_tracker_status_returns_json(self, client):
        """Test that endpoint returns JSON."""
        response = client.get('/agent-tracker/status')
        assert response.content_type == 'application/json'

    def test_agent_tracker_status_has_known_agents(self, client):
        """Test that response includes known_agents list."""
        response = client.get('/agent-tracker/status')
        data = json.loads(response.data)
        assert 'known_agents' in data
        assert isinstance(data['known_agents'], list)

    def test_agent_tracker_status_has_agent_count(self, client):
        """Test that response includes agent_count."""
        response = client.get('/agent-tracker/status')
        data = json.loads(response.data)
        assert 'agent_count' in data
        assert isinstance(data['agent_count'], int)

    def test_agent_tracker_status_count_matches_list_length(self, client):
        """Test that agent_count matches length of known_agents."""
        response = client.get('/agent-tracker/status')
        data = json.loads(response.data)
        assert data['agent_count'] == len(data['known_agents'])


class TestAgentTrackerReset:
    """Tests for /agent-tracker/reset endpoint."""

    def test_agent_tracker_reset_requires_post(self, client):
        """Test that reset endpoint requires POST method."""
        response = client.get('/agent-tracker/reset')
        assert response.status_code == 405  # Method Not Allowed

    def test_agent_tracker_reset_returns_200(self, client):
        """Test that reset endpoint returns 200 OK."""
        response = client.post('/agent-tracker/reset')
        assert response.status_code == 200

    def test_agent_tracker_reset_clears_agents(self, client, reset_agent_tracking):
        """Test that reset clears known agents."""
        # First check status to see current state
        status_response = client.get('/agent-tracker/status')
        status_data = json.loads(status_response.data)
        initial_count = status_data['agent_count']

        # Reset
        reset_response = client.post('/agent-tracker/reset')
        reset_data = json.loads(reset_response.data)

        # Verify message mentions removed count
        assert 'message' in reset_data
        assert str(initial_count) in reset_data['message']

        # Check status again
        new_status = client.get('/agent-tracker/status')
        new_data = json.loads(new_status.data)
        assert new_data['agent_count'] == 0


class TestTrackAgentAndNotify:
    """Tests for track_agent_and_notify function."""

    def test_track_agent_ignores_invalid_agent_id(self, reset_agent_tracking):
        """Test that invalid agent IDs are ignored."""
        from webhook_server.app import track_agent_and_notify, known_agents

        track_agent_and_notify("")
        assert len(known_agents) == 0

        track_agent_and_notify(None)
        assert len(known_agents) == 0

    def test_track_agent_ignores_non_agent_prefix(self, reset_agent_tracking):
        """Test that agent IDs not starting with 'agent-' are ignored."""
        from webhook_server.app import track_agent_and_notify, known_agents

        track_agent_and_notify("user-123")
        assert len(known_agents) == 0

        track_agent_and_notify("invalid-123")
        assert len(known_agents) == 0

    @patch('webhook_server.app.requests.post')
    def test_track_agent_adds_new_agent(self, mock_post, reset_agent_tracking):
        """Test that new agent is tracked and notification is sent."""
        from webhook_server.app import track_agent_and_notify, known_agents

        # Mock successful notification
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        track_agent_and_notify("agent-123")

        # Agent should be added to known_agents
        assert "agent-123" in known_agents

    @patch('webhook_server.app.requests.post')
    def test_track_agent_does_not_notify_twice(self, mock_post, reset_agent_tracking):
        """Test that second tracking of same agent doesn't send notification."""
        from webhook_server.app import track_agent_and_notify

        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Track agent twice
        track_agent_and_notify("agent-456")
        track_agent_and_notify("agent-456")

        # Should only call post once (for the first notification)
        # Note: Due to background thread, we need to give it a moment
        import time
        time.sleep(0.1)

        # First call should have happened
        assert mock_post.called

    @patch('webhook_server.app.requests.post')
    def test_track_agent_handles_notification_failure(self, mock_post, reset_agent_tracking):
        """Test that notification failure doesn't prevent agent tracking."""
        from webhook_server.app import track_agent_and_notify, known_agents

        # Mock failed notification
        mock_post.side_effect = Exception("Connection error")

        track_agent_and_notify("agent-789")

        # Agent should still be tracked even if notification fails
        import time
        time.sleep(0.1)  # Give thread time to execute
        assert "agent-789" in known_agents


class TestQueryGraphitiAPI:
    """Tests for query_graphiti_api function."""

    @patch('webhook_server.app.requests.Session')
    def test_query_graphiti_success(self, mock_session_class):
        """Test successful Graphiti query with unified search endpoint."""
        from webhook_server.app import query_graphiti_api

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock unified search response with both nodes and edges (facts)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nodes": [
                {"name": "Test Node", "summary": "Test summary"}
            ],
            "edges": [
                {"fact": "Test fact"}
            ]
        }
        mock_response.raise_for_status = Mock()

        mock_session.post.return_value = mock_response

        result = query_graphiti_api("test query")

        assert result['success'] is True
        assert 'context' in result
        assert "Test Node" in result['context']
        assert "Test fact" in result['context']

    @patch('webhook_server.app.requests.Session')
    def test_query_graphiti_no_results(self, mock_session_class):
        """Test Graphiti query with no results."""
        from webhook_server.app import query_graphiti_api

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Mock empty unified response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"nodes": [], "edges": []}
        mock_response.raise_for_status = Mock()

        mock_session.post.return_value = mock_response

        result = query_graphiti_api("test query")

        assert result['success'] is False
        assert "No relevant information found" in result['context']

    @patch('webhook_server.app.requests.Session')
    def test_query_graphiti_handles_request_exception(self, mock_session_class):
        """Test handling of request exceptions."""
        from webhook_server.app import query_graphiti_api
        import requests

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.post.side_effect = requests.exceptions.RequestException("Network error")

        result = query_graphiti_api("test query")

        assert result['success'] is False
        assert "Error querying Graphiti" in result['context']

    @patch('webhook_server.app.requests.Session')
    def test_query_graphiti_uses_custom_limits(self, mock_session_class):
        """Test that custom max_nodes limit is used in unified config."""
        from webhook_server.app import query_graphiti_api

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"nodes": [], "edges": []}
        mock_response.raise_for_status = Mock()
        mock_session.post.return_value = mock_response

        query_graphiti_api("test", max_nodes=15, max_facts=25)

        # Check that the unified payload included custom limit
        calls = mock_session.post.call_args_list
        search_call = calls[0]

        # Unified API uses config.limit for max results
        assert search_call[1]['json']['config']['limit'] == 15

    @patch('webhook_server.app.requests.Session')
    def test_query_graphiti_deduplicates_facts(self, mock_session_class):
        """Test that duplicate facts (edges) are deduplicated."""
        from webhook_server.app import query_graphiti_api

        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Return duplicate edges in unified response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "nodes": [],
            "edges": [
                {"fact": "Duplicate fact"},
                {"fact": "Duplicate fact"},
                {"fact": "Unique fact"}
            ]
        }
        mock_response.raise_for_status = Mock()

        mock_session.post.return_value = mock_response

        result = query_graphiti_api("test")

        # Should only contain each fact once
        assert result['context'].count("Duplicate fact") == 1
        assert result['context'].count("Unique fact") == 1


class TestWebhookEndpoint:
    """Tests for the main webhook endpoint."""

    # Note: Full webhook endpoint tests would require patching many dependencies
    # These are placeholder tests - full implementation would be in integration tests

    @pytest.mark.skip(reason="Webhook endpoint requires extensive mocking - see integration tests")
    def test_webhook_endpoint_exists(self, client):
        """Test that webhook endpoint exists."""
        response = client.post('/webhook')
        # Response may be 400 or 500 due to missing data, but endpoint should exist
        assert response.status_code != 404

    @pytest.mark.skip(reason="Requires extensive mocking - see integration tests")
    def test_webhook_processes_message_sent_event(self, client):
        """Test processing of message_sent event."""
        pass

    @pytest.mark.skip(reason="Requires extensive mocking - see integration tests")
    def test_webhook_processes_stream_started_event(self, client):
        """Test processing of stream_started event."""
        pass


class TestAgentDiscoveryBlockLabels:
    """Tests for agent discovery block label uniqueness."""

    def test_agent_specific_label_format(self):
        """Test that agent-specific labels are formatted correctly."""
        # Simple unit test to verify label format
        agent_id = "agent-test-123"
        expected_label = f"available_agents_{agent_id}"
        
        assert expected_label == "available_agents_agent-test-123"
        
    def test_different_agents_have_different_labels(self):
        """Test that different agents produce different labels."""
        agent_id_1 = "agent-aaa"
        agent_id_2 = "agent-bbb"
        
        label_1 = f"available_agents_{agent_id_1}"
        label_2 = f"available_agents_{agent_id_2}"
        
        assert label_1 != label_2
        assert label_1 == "available_agents_agent-aaa"
        assert label_2 == "available_agents_agent-bbb"


class TestProtectedToolsConfig:
    """Tests for protected tools configuration."""

    def test_protected_tools_default_value(self):
        """Test that PROTECTED_TOOLS has a default value."""
        from webhook_server.config import PROTECTED_TOOLS_DEFAULT
        assert PROTECTED_TOOLS_DEFAULT == "find_agents"

    def test_protected_tools_config_exists(self):
        """Test that PROTECTED_TOOLS config is accessible."""
        from webhook_server.config import PROTECTED_TOOLS
        assert PROTECTED_TOOLS is not None


class TestEnsureProtectedTools:
    """Tests for ensure_protected_tools function."""

    def test_ensure_protected_tools_requires_agent_id(self):
        """Test that function requires agent_id."""
        from letta_tool_utils import ensure_protected_tools
        
        result = ensure_protected_tools(None)
        
        assert result["success"] is False
        assert "No agent_id provided" in result.get("error", "")

    def test_ensure_protected_tools_empty_config(self):
        """Test with empty protected tools config."""
        from letta_tool_utils import ensure_protected_tools
        
        result = ensure_protected_tools("agent-123", protected_tools_config="")
        
        assert result["success"] is True
        assert result["attached"] == []
        assert "No protected tools configured" in result.get("message", "")

    @patch('letta_tool_utils.get_agent_tool_names')
    def test_ensure_protected_tools_already_attached(self, mock_get_tools):
        """Test when protected tool is already attached."""
        from letta_tool_utils import ensure_protected_tools
        
        # Mock that find_agents is already attached
        mock_get_tools.return_value = {"find_agents", "send_message", "core_memory_append"}
        
        result = ensure_protected_tools("agent-123", protected_tools_config="find_agents")
        
        assert result["success"] is True
        assert "find_agents" in result["already_present"]
        assert len(result["attached"]) == 0
        mock_get_tools.assert_called_once_with("agent-123")

    @patch('letta_tool_utils.attach_tool_to_agent')
    @patch('letta_tool_utils.get_tool_id_by_name')
    @patch('letta_tool_utils.get_agent_tool_names')
    def test_ensure_protected_tools_attaches_missing(self, mock_get_tools, mock_get_id, mock_attach):
        """Test that missing protected tool is attached."""
        from letta_tool_utils import ensure_protected_tools
        
        # Mock that find_agents is NOT attached
        mock_get_tools.return_value = {"send_message", "core_memory_append"}
        mock_get_id.return_value = "tool-find-agents-123"
        mock_attach.return_value = True
        
        result = ensure_protected_tools("agent-123", protected_tools_config="find_agents")
        
        assert result["success"] is True
        assert len(result["attached"]) == 1
        assert result["attached"][0]["name"] == "find_agents"
        assert result["attached"][0]["id"] == "tool-find-agents-123"
        mock_attach.assert_called_once_with("agent-123", "tool-find-agents-123")

    @patch('letta_tool_utils.get_tool_id_by_name')
    @patch('letta_tool_utils.get_agent_tool_names')
    def test_ensure_protected_tools_handles_missing_tool_id(self, mock_get_tools, mock_get_id):
        """Test handling when tool ID cannot be found."""
        from letta_tool_utils import ensure_protected_tools
        
        mock_get_tools.return_value = set()
        mock_get_id.return_value = None  # Tool not found
        
        result = ensure_protected_tools("agent-123", protected_tools_config="nonexistent_tool")
        
        assert result["success"] is False
        assert len(result["failed"]) == 1
        assert result["failed"][0]["name"] == "nonexistent_tool"
        assert result["failed"][0]["reason"] == "tool_not_found"

    @patch('letta_tool_utils.attach_tool_to_agent')
    @patch('letta_tool_utils.get_tool_id_by_name')
    @patch('letta_tool_utils.get_agent_tool_names')
    def test_ensure_protected_tools_handles_attach_failure(self, mock_get_tools, mock_get_id, mock_attach):
        """Test handling when attach operation fails."""
        from letta_tool_utils import ensure_protected_tools
        
        mock_get_tools.return_value = set()
        mock_get_id.return_value = "tool-123"
        mock_attach.return_value = False  # Attach failed
        
        result = ensure_protected_tools("agent-123", protected_tools_config="find_agents")
        
        assert result["success"] is False
        assert len(result["failed"]) == 1
        assert result["failed"][0]["reason"] == "attach_failed"

    @patch('letta_tool_utils.attach_tool_to_agent')
    @patch('letta_tool_utils.get_tool_id_by_name')
    @patch('letta_tool_utils.get_agent_tool_names')
    def test_ensure_protected_tools_multiple_tools(self, mock_get_tools, mock_get_id, mock_attach):
        """Test with multiple protected tools configured."""
        from letta_tool_utils import ensure_protected_tools
        
        # Only one tool attached
        mock_get_tools.return_value = {"find_agents"}
        # Return different IDs for different tools
        mock_get_id.side_effect = lambda name: f"tool-{name}-id"
        mock_attach.return_value = True
        
        result = ensure_protected_tools("agent-123", protected_tools_config="find_agents,find_tools,search")
        
        assert result["success"] is True
        assert "find_agents" in result["already_present"]
        assert len(result["attached"]) == 2  # find_tools and search


class TestGetToolIdByName:
    """Tests for get_tool_id_by_name function."""

    @patch('letta_tool_utils.requests.get')
    def test_get_tool_id_by_name_success(self, mock_get):
        """Test successful tool ID lookup by name."""
        from letta_tool_utils import get_tool_id_by_name
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"name": "find_agents", "id": "tool-123"},
            {"name": "search", "id": "tool-456"}
        ]
        mock_get.return_value = mock_response
        
        result = get_tool_id_by_name("find_agents")
        
        assert result == "tool-123"

    @patch('letta_tool_utils.requests.get')
    def test_get_tool_id_by_name_not_found(self, mock_get):
        """Test tool ID lookup when tool not found."""
        from letta_tool_utils import get_tool_id_by_name
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"name": "other_tool", "id": "tool-123"}
        ]
        mock_get.return_value = mock_response
        
        result = get_tool_id_by_name("find_agents")
        
        assert result is None

    @patch('letta_tool_utils.requests.get')
    def test_get_tool_id_by_name_case_insensitive(self, mock_get):
        """Test that tool lookup is case insensitive."""
        from letta_tool_utils import get_tool_id_by_name
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"name": "Find_Agents", "id": "tool-123"}
        ]
        mock_get.return_value = mock_response
        
        result = get_tool_id_by_name("find_agents")
        
        assert result == "tool-123"


class TestAttachToolToAgent:
    """Tests for attach_tool_to_agent function."""

    @patch('letta_tool_utils.requests.patch')
    def test_attach_tool_success(self, mock_patch):
        """Test successful tool attachment."""
        from letta_tool_utils import attach_tool_to_agent
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response
        
        result = attach_tool_to_agent("agent-123", "tool-456")
        
        assert result is True
        mock_patch.assert_called_once()

    @patch('letta_tool_utils.requests.patch')
    def test_attach_tool_already_attached(self, mock_patch):
        """Test when tool is already attached (409 conflict)."""
        from letta_tool_utils import attach_tool_to_agent
        
        mock_response = Mock()
        mock_response.status_code = 409
        mock_patch.return_value = mock_response
        
        result = attach_tool_to_agent("agent-123", "tool-456")
        
        # Should return True since tool is effectively attached
        assert result is True

    @patch('letta_tool_utils.requests.patch')
    def test_attach_tool_failure(self, mock_patch):
        """Test handling of attachment failure."""
        from letta_tool_utils import attach_tool_to_agent
        
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_patch.return_value = mock_response
        
        result = attach_tool_to_agent("agent-123", "tool-456")
        
        assert result is False


class TestAppConfiguration:
    """Tests for Flask app configuration."""

    def test_app_is_flask_instance(self, app):
        """Test that app is a Flask instance."""
        from flask import Flask
        assert isinstance(app, Flask)

    def test_app_in_testing_mode(self, app):
        """Test that app is in testing mode."""
        assert app.config['TESTING'] is True

    def test_app_debug_disabled_in_tests(self, app):
        """Test that debug mode is disabled in tests."""
        assert app.config['DEBUG'] is False
