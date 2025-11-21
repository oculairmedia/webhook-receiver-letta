"""
Performance benchmark tests for Letta Webhook Receiver.

These tests measure performance of critical operations to ensure
they meet required latency targets.
"""

import pytest
from unittest.mock import Mock, patch
import time

# Mark all tests in this module as performance tests
pytestmark = pytest.mark.performance


class TestContextBuildingPerformance:
    """Performance tests for context building operations."""

    @pytest.mark.benchmark
    def test_build_cumulative_context_performance(self, benchmark):
        """Test that context building completes quickly."""
        from webhook_server.context_utils import _build_cumulative_context

        existing = "Existing context " * 100
        new = "New context " * 100

        result = benchmark(_build_cumulative_context, existing, new)

        # Should complete in under 100ms
        assert benchmark.stats.mean < 0.1

    @pytest.mark.benchmark
    def test_truncate_oldest_entries_performance(self, benchmark):
        """Test that truncation completes quickly."""
        from webhook_server.context_utils import _truncate_oldest_entries

        # Create large context
        long_context = ""
        for i in range(50):
            long_context += f"\n\n--- CONTEXT ENTRY (2024-01-{i:02d} 10:00:00 UTC) ---\n\n"
            long_context += "Context entry " * 50

        result = benchmark(_truncate_oldest_entries, long_context, 4800)

        # Should complete in under 50ms
        assert benchmark.stats.mean < 0.05

    @pytest.mark.benchmark
    def test_parse_context_entries_performance(self, benchmark):
        """Test that parsing entries is efficient."""
        from webhook_server.context_utils import _parse_context_entries

        # Create context with many entries
        context = ""
        for i in range(20):
            context += f"\n\n--- CONTEXT ENTRY (2024-01-15 {i:02d}:00:00 UTC) ---\n\n"
            context += f"Entry {i} content here"

        result = benchmark(_parse_context_entries, context)

        # Should complete in under 20ms
        assert benchmark.stats.mean < 0.02


class TestSimilarityCheckPerformance:
    """Performance tests for similarity checking."""

    @pytest.mark.benchmark
    def test_similarity_check_performance(self, benchmark):
        """Test that similarity checks are fast."""
        from webhook_server.context_utils import _is_content_similar

        content1 = "Test content " * 100
        content2 = "Different content " * 100

        result = benchmark(_is_content_similar, content1, content2)

        # Should complete in under 10ms
        assert benchmark.stats.mean < 0.01

    @pytest.mark.benchmark
    def test_query_aware_similarity_performance(self, benchmark):
        """Test query-aware similarity check performance."""
        from webhook_server.context_utils import _is_content_similar_with_query_awareness

        arxiv_content1 = "**Recent Research Papers (arXiv)**\npapers relevant to: AI\n" + "Paper content " * 50
        arxiv_content2 = "**Recent Research Papers (arXiv)**\npapers relevant to: ML\n" + "Paper content " * 50

        result = benchmark(_is_content_similar_with_query_awareness, arxiv_content1, arxiv_content2)

        # Should complete in under 20ms
        assert benchmark.stats.mean < 0.02


class TestMemoryOperationsPerformance:
    """Performance tests for memory operations."""

    @pytest.mark.benchmark
    @patch('webhook_server.memory_manager.requests.post')
    @patch('webhook_server.memory_manager.find_memory_block')
    def test_create_memory_block_performance(self, mock_find, mock_post, benchmark):
        """Test memory block creation performance."""
        from webhook_server.memory_manager import create_memory_block

        mock_find.return_value = (None, False)
        mock_response = Mock()
        mock_response.json.return_value = {"id": "block-123", "label": "test"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        block_data = {"label": "test", "value": "content"}

        result = benchmark(create_memory_block, block_data)

        # Should complete in under 100ms (mocked)
        assert benchmark.stats.mean < 0.1


class TestToolManagerPerformance:
    """Performance tests for tool management."""

    @pytest.mark.benchmark
    @patch('tool_manager.requests.get')
    def test_get_agent_tools_performance(self, mock_get, benchmark):
        """Test that fetching agent tools is fast."""
        import tool_manager

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": f"tool-{i}", "name": f"tool_{i}"}
            for i in range(10)
        ]
        mock_get.return_value = mock_response

        result = benchmark(tool_manager.get_agent_tools, "agent-123")

        # Should complete in under 50ms (mocked)
        assert benchmark.stats.mean < 0.05


class TestEndToEndPerformance:
    """End-to-end performance tests."""

    @pytest.mark.slow
    @pytest.mark.skip(reason="E2E performance test - requires full environment")
    def test_webhook_processing_latency(self, client):
        """Test that complete webhook processing meets latency target."""
        webhook_payload = {
            "event_type": "stream_started",
            "agent_id": "agent-perf-test",
            "data": {
                "prompt": "Performance test query"
            }
        }

        start_time = time.time()

        response = client.post(
            '/webhook',
            json=webhook_payload
        )

        elapsed_time = time.time() - start_time

        # Should complete in under 3 seconds
        assert elapsed_time < 3.0
        assert response.status_code in [200, 201]


class TestConcurrentOperations:
    """Performance tests for concurrent operations."""

    @pytest.mark.slow
    @pytest.mark.skip(reason="Concurrency test - requires careful setup")
    def test_concurrent_context_building(self):
        """Test that concurrent context building doesn't degrade performance."""
        from webhook_server.context_utils import _build_cumulative_context
        import concurrent.futures

        existing = "Existing " * 100
        new = "New " * 100

        def build_context():
            return _build_cumulative_context(existing, new)

        start_time = time.time()

        # Run 10 concurrent context building operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(build_context) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        elapsed_time = time.time() - start_time

        # Should complete all operations in under 1 second
        assert elapsed_time < 1.0
        assert len(results) == 10


@pytest.mark.memory
class TestMemoryUsage:
    """Tests for memory usage and efficiency."""

    def test_large_context_memory_efficiency(self):
        """Test that processing large contexts doesn't consume excessive memory."""
        from webhook_server.context_utils import _build_cumulative_context
        import sys

        # Create large context
        large_existing = "Large content " * 10000
        large_new = "New content " * 1000

        # Get initial size
        initial_size = sys.getsizeof(large_existing) + sys.getsizeof(large_new)

        result = _build_cumulative_context(large_existing, large_new)

        result_size = sys.getsizeof(result)

        # Result should not be more than 2x the input size
        assert result_size < initial_size * 2

    def test_truncation_reduces_memory(self):
        """Test that truncation effectively reduces memory usage."""
        from webhook_server.context_utils import _truncate_oldest_entries
        import sys

        # Create very large context
        large_context = "X" * 100000

        initial_size = sys.getsizeof(large_context)

        truncated = _truncate_oldest_entries(large_context, 4800)

        final_size = sys.getsizeof(truncated)

        # Should be significantly smaller
        assert final_size < initial_size * 0.1
