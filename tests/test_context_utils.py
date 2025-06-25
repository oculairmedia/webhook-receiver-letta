import unittest
from webhook_server import context_utils

class TestContextUtils(unittest.TestCase):

    def test_build_cumulative_context(self):
        """
        Tests the _build_cumulative_context function.
        """
        existing_context = "This is the first entry."
        new_context = "This is the second entry."
        expected_context = "This is the first entry.\n\nThis is the second entry."
        self.assertEqual(context_utils._build_cumulative_context(existing_context, new_context), expected_context)

        # Test with an empty existing context
        self.assertEqual(context_utils._build_cumulative_context("", new_context), new_context)

        # Test with an empty new context
        self.assertEqual(context_utils._build_cumulative_context(existing_context, ""), existing_context)

    def test_parse_context_entries(self):
        """
        Tests the _parse_context_entries function.
        """
        context = "Entry 1\n\nEntry 2"
        expected_entries = [{"content": "Entry 1"}, {"content": "Entry 2"}]
        self.assertEqual(context_utils._parse_context_entries(context), expected_entries)

    def test_is_content_similar(self):
        """
        Tests the _is_content_similar function.
        """
        self.assertTrue(context_utils._is_content_similar("  hello  ", "hello"))
        self.assertFalse(context_utils._is_content_similar("hello", "world"))

    def test_truncate_oldest_entries(self):
        """
        Tests the _truncate_oldest_entries function.
        """
        context = "Old entry.\n\nNew entry."
        self.assertEqual(context_utils._truncate_oldest_entries(context, 15), "New entry.")
        self.assertEqual(context_utils._truncate_oldest_entries(context, 100), context)

if __name__ == '__main__':
    unittest.main()