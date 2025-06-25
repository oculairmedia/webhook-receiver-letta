import unittest
import json
from unittest.mock import patch
from webhook_server.app import app

class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('webhook_server.app.generate_context_from_prompt')
    @patch('webhook_server.app.create_memory_block')
    def test_webhook_receiver_success(self, mock_create_block, mock_generate_context):
        """
        Tests the webhook receiver with a successful request.
        """
        mock_generate_context.return_value = {"context": "Generated context"}
        mock_create_block.return_value = {"status": "success"}

        payload = {"agent_id": "test-agent", "prompt": "test prompt"}
        response = self.app.post('/webhook/letta',
                                 data=json.dumps(payload),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'success')

    def test_webhook_receiver_missing_data(self):
        """
        Tests the webhook receiver with missing data in the payload.
        """
        payload = {"agent_id": "test-agent"} # Missing prompt
        response = self.app.post('/webhook/letta',
                                 data=json.dumps(payload),
                                 content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

if __name__ == '__main__':
    unittest.main()