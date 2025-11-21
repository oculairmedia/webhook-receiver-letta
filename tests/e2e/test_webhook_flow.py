"""
End-to-end tests for complete webhook processing flow.

These tests verify the entire webhook processing pipeline from receiving
a webhook to generating context, attaching tools, and updating memory blocks.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import responses
from datetime import datetime, UTC


@pytest.mark.e2e
class TestCompleteWebhookFlow:
    """End-to-end tests for complete webhook processing."""

    @pytest.mark.skip(reason="E2E test requires full environment setup")
    @responses.activate
    @patch('webhook_server.app.find_attach_tools')
    @patch('webhook_server.app.create_memory_block')
    @patch('webhook_server.app.query_graphiti_api')
    def test_complete_stream_started_flow(
        self,
        mock_graphiti,
        mock_create_block,
        mock_attach_tools,
        client
    ):
        """
        Test complete flow for stream_started event:
        1. Receive webhook
        2. Extract prompt
        3. Query Graphiti
        4. Create/update memory block
        5. Attach relevant tools
        6. Return success response
        """
        # Mock Graphiti response
        mock_graphiti.return_value = {
            "success": True,
            "context": "Relevant context from knowledge graph"
        }

        # Mock memory block creation
        mock_create_block.return_value = {
            "id": "block-123",
            "label": "cumulative_context",
            "value": "Context with knowledge"
        }

        # Mock tool attachment
        mock_attach_tools.return_value = "Tools updated successfully"

        # Send webhook
        webhook_payload = {
            "event_type": "stream_started",
            "agent_id": "agent-test-123",
            "data": {
                "prompt": "Tell me about quantum computing"
            }
        }

        response = client.post(
            '/webhook',
            data=json.dumps(webhook_payload),
            content_type='application/json'
        )

        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data.get('status') == 'success' or 'received' in data.get('message', '').lower()

        # Verify all steps were called
        mock_graphiti.assert_called_once()
        mock_create_block.assert_called_once()
        mock_attach_tools.assert_called()

    @pytest.mark.skip(reason="E2E test requires full environment setup")
    @responses.activate
    @patch('webhook_server.app.arxiv_integration')
    @patch('webhook_server.app.create_memory_block')
    def test_arxiv_integration_flow(
        self,
        mock_create_block,
        mock_arxiv,
        client
    ):
        """
        Test flow with arXiv integration:
        1. Detect arXiv-related prompt
        2. Query arXiv for papers
        3. Include papers in context
        4. Update memory block
        """
        # Mock arXiv response
        mock_arxiv.return_value = {
            "success": True,
            "papers": [
                {
                    "title": "Quantum Computing Advances",
                    "authors": ["Smith, J.", "Doe, A."],
                    "summary": "Recent advances in quantum computing"
                }
            ]
        }

        mock_create_block.return_value = {
            "id": "block-456",
            "value": "Context with arXiv papers"
        }

        webhook_payload = {
            "event_type": "stream_started",
            "agent_id": "agent-test-456",
            "data": {
                "prompt": "Find recent papers on arxiv about quantum computing"
            }
        }

        response = client.post(
            '/webhook',
            data=json.dumps(webhook_payload),
            content_type='application/json'
        )

        assert response.status_code in [200, 201]


@pytest.mark.e2e
class TestWebhookPerformance:
    """Performance benchmarks for webhook processing."""

    @pytest.mark.benchmark
    @pytest.mark.skip(reason="Performance test - run separately")
    def test_webhook_response_time_under_3_seconds(self, client, benchmark):
        """Test that webhook processing completes within 3 seconds."""
        webhook_payload = {
            "event_type": "stream_started",
            "agent_id": "agent-perf-test",
            "data": {
                "prompt": "Performance test query"
            }
        }

        def send_webhook():
            return client.post(
                '/webhook',
                data=json.dumps(webhook_payload),
                content_type='application/json'
            )

        result = benchmark(send_webhook)

        # Assert response time is under 3 seconds
        assert benchmark.stats.mean < 3.0


@pytest.mark.e2e
class TestAgentTrackingFlow:
    """E2E tests for agent tracking and notifications."""

    @patch('webhook_server.app.requests.post')
    def test_new_agent_triggers_notification(self, mock_post, client, reset_agent_tracking):
        """Test that detecting a new agent triggers Matrix notification."""
        # Mock Matrix client response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # First, check agent tracker status
        status_before = client.get('/agent-tracker/status')
        data_before = json.loads(status_before.data)
        initial_count = data_before['agent_count']

        # Simulate new agent detection (this would normally happen via webhook)
        from webhook_server.app import track_agent_and_notify
        track_agent_and_notify("agent-new-789")

        # Give background thread time to execute
        import time
        time.sleep(0.2)

        # Check agent tracker status again
        status_after = client.get('/agent-tracker/status')
        data_after = json.loads(status_after.data)

        assert data_after['agent_count'] == initial_count + 1
        assert "agent-new-789" in data_after['known_agents']


@pytest.mark.e2e
class TestErrorRecovery:
    """E2E tests for error recovery and resilience."""

    @pytest.mark.skip(reason="E2E test requires full environment setup")
    @patch('webhook_server.app.query_graphiti_api')
    @patch('webhook_server.app.create_memory_block')
    def test_continues_on_graphiti_failure(
        self,
        mock_create_block,
        mock_graphiti,
        client
    ):
        """Test that webhook processing continues even if Graphiti fails."""
        # Mock Graphiti failure
        mock_graphiti.return_value = {
            "success": False,
            "context": "Error querying Graphiti"
        }

        # Memory block should still be created
        mock_create_block.return_value = {"id": "block-123"}

        webhook_payload = {
            "event_type": "stream_started",
            "agent_id": "agent-test-recovery",
            "data": {
                "prompt": "Test query"
            }
        }

        response = client.post(
            '/webhook',
            data=json.dumps(webhook_payload),
            content_type='application/json'
        )

        # Should still return 200 even if Graphiti failed
        assert response.status_code in [200, 201]
        # Memory block creation should still be attempted
        mock_create_block.assert_called()


@pytest.mark.e2e
class TestWebhookValidation:
    """E2E tests for webhook payload validation."""

    @pytest.mark.skip(reason="Validation behavior depends on implementation")
    def test_rejects_malformed_webhook(self, client):
        """Test that malformed webhooks are rejected."""
        malformed_payload = {
            "invalid_field": "value"
            # Missing required fields
        }

        response = client.post(
            '/webhook',
            data=json.dumps(malformed_payload),
            content_type='application/json'
        )

        assert response.status_code in [400, 422, 500]

    @pytest.mark.skip(reason="Validation behavior depends on implementation")
    def test_rejects_empty_webhook(self, client):
        """Test that empty webhooks are rejected."""
        response = client.post(
            '/webhook',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code in [400, 422, 500]
