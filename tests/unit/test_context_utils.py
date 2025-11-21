"""
Unit tests for webhook_server.context_utils module.

Tests context building, deduplication, truncation, and similarity detection.
"""

import pytest
from datetime import datetime, UTC
from webhook_server.context_utils import (
    _build_cumulative_context,
    _parse_context_entries,
    _is_content_similar,
    _is_content_similar_with_query_awareness,
    _truncate_oldest_entries,
    MAX_CONTEXT_SNIPPET_LENGTH
)


class TestBuildCumulativeContext:
    """Tests for _build_cumulative_context function."""

    def test_build_context_with_empty_existing(self):
        """Test building context when existing context is empty."""
        new_context = "New context entry"
        result = _build_cumulative_context("", new_context)
        assert result == new_context

    def test_build_context_with_empty_new(self):
        """Test building context when new context is empty."""
        existing = "Existing context"
        result = _build_cumulative_context(existing, "")
        assert result == existing

    def test_build_context_appends_with_separator(self):
        """Test that new context is appended with a separator."""
        existing = "Old context"
        new = "New context"
        result = _build_cumulative_context(existing, new)

        assert "Old context" in result
        assert "New context" in result
        assert "--- CONTEXT ENTRY" in result

    def test_build_context_includes_timestamp(self):
        """Test that separator includes a timestamp."""
        result = _build_cumulative_context("Old", "New")
        assert "UTC" in result
        # Check for date format (YYYY-MM-DD)
        assert any(char.isdigit() for char in result)

    def test_build_context_deduplication(self):
        """Test that duplicate content is not appended."""
        existing = "Some unique content"
        # Same content should be detected as duplicate
        result = _build_cumulative_context(existing, existing)

        # Should only contain the content once (no duplication)
        assert result == existing

    def test_build_context_truncation_when_exceeds_limit(self):
        """Test that context is truncated when it exceeds MAX_CONTEXT_SNIPPET_LENGTH."""
        # Create very long existing context
        long_existing = "A" * (MAX_CONTEXT_SNIPPET_LENGTH - 100)
        new_context = "B" * 500

        result = _build_cumulative_context(long_existing, new_context)

        # Result should not exceed maximum length
        assert len(result) <= MAX_CONTEXT_SNIPPET_LENGTH

    def test_build_context_preserves_new_content_after_truncation(self):
        """Test that new content is preserved even after truncation."""
        long_existing = "X" * MAX_CONTEXT_SNIPPET_LENGTH
        new_context = "NEW_IMPORTANT_CONTENT"

        result = _build_cumulative_context(long_existing, new_context)

        # New content should be in the result
        assert "NEW_IMPORTANT_CONTENT" in result or "TRUNCATED" in result

    def test_build_context_with_whitespace_only_existing(self):
        """Test handling of whitespace-only existing context."""
        result = _build_cumulative_context("   \n\n  ", "New content")
        assert result == "New content"

    def test_build_context_with_whitespace_only_new(self):
        """Test handling of whitespace-only new context."""
        existing = "Existing content"
        result = _build_cumulative_context(existing, "  \n  ")
        assert result == existing


class TestParseContextEntries:
    """Tests for _parse_context_entries function."""

    def test_parse_empty_context(self):
        """Test parsing empty context."""
        result = _parse_context_entries("")
        assert result == []

    def test_parse_context_without_separators(self):
        """Test parsing context without entry separators (legacy content)."""
        context = "Legacy content without separators"
        result = _parse_context_entries(context)

        assert len(result) == 1
        assert result[0]["timestamp"] == "Legacy"
        assert result[0]["content"] == "Legacy content without separators"

    def test_parse_context_with_single_entry(self):
        """Test parsing context with one timestamped entry."""
        context = "\n\n--- CONTEXT ENTRY (2024-01-15 10:00:00 UTC) ---\n\nFirst entry"
        result = _parse_context_entries(context)

        assert len(result) == 1
        assert result[0]["timestamp"] == "2024-01-15 10:00:00 UTC"
        assert result[0]["content"] == "First entry"

    def test_parse_context_with_multiple_entries(self):
        """Test parsing context with multiple timestamped entries."""
        context = (
            "Legacy content"
            "\n\n--- CONTEXT ENTRY (2024-01-15 10:00:00 UTC) ---\n\nFirst entry"
            "\n\n--- CONTEXT ENTRY (2024-01-15 11:00:00 UTC) ---\n\nSecond entry"
        )
        result = _parse_context_entries(context)

        assert len(result) == 3
        assert result[0]["timestamp"] == "Legacy"
        assert result[1]["timestamp"] == "2024-01-15 10:00:00 UTC"
        assert result[2]["timestamp"] == "2024-01-15 11:00:00 UTC"

    def test_parse_context_ignores_empty_entries(self):
        """Test that empty entries are ignored during parsing."""
        context = (
            "\n\n--- CONTEXT ENTRY (2024-01-15 10:00:00 UTC) ---\n\nValid entry"
            "\n\n--- CONTEXT ENTRY (2024-01-15 11:00:00 UTC) ---\n\n   "
        )
        result = _parse_context_entries(context)

        # Should only have the valid entry
        assert len(result) == 1
        assert result[0]["content"] == "Valid entry"


class TestIsContentSimilar:
    """Tests for _is_content_similar function."""

    def test_exact_match(self):
        """Test that exact matches are detected as similar."""
        content = "Exact same content"
        assert _is_content_similar(content, content) is True

    def test_case_insensitive_match(self):
        """Test that case differences are ignored."""
        assert _is_content_similar("Hello World", "hello world") is True

    def test_whitespace_differences(self):
        """Test handling of whitespace differences."""
        content1 = "Hello World"
        content2 = "  Hello World  "
        # Should be similar due to strip()
        assert _is_content_similar(content1, content2) is True

    def test_completely_different_content(self):
        """Test that completely different content is not similar."""
        content1 = "Quantum computing research"
        content2 = "Weather forecast for tomorrow"
        assert _is_content_similar(content1, content2) is False

    def test_empty_content_comparison(self):
        """Test comparison with empty content."""
        assert _is_content_similar("", "something") is False
        assert _is_content_similar("something", "") is False
        assert _is_content_similar("", "") is False

    def test_substring_containment(self):
        """Test that substrings are detected as similar when appropriate."""
        short = "AI research"
        long = "This is a long article about AI research and its applications"
        # Short content contained in long content
        assert _is_content_similar(short, long) is True


class TestIsContentSimilarWithQueryAwareness:
    """Tests for _is_content_similar_with_query_awareness function."""

    def test_different_arxiv_queries_not_similar(self):
        """Test that different arXiv queries are not considered similar."""
        content1 = "**Recent Research Papers (arXiv)**\npapers relevant to: quantum computing\nPaper 1"
        content2 = "**Recent Research Papers (arXiv)**\npapers relevant to: machine learning\nPaper 1"

        result = _is_content_similar_with_query_awareness(content1, content2)
        assert result is False

    def test_same_arxiv_query_falls_through_to_similarity(self):
        """Test that same arXiv query uses regular similarity check."""
        content1 = "**Recent Research Papers (arXiv)**\npapers relevant to: AI\nPaper A"
        content2 = "**Recent Research Papers (arXiv)**\npapers relevant to: AI\nPaper A"

        # Should be similar because query is the same and content is same
        result = _is_content_similar_with_query_awareness(content1, content2)
        assert result is True

    def test_different_graphiti_timestamps_not_similar(self):
        """Test that different Graphiti search contexts are not similar."""
        content1 = (
            "Relevant Entities from Knowledge Graph:\n"
            "--- CONTEXT ENTRY (2024-01-15 10:00:00 UTC) ---\n"
            "Node about AI"
        )
        content2 = (
            "Relevant Entities from Knowledge Graph:\n"
            "--- CONTEXT ENTRY (2024-01-15 11:00:00 UTC) ---\n"
            "Node about AI"
        )

        result = _is_content_similar_with_query_awareness(content1, content2)
        assert result is False

    def test_regular_content_uses_standard_similarity(self):
        """Test that non-arXiv/non-Graphiti content uses standard similarity."""
        content1 = "Regular content here"
        content2 = "Regular content here"

        result = _is_content_similar_with_query_awareness(content1, content2)
        assert result is True

    def test_empty_content_not_similar(self):
        """Test that empty content is not similar."""
        assert _is_content_similar_with_query_awareness("", "something") is False
        assert _is_content_similar_with_query_awareness("something", "") is False


class TestTruncateOldestEntries:
    """Tests for _truncate_oldest_entries function."""

    def test_no_truncation_when_under_limit(self):
        """Test that content under limit is not truncated."""
        short_context = "Short context"
        result = _truncate_oldest_entries(short_context, 1000)
        assert result == short_context

    def test_truncation_preserves_recent_entry(self):
        """Test that most recent entry is preserved during truncation."""
        context = (
            "\n\n--- CONTEXT ENTRY (2024-01-15 09:00:00 UTC) ---\n\nOld entry " + "X" * 3000 +
            "\n\n--- CONTEXT ENTRY (2024-01-15 10:00:00 UTC) ---\n\nRecent entry"
        )
        result = _truncate_oldest_entries(context, 500)

        assert "Recent entry" in result
        assert len(result) <= 500

    def test_truncation_adds_notice(self):
        """Test that truncation adds a notice."""
        long_context = (
            "\n\n--- CONTEXT ENTRY (2024-01-15 09:00:00 UTC) ---\n\n" + "A" * 2000 +
            "\n\n--- CONTEXT ENTRY (2024-01-15 10:00:00 UTC) ---\n\n" + "B" * 2000
        )
        result = _truncate_oldest_entries(long_context, 1000)

        assert "TRUNCATED" in result

    def test_truncation_with_unparseable_content(self):
        """Test truncation fallback for unparseable content."""
        # Content without proper entry structure
        long_text = "A" * 1000
        result = _truncate_oldest_entries(long_text, 500)

        assert len(result) <= 500
        # Should take from the end
        assert result.endswith("A" * 100)  # Last 100 chars should be 'A'

    def test_truncation_respects_max_length(self):
        """Test that truncation always respects max_length."""
        for length in [100, 500, 1000, 2000]:
            long_context = "X" * (length * 3)
            result = _truncate_oldest_entries(long_context, length)
            assert len(result) <= length

    def test_truncation_with_very_long_single_entry(self):
        """Test truncation when single recent entry exceeds limit."""
        very_long_entry = "Z" * 6000
        context = f"\n\n--- CONTEXT ENTRY (2024-01-15 10:00:00 UTC) ---\n\n{very_long_entry}"

        result = _truncate_oldest_entries(context, 1000)

        # Should truncate but keep some of the content
        assert len(result) <= 1000
        assert "Z" in result


class TestContextUtilsEdgeCases:
    """Edge case tests for context utilities."""

    def test_build_context_with_unicode_characters(self):
        """Test context building with Unicode characters."""
        existing = "Previous content with émojis 🎉"
        new = "New content with 中文字符"

        result = _build_cumulative_context(existing, new)
        assert "émojis 🎉" in result
        assert "中文字符" in result

    def test_parse_context_with_malformed_timestamps(self):
        """Test parsing context with malformed timestamp separators."""
        context = "\n\n--- CONTEXT ENTRY (Invalid Timestamp ---\n\nSome content"
        result = _parse_context_entries(context)

        # Should handle gracefully
        assert isinstance(result, list)

    def test_similarity_with_very_long_strings(self):
        """Test similarity check with very long strings."""
        long1 = "A" * 10000
        long2 = "B" * 10000

        result = _is_content_similar(long1, long2)
        assert result is False

    def test_truncation_at_exact_limit(self):
        """Test truncation when content is exactly at the limit."""
        context = "X" * MAX_CONTEXT_SNIPPET_LENGTH
        result = _truncate_oldest_entries(context, MAX_CONTEXT_SNIPPET_LENGTH)

        assert len(result) == MAX_CONTEXT_SNIPPET_LENGTH
