#!/usr/bin/env python3
"""
Test script for knowledge retrieval performance evaluation
"""
import os
import json
import time
from retrieve_context import generate_context_from_prompt

# Set environment variables for testing
os.environ["GRAPHITI_MAX_NODES"] = "5"
os.environ["GRAPHITI_MAX_FACTS"] = "15"
os.environ["QUERY_REFINEMENT_ENABLED"] = "true"
os.environ["EXTERNAL_QUERY_ENABLED"] = "true"
os.environ["CEREBRAS_API_KEY"] = "csk-vwwe8jynnn8mkrxhy253r9f3n52j25dpjjd998fr44c9wd32"

def test_single_query(query: str, description: str = "", file_handle=None):
    """Test a single query and measure performance"""
    def log_both(message):
        print(message)
        if file_handle:
            file_handle.write(message + "\n")
    
    log_both(f"\n{'='*80}")
    log_both(f"TEST: {description}")
    log_both(f"Query: {query}")
    log_both(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        context = generate_context_from_prompt(
            messages=query,
            graphiti_url="http://192.168.50.90:8001/api",
            max_nodes=5,
            max_facts=15,
            group_ids=None  # None means search all groups
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        log_both(f"\n✅ SUCCESS (took {duration:.2f}s)")
        log_both(f"Context length: {len(context)} characters")
        log_both(f"Context preview: {context[:200]}...")
        
        # Write full context to file
        if file_handle:
            file_handle.write(f"\n--- FULL CONTEXT FOR: {description} ---\n")
            file_handle.write(context)
            file_handle.write(f"\n--- END CONTEXT FOR: {description} ---\n\n")
        
        return context, duration
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        log_both(f"\n❌ ERROR (took {duration:.2f}s): {e}")
        return None, duration

def test_conversation_history(file_handle=None):
    """Test with conversation history format"""
    def log_both(message):
        print(message)
        if file_handle:
            file_handle.write(message + "\n")
    
    messages = [
        {"role": "user", "content": "What is machine learning?"},
        {"role": "assistant", "content": "Machine learning is a subset of artificial intelligence..."},
        {"role": "user", "content": "How does deep learning work?"}
    ]
    
    log_both(f"\n{'='*80}")
    log_both(f"TEST: Conversation History Format")
    log_both(f"Messages: {json.dumps(messages, indent=2)}")
    log_both(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        context = generate_context_from_prompt(
            messages=messages,
            graphiti_url="http://192.168.50.90:8001/api",
            max_nodes=5,
            max_facts=15,
            group_ids=None  # None means search all groups
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        log_both(f"\n✅ SUCCESS (took {duration:.2f}s)")
        log_both(f"Context length: {len(context)} characters")
        log_both(f"Context preview: {context[:200]}...")
        
        # Write full context to file
        if file_handle:
            file_handle.write(f"\n--- FULL CONTEXT FOR: Conversation History Format ---\n")
            file_handle.write(context)
            file_handle.write(f"\n--- END CONTEXT FOR: Conversation History Format ---\n\n")
        
        return context, duration
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        log_both(f"\n❌ ERROR (took {duration:.2f}s): {e}")
        return None, duration

def main():
    """Run comprehensive tests"""
    # Create output file with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = f"knowledge_retrieval_test_results_{timestamp}.txt"
    
    def log_both(message, file_handle=None):
        """Log to both console and file"""
        print(message)
        if file_handle:
            file_handle.write(message + "\n")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        log_both("🚀 Starting Knowledge Retrieval Performance Tests", f)
        log_both(f"Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}", f)
        log_both(f"Environment Configuration:", f)
        log_both(f"  - GRAPHITI_MAX_NODES: {os.environ.get('GRAPHITI_MAX_NODES')}", f)
        log_both(f"  - GRAPHITI_MAX_FACTS: {os.environ.get('GRAPHITI_MAX_FACTS')}", f)
        log_both(f"  - QUERY_REFINEMENT_ENABLED: {os.environ.get('QUERY_REFINEMENT_ENABLED')}", f)
        log_both(f"  - EXTERNAL_QUERY_ENABLED: {os.environ.get('EXTERNAL_QUERY_ENABLED')}", f)
        log_both("", f)
    
        results = []
        
        # Test cases
        test_cases = [
            ("What is artificial intelligence?", "Simple AI query"),
            ("How do neural networks learn?", "Technical ML query"),
            ("Tell me about Python programming", "Programming query"),
            ("What are the benefits of renewable energy?", "General knowledge query"),
            ("Explain quantum computing", "Advanced technology query")
        ]
        
        # Run single query tests
        for query, description in test_cases:
            context, duration = test_single_query(query, description, f)
            results.append({
                "type": "single_query",
                "query": query,
                "description": description,
                "duration": duration,
                "success": context is not None,
                "context_length": len(context) if context else 0
            })
        
        # Test conversation history
        context, duration = test_conversation_history(f)
        results.append({
            "type": "conversation_history",
            "query": "conversation_test",
            "description": "Conversation history format",
            "duration": duration,
            "success": context is not None,
            "context_length": len(context) if context else 0
        })
        
        # Performance summary
        log_both(f"\n{'='*80}", f)
        log_both("📊 PERFORMANCE SUMMARY", f)
        log_both(f"{'='*80}", f)
        
        successful_tests = [r for r in results if r["success"]]
        failed_tests = [r for r in results if not r["success"]]
        
        if successful_tests:
            avg_duration = sum(r["duration"] for r in successful_tests) / len(successful_tests)
            min_duration = min(r["duration"] for r in successful_tests)
            max_duration = max(r["duration"] for r in successful_tests)
            avg_context_length = sum(r["context_length"] for r in successful_tests) / len(successful_tests)
            
            log_both(f"✅ Successful tests: {len(successful_tests)}/{len(results)}", f)
            log_both(f"⏱️  Average duration: {avg_duration:.2f}s", f)
            log_both(f"🏃 Fastest query: {min_duration:.2f}s", f)
            log_both(f"🐌 Slowest query: {max_duration:.2f}s", f)
            log_both(f"📝 Average context length: {avg_context_length:.0f} characters", f)
            
            log_both(f"\nDetailed Results:", f)
            for result in successful_tests:
                log_both(f"  • {result['description']}: {result['duration']:.2f}s ({result['context_length']} chars)", f)
        
        if failed_tests:
            log_both(f"\n❌ Failed tests: {len(failed_tests)}", f)
            for result in failed_tests:
                log_both(f"  • {result['description']}: FAILED after {result['duration']:.2f}s", f)
        
        log_both(f"\n{'='*80}", f)
        log_both("🏁 Testing Complete!", f)
        log_both(f"Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}", f)
        log_both(f"Results saved to: {output_file}", f)
        log_both(f"{'='*80}", f)
    
    print(f"\n📄 Full test results with context details saved to: {output_file}")

if __name__ == "__main__":
    main()