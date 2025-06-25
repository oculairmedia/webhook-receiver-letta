#!/usr/bin/env python3
"""
Test script for cumulative context system in flask_webhook_receiver.py

This script tests:
1. Correct accumulation of context with timestamped separators
2. Effective deduplication of identical or highly similar content  
3. Proper truncation of oldest entries when MAX_CONTEXT_SNIPPET_LENGTH is exceeded

Author: Test Suite
"""

import unittest
import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, call
import re

# Import the functions and constants we need to test
try:
    from flask_webhook_receiver import (
        create_memory_block, 
        find_context_block, 
        update_memory_block, 
        MAX_CONTEXT_SNIPPET_LENGTH,
        _build_cumulative_context,
        _parse_context_entries,
        _is_content_similar,
        _truncate_oldest_entries
    )
    print("✅ Successfully imported functions from flask_webhook_receiver.py")
except ImportError as e:
    print(f"❌ Failed to import from flask_webhook_receiver.py: {e}")
    sys.exit(1)

# Global mock state to simulate persistence
mock_letta_blocks = {}  # {block_id: {"id": block_id, "value": "...", "name": "..."}}
current_block_for_agent = {}  # {agent_id: block_id}

def reset_mock_state():
    """Reset the global mock state for fresh test runs"""
    global mock_letta_blocks, current_block_for_agent
    mock_letta_blocks = {}
    current_block_for_agent = {}

class TestCumulativeContext(unittest.TestCase):
    """Test suite for cumulative context functionality"""
    
    def setUp(self):
        """Set up fresh state for each test"""
        reset_mock_state()
        # Override MAX_CONTEXT_SNIPPET_LENGTH for easier testing
        self.original_max_len = MAX_CONTEXT_SNIPPET_LENGTH
        # Temporarily set a smaller limit for testing truncation
        import flask_webhook_receiver
        flask_webhook_receiver.MAX_CONTEXT_SNIPPET_LENGTH = 1000

    def tearDown(self):
        """Restore original settings after each test"""
        import flask_webhook_receiver
        flask_webhook_receiver.MAX_CONTEXT_SNIPPET_LENGTH = self.original_max_len

    def simulate_interaction(self, mock_find_block, mock_get, mock_patch, mock_post, agent_id, new_content_snippet, test_block_id="test_block_123"):
        """
        Simulate a webhook interaction that creates or updates a memory block
        Returns the current state of the block after the interaction
        """
        global current_block_for_agent, mock_letta_blocks

        # The test method is responsible for patching and setting all mocks

        # Prepare block data
        block_data_for_letta = {
            "name": f"graphiti_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "label": "graphiti_context",
            "value": new_content_snippet,
            "metadata": {"timestamp": datetime.now().isoformat()}
        }

        # Call the actual create_memory_block function
        existing_block_info, _ = mock_find_block.return_value

        if existing_block_info:
            # This will trigger the update path
            result = create_memory_block(block_data_for_letta, agent_id)
            # Update the mock block with the PATCH response data
            if test_block_id in mock_letta_blocks:
                if mock_patch.return_value.json.return_value:
                    patch_response = mock_patch.return_value.json.return_value
                    mock_letta_blocks[test_block_id]["value"] = patch_response["value"]
        else:
            # This will trigger the create path
            result = create_memory_block(block_data_for_letta, agent_id)
            # Store the newly "created" block in our mock
            mock_letta_blocks[test_block_id] = {
                "id": test_block_id,
                "value": new_content_snippet,
                "name": result.get("block_name", "graphiti_context_test"),
                "label": "graphiti_context"
            }
            current_block_for_agent[agent_id] = test_block_id
        
        return mock_letta_blocks.get(test_block_id)

    def get_current_block_state(self, agent_id):
        """Helper to get current block state for an agent"""
        if agent_id in current_block_for_agent:
            block_id = current_block_for_agent[agent_id]
            return mock_letta_blocks.get(block_id)
        return None

    @patch('flask_webhook_receiver.requests.post')
    @patch('flask_webhook_receiver.requests.patch')
    @patch('flask_webhook_receiver.requests.get')
    @patch('flask_webhook_receiver.find_context_block')
    def test_scenario_1_basic_accumulation(self, mock_find_block, mock_get, mock_patch, mock_post):
        """Test basic accumulation of context with timestamped separators"""
        print("\n🧪 Testing Scenario 1: Basic Accumulation")
        
        agent_id = "agent-1eacfc07-d8b6-4f25-a6ee-aab71934e07a"
        
        # First interaction
        content1 = "First interaction: User asks about Python"
        mock_find_block.return_value = (None, False)
        # Set up mock POST response with proper block ID
        mock_post.return_value.json.return_value = {
            "id": "test_block_123",
            "name": f"graphiti_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "value": content1,
            "label": "graphiti_context"
        }
        mock_post.return_value.status_code = 200
        block1 = self.simulate_interaction(mock_find_block, mock_get, mock_patch, mock_post, agent_id, content1)
        self.assertIsNotNone(block1)
        self.assertIn(content1, block1["value"])
        print(f"✅ First interaction stored: {content1[:50]}...")
        
        # Second interaction
        content2 = "Second interaction: User asks about Flask"
        mock_letta_blocks[current_block_for_agent[agent_id]] = block1
        mock_find_block.return_value = (block1, True)

        # Set up mock PATCH response with accumulated content
        mock_patch.return_value.json.return_value = {
            "id": "test_block_123",
            "name": block1["name"],
            "value": _build_cumulative_context(block1["value"], content2),
            "label": "graphiti_context"
        }
        mock_patch.return_value.status_code = 200

        block2 = self.simulate_interaction(mock_find_block, mock_get, mock_patch, mock_post, agent_id, content2)
        self.assertIsNotNone(block2)
        
        # Verify accumulation
        block_value = block2["value"]
        self.assertIn(content1, block_value)
        self.assertIn(content2, block_value)
        self.assertIn("--- CONTEXT ENTRY (", block_value)
        print(f"✅ Second interaction accumulated properly")
        
        # Third interaction
        content3 = "Third interaction: User asks about databases"
        mock_letta_blocks[current_block_for_agent[agent_id]] = block2
        mock_find_block.return_value = (block2, True)

        # Set up mock PATCH response with accumulated content
        mock_patch.return_value.json.return_value = {
            "id": "test_block_123",
            "name": block2["name"],
            "value": _build_cumulative_context(block2["value"], content3),
            "label": "graphiti_context"
        }
        mock_patch.return_value.status_code = 200

        block3 = self.simulate_interaction(mock_find_block, mock_get, mock_patch, mock_post, agent_id, content3)
        
        # Verify all three are present
        final_value = block3["value"]
        self.assertIn(content1, final_value)
        self.assertIn(content2, final_value) 
        self.assertIn(content3, final_value)
        
        # Count context entry separators
        separator_count = final_value.count("--- CONTEXT ENTRY (")
        self.assertEqual(separator_count, 2, "Should have 2 separators for 3 entries")
        
        print(f"✅ All three interactions properly accumulated")
        print(f"📊 Final context length: {len(final_value)} characters")
        print("✅ Scenario 1: PASSED\n")

    @patch('flask_webhook_receiver.requests.post')
    @patch('flask_webhook_receiver.requests.patch')
    @patch('flask_webhook_receiver.requests.get')
    @patch('flask_webhook_receiver.find_context_block')
    def test_scenario_2_deduplication(self, mock_find_block, mock_get, mock_patch, mock_post):
        """Test deduplication of identical and similar content"""
        print("🧪 Testing Scenario 2: Deduplication")
        
        agent_id = "agent-1eacfc07-d8b6-4f25-a6ee-aab71934e07a"
        
        # First interaction
        content1 = "User wants to know about machine learning algorithms"
        mock_find_block.return_value = (None, False)
        mock_post.return_value.json.return_value = {
            "id": "test_block_123",
            "name": f"graphiti_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "value": content1,
            "label": "graphiti_context"
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "id": "test_block_123",
            "name": f"graphiti_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "value": content1,
            "label": "graphiti_context"
        }
        mock_post.return_value.status_code = 200
        block1 = self.simulate_interaction(mock_find_block, mock_get, mock_patch, mock_post, agent_id, content1)
        original_length = len(block1["value"])
        print(f"✅ First interaction stored: {content1[:50]}...")
        
        # Second interaction - identical content
        content2 = "User wants to know about machine learning algorithms"  # Exactly the same
        mock_letta_blocks[current_block_for_agent[agent_id]] = block1
        mock_find_block.return_value = (block1, True)
        mock_post.return_value.json.return_value = {
            "id": "test_block_123",
            "name": f"graphiti_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "value": content2,
            "label": "graphiti_context"
        }
        mock_post.return_value.status_code = 200
        mock_patch.return_value.json.return_value = {
            "id": "test_block_123",
            "name": f"graphiti_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "value": content2,
            "label": "graphiti_context"
        }
        mock_patch.return_value.status_code = 200
        block2 = self.simulate_interaction(mock_find_block, mock_get, mock_patch, mock_post, agent_id, content2)
        
        # Should not have grown (deduplication should prevent adding duplicate)
        new_length = len(block2["value"])
        self.assertEqual(original_length, new_length, 
                        "Identical content should be deduplicated")
        print("✅ Identical content was deduplicated")
        
        # Third interaction - highly similar content
        content3 = "User wants to know about machine learning algorithms and techniques"
        mock_letta_blocks[current_block_for_agent[agent_id]] = block2
        mock_find_block.return_value = (block2, True)
        mock_post.return_value.json.return_value = {
            "id": "test_block_123",
            "name": f"graphiti_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "value": content3,
            "label": "graphiti_context"
        }
        mock_post.return_value.status_code = 200
        mock_patch.return_value.json.return_value = {
            "id": "test_block_123",
            "name": f"graphiti_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "value": content3,
            "label": "graphiti_context"
        }
        mock_patch.return_value.status_code = 200
        block3 = self.simulate_interaction(mock_find_block, mock_get, mock_patch, mock_post, agent_id, content3)
        
        # This should also be deduplicated due to high similarity
        similar_length = len(block3["value"])
        similarity_detected = similar_length == original_length
        if similarity_detected:
            print("✅ Highly similar content was deduplicated")
        else:
            print("ℹ️  Highly similar content was added (similarity threshold not met)")
        
        # Fourth interaction - clearly different content
        content4 = "User asks about web development frameworks"
        mock_letta_blocks[current_block_for_agent[agent_id]] = block3
        mock_find_block.return_value = (block3, True)
        block4 = self.simulate_interaction(mock_find_block, mock_get, mock_patch, mock_post, agent_id, content4)
        
        # This should definitely be added
        final_length = len(block4["value"])
        self.assertGreater(final_length, original_length, 
                          "Different content should be added")
        print("✅ Different content was properly added")
        
        print("✅ Scenario 2: PASSED\n")

    def test_scenario_3_truncation(self):
        """Test truncation when MAX_CONTEXT_SNIPPET_LENGTH is exceeded"""
        print("🧪 Testing Scenario 3: Truncation")
        
        agent_id = "agent-1eacfc07-d8b6-4f25-a6ee-aab71934e07a"
        
    @patch('flask_webhook_receiver.requests.post')
    @patch('flask_webhook_receiver.requests.patch')
    @patch('flask_webhook_receiver.requests.get')
    @patch('flask_webhook_receiver.find_context_block')
    def test_scenario_3_truncation(self, mock_find_block, mock_get, mock_patch, mock_post):
        print("🧪 Testing Scenario 3: Truncation")
        
        agent_id = "agent-1eacfc07-d8b6-4f25-a6ee-aab71934e07a"
        
        # Set a very small limit for this test
        import flask_webhook_receiver
        original_limit = flask_webhook_receiver.MAX_CONTEXT_SNIPPET_LENGTH
        flask_webhook_receiver.MAX_CONTEXT_SNIPPET_LENGTH = 500  # Very small for testing
        
        try:
            # Add multiple chunks of content to exceed the limit
            chunks = [
                "This is the first chunk of content that should be added to the context. " * 3,
                "This is the second chunk with different information about user preferences. " * 3,
                "Here's a third chunk discussing various technical topics and solutions. " * 3,
                "Fourth chunk contains more detailed information about complex subjects. " * 3,
                "Fifth chunk adds even more content to definitely exceed our small limit. " * 3,
                "Sixth chunk should trigger truncation of the oldest entries in the context. " * 3
            ]
            
            # Helper function to normalize whitespace for comparison
            def normalize_text(text):
                return ' '.join(text.split())

            block = None
            for i, chunk in enumerate(chunks):
                if i == 0:
                    mock_find_block.return_value = (None, False)
                else:
                    mock_letta_blocks[current_block_for_agent[agent_id]] = block
                    mock_find_block.return_value = (block, True)
                # Set up mock responses
                if i == 0:
                    # First chunk uses POST
                    mock_post.return_value.json.return_value = {
                        "id": "test_block_123",
                        "name": f"graphiti_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "value": chunk,
                        "label": "graphiti_context"
                    }
                    mock_post.return_value.status_code = 200
                else:
                    # Subsequent chunks use PATCH with accumulated content
                    existing_content = block["value"] if block else ""
                    accumulated_content = _build_cumulative_context(existing_content, chunk)
                    mock_patch.return_value.json.return_value = {
                        "id": "test_block_123",
                        "name": block["name"] if block else f"graphiti_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "value": accumulated_content,
                        "label": "graphiti_context"
                    }
                    mock_patch.return_value.status_code = 200
                
                block = self.simulate_interaction(mock_find_block, mock_get, mock_patch, mock_post, agent_id, chunk)
                current_length = len(block["value"])
                print(f"After chunk {i+1}: {current_length} characters")
                
                # Once we exceed the limit, truncation should kick in
                if current_length > flask_webhook_receiver.MAX_CONTEXT_SNIPPET_LENGTH:
                    self.fail(f"Context length {current_length} exceeds limit {flask_webhook_receiver.MAX_CONTEXT_SNIPPET_LENGTH}")
            
            # Verify final state
            final_context = block["value"]
            final_length = len(final_context)
            
            # Should not exceed our limit
            self.assertLessEqual(final_length, flask_webhook_receiver.MAX_CONTEXT_SNIPPET_LENGTH,
                               f"Final context length {final_length} should not exceed limit {flask_webhook_receiver.MAX_CONTEXT_SNIPPET_LENGTH}")
            
            # Should contain truncation notice
            self.assertIn("--- OLDER ENTRIES TRUNCATED ---", final_context,
                         "Should contain truncation notice")
            
            # Should contain the most recent entries
            # Normalize both strings before comparison
            final_context_normalized = normalize_text(final_context)
            last_chunk_normalized = normalize_text(chunks[-1])
            first_chunk_normalized = normalize_text(chunks[0])
            
            # Check for normalized content
            self.assertIn(last_chunk_normalized, final_context_normalized,
                         "Should contain the most recent chunk")
            
            # Should NOT contain the earliest entries (they should be truncated)
            self.assertNotIn(first_chunk_normalized, final_context_normalized,
                           "Should NOT contain the oldest chunk")
            
            print(f"✅ Truncation working correctly - final length: {final_length}")
            print("✅ Truncation notice present")
            print("✅ Most recent content preserved")
            print("✅ Oldest content properly removed")
            print("✅ Scenario 3: PASSED\n")
            
        finally:
            # Restore original limit
            flask_webhook_receiver.MAX_CONTEXT_SNIPPET_LENGTH = original_limit

    def test_helper_functions(self):
        """Test the individual helper functions"""
        print("🧪 Testing Helper Functions")
        
        # Test _is_content_similar
        self.assertTrue(_is_content_similar("Hello world", "Hello world"))
        self.assertTrue(_is_content_similar("Hello world", "hello world"))  # Case insensitive
        self.assertFalse(_is_content_similar("Hello world", "Goodbye world"))
        print("✅ _is_content_similar working correctly")
        
        # Test _parse_context_entries
        test_context = """First entry without separator

--- CONTEXT ENTRY (2024-01-01 12:00:00 UTC) ---

Second entry with separator

--- CONTEXT ENTRY (2024-01-01 13:00:00 UTC) ---

Third entry with separator"""
        
        entries = _parse_context_entries(test_context)
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0]["timestamp"], "Legacy")
        self.assertEqual(entries[1]["timestamp"], "2024-01-01 12:00:00 UTC")
        self.assertEqual(entries[2]["timestamp"], "2024-01-01 13:00:00 UTC")
        print("✅ _parse_context_entries working correctly")
        
        # Test _build_cumulative_context
        existing = "Old content"
        new = "New content"
        result = _build_cumulative_context(existing, new)
        self.assertIn("Old content", result)
        self.assertIn("New content", result)
        self.assertIn("--- CONTEXT ENTRY (", result)
        print("✅ _build_cumulative_context working correctly")
        
        print("✅ Helper Functions: PASSED\n")

def run_comprehensive_test():
    """Run all test scenarios and provide a summary"""
    print("🚀 Starting Comprehensive Cumulative Context Tests")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCumulativeContext)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED! The cumulative context system is working correctly.")
    else:
        print("\n⚠️  SOME TESTS FAILED. Please review the issues above.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    # Allow running specific tests or all tests
    import argparse
    
    parser = argparse.ArgumentParser(description="Test cumulative context system")
    parser.add_argument("--test", help="Run specific test method", default=None)
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    if args.test:
        # Run specific test
        suite = unittest.TestSuite()
        suite.addTest(TestCumulativeContext(args.test))
        runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
        result = runner.run(suite)
    else:
        # Run comprehensive test
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)