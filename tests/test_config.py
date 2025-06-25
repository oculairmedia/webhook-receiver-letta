import unittest
import os
from webhook_server import config

class TestConfig(unittest.TestCase):

    def test_get_api_url(self):
        """
        Tests the get_api_url function to ensure it constructs URLs correctly.
        """
        # Test with a standard path
        path = "agents/some-agent-id/core-memory/blocks"
        expected_url = f"{config.LETTA_BASE_URL}/v1/{path}"
        self.assertEqual(config.get_api_url(path), expected_url)

        # Test with a path that has a leading slash
        path_with_slash = "/blocks"
        expected_url_for_slash = f"{config.LETTA_BASE_URL}/v1/blocks"
        self.assertEqual(config.get_api_url(path_with_slash), expected_url_for_slash)

        # Test with an empty path
        self.assertEqual(config.get_api_url(""), f"{config.LETTA_BASE_URL}/v1/")

if __name__ == '__main__':
    unittest.main()