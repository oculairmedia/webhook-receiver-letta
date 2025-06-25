import unittest
from unittest.mock import patch, Mock
from webhook_server import memory_manager

class TestMemoryManager(unittest.TestCase):

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('requests.patch')
    def test_update_memory_block(self, mock_patch, mock_find):
        """
        Tests that update_memory_block is called when a block is found.
        """
        mock_find.return_value = ({"id": "block-123", "value": "old context"}, True)
        mock_response = Mock()
        mock_response.json.return_value = {"id": "block-123", "value": "new context"}
        mock_patch.return_value = mock_response

        block_data = {"label": "graphiti_context", "value": "new context"}
        result = memory_manager.create_memory_block(block_data, "agent-123")
        
        self.assertEqual(result['id'], 'block-123')
        self.assertEqual(result['value'], 'new context')

    @patch('webhook_server.memory_manager.find_memory_block')
    @patch('requests.post')
    def test_create_memory_block(self, mock_post, mock_find):
        """
        Tests that a new block is created when no existing block is found.
        """
        mock_find.return_value = (None, False)
        mock_response = Mock()
        mock_response.json.return_value = {"id": "new-block-456", "value": "new context"}
        mock_post.return_value = mock_response

        block_data = {"label": "graphiti_context", "value": "new context"}
        result = memory_manager.create_memory_block(block_data, "agent-123")
        
        self.assertEqual(result['id'], 'new-block-456')

if __name__ == '__main__':
    unittest.main()