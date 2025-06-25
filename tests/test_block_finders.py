import unittest
from unittest.mock import patch, Mock
from webhook_server import block_finders

class TestBlockFinders(unittest.TestCase):

    @patch('requests.get')
    def test_find_memory_block_attached(self, mock_get):
        """
        Tests find_memory_block when the block is already attached to the agent.
        """
        mock_response = Mock()
        mock_response.json.return_value = {
            "blocks": [
                {"id": "block-123", "label": "graphiti_context"}
            ]
        }
        mock_get.return_value = mock_response

        block, is_attached = block_finders.find_memory_block("agent-123", "graphiti_context")
        self.assertIsNotNone(block)
        self.assertTrue(is_attached)
        self.assertEqual(block['id'], 'block-123')

    @patch('requests.get')
    def test_find_memory_block_global(self, mock_get):
        """
        Tests find_memory_block when the block is found globally but not attached.
        """
        # First call for attached blocks (returns empty)
        mock_attached_response = Mock()
        mock_attached_response.json.return_value = {"blocks": []}
        
        # Second call for global blocks (returns a block)
        mock_global_response = Mock()
        mock_global_response.json.return_value = {
            "blocks": [
                {"id": "block-456", "label": "graphiti_context"}
            ]
        }
        mock_get.side_effect = [mock_attached_response, mock_global_response]

        block, is_attached = block_finders.find_memory_block("agent-123", "graphiti_context")
        self.assertIsNotNone(block)
        self.assertFalse(is_attached)
        self.assertEqual(block['id'], 'block-456')

if __name__ == '__main__':
    unittest.main()