"""
Pytest configuration and shared fixtures for Letta Webhook Receiver tests.

This module provides common fixtures, test utilities, and configuration
that can be used across all test modules.
"""

import pytest
import os
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, UTC
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webhook_server import app as flask_app
from webhook_server.config import (
    LETTA_BASE_URL,
    LETTA_PASSWORD,
    GRAPHITI_API_URL,
    GRAPHITI_MAX_NODES,
    GRAPHITI_MAX_FACTS
)


# ============================================================================
# Environment and Configuration Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_env_vars():
    """Set up test environment variables."""
    original_env = os.environ.copy()

    # Set test environment variables
    test_vars = {
        "LETTA_BASE_URL": "http://test-letta.example.com",
        "LETTA_PASSWORD": "test_password_123",
        "GRAPHITI_URL": "http://test-graphiti.example.com:8003",
        "GRAPHITI_MAX_NODES": "5",
        "GRAPHITI_MAX_FACTS": "15",
        "MATRIX_CLIENT_URL": "http://test-matrix.example.com:8004",
        "EXTERNAL_QUERY_ENABLED": "true",
        "QUERY_REFINEMENT_ENABLED": "true"
    }

    os.environ.update(test_vars)

    yield test_vars

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_config():
    """Mock configuration values for testing."""
    return {
        "letta_base_url": "http://test-letta.example.com",
        "letta_password": "test_password_123",
        "graphiti_url": "http://test-graphiti.example.com:8003",
        "graphiti_max_nodes": 5,
        "graphiti_max_facts": 15,
        "matrix_client_url": "http://test-matrix.example.com:8004"
    }


# ============================================================================
# Flask Application Fixtures
# ============================================================================

@pytest.fixture
def app():
    """Create Flask app instance for testing."""
    flask_app.app.config.update({
        "TESTING": True,
        "DEBUG": False,
    })
    return flask_app.app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create Flask CLI test runner."""
    return app.test_cli_runner()


# ============================================================================
# Mock HTTP Response Fixtures
# ============================================================================

@pytest.fixture
def mock_graphiti_response():
    """Mock successful Graphiti API response."""
    return {
        "nodes": [
            {
                "name": "Test Node 1",
                "summary": "This is a test node about AI research",
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "name": "Test Node 2",
                "summary": "Another test node about machine learning",
                "created_at": "2024-01-16T14:20:00Z"
            }
        ],
        "edges": [
            {
                "source": "node_1",
                "target": "node_2",
                "fact": "Test Node 1 is related to Test Node 2",
                "created_at": "2024-01-17T09:15:00Z"
            }
        ]
    }


@pytest.fixture
def mock_graphiti_empty_response():
    """Mock empty Graphiti API response (no results)."""
    return {
        "nodes": [],
        "edges": []
    }


@pytest.fixture
def mock_letta_agent_response():
    """Mock Letta agent details response."""
    return {
        "id": "agent-test-12345",
        "name": "Test Agent",
        "description": "A test agent for unit testing",
        "memory": {
            "human": "Test user",
            "persona": "Test assistant"
        },
        "created_at": "2024-01-15T10:00:00Z"
    }


@pytest.fixture
def mock_letta_memory_block():
    """Mock Letta memory block response."""
    return {
        "id": "block-test-67890",
        "label": "cumulative_context",
        "value": "Previous context from knowledge graph",
        "limit": 6000,
        "created_at": "2024-01-15T10:00:00Z"
    }


@pytest.fixture
def mock_tool_discovery_response():
    """Mock tool discovery API response."""
    return {
        "tools": [
            {
                "id": "tool-arxiv-search",
                "name": "arxiv_search",
                "description": "Search arXiv for research papers",
                "tags": ["arxiv", "research", "papers"]
            },
            {
                "id": "tool-web-search",
                "name": "web_search",
                "description": "Search the web for information",
                "tags": ["web", "search"]
            }
        ]
    }


# ============================================================================
# Webhook Payload Fixtures
# ============================================================================

@pytest.fixture
def webhook_payload_message_sent():
    """Sample webhook payload for message_sent event."""
    return {
        "event_type": "message_sent",
        "agent_id": "agent-test-12345",
        "user_id": "user-test-67890",
        "data": {
            "message": {
                "role": "user",
                "text": "Tell me about quantum computing and its applications in cryptography"
            }
        },
        "timestamp": datetime.now(UTC).isoformat()
    }


@pytest.fixture
def webhook_payload_stream_started():
    """Sample webhook payload for stream_started event with prompt."""
    return {
        "event_type": "stream_started",
        "agent_id": "agent-test-12345",
        "user_id": "user-test-67890",
        "data": {
            "prompt": "Research the latest developments in quantum computing",
            "messages": [
                {
                    "role": "user",
                    "text": "What are the latest quantum computing developments?"
                }
            ]
        },
        "timestamp": datetime.now(UTC).isoformat()
    }


@pytest.fixture
def webhook_payload_list_prompt():
    """Webhook payload with prompt as a list (common format)."""
    return {
        "event_type": "stream_started",
        "agent_id": "agent-test-99999",
        "data": {
            "prompt": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Search for papers about neural networks on arXiv"}
            ]
        }
    }


@pytest.fixture
def webhook_payload_empty():
    """Empty webhook payload for error handling tests."""
    return {}


@pytest.fixture
def webhook_payload_malformed():
    """Malformed webhook payload for error handling tests."""
    return {
        "event_type": "unknown_event",
        # Missing agent_id
        "data": None
    }


# ============================================================================
# Mock External Service Fixtures
# ============================================================================

@pytest.fixture
def mock_requests_session():
    """Mock requests.Session for HTTP calls."""
    session = Mock()
    session.get = Mock()
    session.post = Mock()
    session.put = Mock()
    session.delete = Mock()
    return session


@pytest.fixture
def mock_graphiti_api(mock_graphiti_response):
    """Mock the Graphiti API client."""
    with patch('webhook_server.app.query_graphiti_api') as mock:
        mock.return_value = mock_graphiti_response
        yield mock


@pytest.fixture
def mock_letta_api():
    """Mock the Letta API client."""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post, \
         patch('requests.put') as mock_put:

        # Configure default responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "success"}

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "success"}

        mock_put.return_value.status_code = 200
        mock_put.return_value.json.return_value = {"status": "success"}

        yield {
            'get': mock_get,
            'post': mock_post,
            'put': mock_put
        }


@pytest.fixture
def mock_matrix_client():
    """Mock Matrix client for notifications."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "notified"}
        yield mock_post


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_context_entries():
    """Sample context entries for testing context building."""
    return [
        {
            "type": "node",
            "content": "Quantum computing uses quantum mechanics for computation",
            "timestamp": "2024-01-15T10:00:00Z",
            "source": "Test Node 1"
        },
        {
            "type": "fact",
            "content": "Quantum computers can break RSA encryption",
            "timestamp": "2024-01-15T11:00:00Z",
            "source": "Edge between Node 1 and Node 2"
        },
        {
            "type": "node",
            "content": "Post-quantum cryptography is being developed",
            "timestamp": "2024-01-15T12:00:00Z",
            "source": "Test Node 3"
        }
    ]


@pytest.fixture
def sample_memory_blocks():
    """Sample memory blocks for testing."""
    return [
        {
            "id": "block-1",
            "label": "cumulative_context",
            "value": "Previous context about quantum computing",
            "limit": 6000
        },
        {
            "id": "block-2",
            "label": "human",
            "value": "User is interested in quantum computing",
            "limit": 2000
        }
    ]


@pytest.fixture
def sample_tools():
    """Sample tools for testing tool attachment."""
    return [
        {
            "id": "tool-arxiv-search",
            "name": "arxiv_search",
            "description": "Search arXiv for research papers",
            "tags": ["arxiv", "research"]
        },
        {
            "id": "tool-web-search",
            "name": "web_search",
            "description": "Search the web",
            "tags": ["web"]
        },
        {
            "id": "tool-calculator",
            "name": "calculator",
            "description": "Perform calculations",
            "tags": ["math"]
        }
    ]


# ============================================================================
# Helper Functions
# ============================================================================

@pytest.fixture
def make_api_url():
    """Helper to construct API URLs for testing."""
    def _make_url(base_url, path):
        return f"{base_url.rstrip('/')}/v1/{path.lstrip('/')}"
    return _make_url


@pytest.fixture
def create_mock_response():
    """Helper to create mock HTTP responses."""
    def _create(status_code=200, json_data=None, text=None):
        response = Mock()
        response.status_code = status_code
        response.ok = 200 <= status_code < 300
        response.json = Mock(return_value=json_data if json_data is not None else {})
        response.text = text or json.dumps(json_data) if json_data else ""
        response.raise_for_status = Mock()
        if not response.ok:
            response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
        return response
    return _create


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def reset_agent_tracking():
    """Reset agent tracking state before each test."""
    from webhook_server.app import known_agents
    known_agents.clear()
    yield
    known_agents.clear()


@pytest.fixture(autouse=True)
def cleanup_environment():
    """Cleanup environment after each test."""
    yield
    # Any cleanup code can go here
